"""
CyberTwin - threat_engine.py
Detect -> Explain layer.

Combines:
 1. Text normalization
 2. Semantic/prototype similarity (TF-IDF cosine) - upgrade point for real ML model
 3. Structured security indicators (URL, social engineering, credential/payment signals)
 4. Lightweight weighted risk-scoring layer

This is an explainable heuristic + semantic MVP. It does NOT claim ML accuracy.
A trained classifier can later replace classify_threat() without changing app.py.
"""

import re
from urllib.parse import urlparse
from datetime import datetime

# ---------------------------------------------------------------------------
# 1. Text normalization
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    if not text:
        return ""
    t = text.lower()
    # normalize obfuscations like "fr33", "0tp", excessive punctuation
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_urls(text: str):
    if not text:
        return []
    # find http(s) urls, www., and bare domains with suspicious TLD-ish pattern
    pattern = r"(https?://[^\s'\"<>]+|www\.[^\s'\"<>]+|[a-z0-9-]+\.[a-z]{2,}(?:/[^\s'\"<>]*)?)"
    found = re.findall(pattern, text, flags=re.IGNORECASE)
    # light cleanup of trailing punctuation
    cleaned = [u.rstrip(".,;!?)'\"") for u in found]
    # dedupe preserve order
    seen, out = set(), []
    for u in cleaned:
        if u.lower() not in seen:
            seen.add(u.lower())
            out.append(u)
    return out


# ---------------------------------------------------------------------------
# 2. Semantic / prototype similarity layer
#    Upgrade point: replace with sentence-embeddings + LogisticRegression/XGB.
# ---------------------------------------------------------------------------

THREAT_PROTOTYPES = {
    "Phishing": [
        "your account has been suspended verify immediately by clicking the link",
        "dear customer your bank account will be blocked update kyc now",
        "security alert unusual login attempt confirm your identity here",
    ],
    "Financial scam": [
        "send money urgently via upi google pay phonepe to avoid penalty",
        "pay processing fee to release your prize lottery winnings",
        "your electricity bill overdue pay now to avoid disconnection",
    ],
    "Fake job scam": [
        "congratulations selected for work from home job pay registration fee",
        "earn 5000 per day by liking videos deposit refundable amount first",
        "job offer no interview pay training fee to confirm your seat",
    ],
    "Investment scam": [
        "double your money guaranteed returns crypto forex trading profit",
        "invest small amount get high returns risk free telegram group",
        "stock tips guaranteed profit join premium plan now",
    ],
    "Delivery/refund scam": [
        "your parcel is held pay customs fee to release delivery",
        "your order could not be delivered confirm address and pay redelivery",
        "refund failed enter bank details to receive refund amount",
    ],
    "Impersonation": [
        "this is your boss send gift cards urgently keep it confidential",
        "hello this is bank manager share otp to verify your account",
        "i am from customer support team calling from head office",
    ],
    "Credential theft": [
        "login to verify your password reset your account credentials",
        "enter your username password otp to unlock your account",
        "confirm your email password to avoid mailbox closure",
    ],
    "Account takeover": [
        "someone tried to access your account share otp to secure it",
        "your whatsapp account will expire forward verification code",
        "account takeover warning confirm otp to keep account safe",
    ],
    "Malicious link": [
        "click this shortened link to claim reward http bit ly free gift",
        "open this link to view photos document download file",
        "scan qr to receive payment instead money will be debited",
    ],
    "Social engineering": [
        "urgent act now last chance fear threat police action against you",
        "you won lottery prize reward claim now limited offer",
        "do not tell anyone keep secret act immediately",
    ],
    "Harassment/blackmail": [
        "we have your private photos videos pay or we will leak share them",
        "sextortion webcam recorded you send money or contact your family",
        "threatening blackmail expose secrets pay bitcoin to delete",
    ],
}

BENIGN_PROTOTYPES = [
    "meeting scheduled for tomorrow please confirm your availability thanks",
    "your order has been shipped tracking details available on official app",
    "reminder team lunch on friday let me know if you can join",
]


def semantic_scores(text: str) -> dict:
    """
    TF-IDF cosine similarity of input vs prototype groups.
    Returns {threat_type: 0..1}. Purely supportive signal, not a trained model.
    """
    norm = normalize_text(text)
    if not norm or len(norm.split()) < 2:
        return {k: 0.0 for k in THREAT_PROTOTYPES}
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except Exception:
        return {k: 0.0 for k in THREAT_PROTOTYPES}

    corpus_labels, corpus_texts = [], []
    for label, examples in THREAT_PROTOTYPES.items():
        for ex in examples:
            corpus_labels.append(label)
            corpus_texts.append(ex)
    for b in BENIGN_PROTOTYPES:
        corpus_labels.append("__benign__")
        corpus_texts.append(b)
    all_docs = corpus_texts + [norm]
    try:
        vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", min_df=1)
        mat = vec.fit_transform(all_docs)
        inp = mat[-1]
        proto_mat = mat[:-1]
        sims = cosine_similarity(inp, proto_mat)[0]
    except ValueError:
        return {k: 0.0 for k in THREAT_PROTOTYPES}

    best = {k: 0.0 for k in THREAT_PROTOTYPES}
    benign_best = 0.0
    for label, s in zip(corpus_labels, sims):
        s = float(s)
        if label == "__benign__":
            benign_best = max(benign_best, s)
        else:
            best[label] = max(best[label], s)
    # dampen if benign is clearly closer
    if benign_best > max(best.values(), default=0) + 0.08:
        best = {k: v * 0.4 for k, v in best.items()}
    return best


# ---------------------------------------------------------------------------
# 3. Structured security features
# ---------------------------------------------------------------------------

SE_PATTERNS = {
    "urgency": [r"\burgent\w*", r"\bimmediately\b", r"\bright now\b", r"\blast chance\b",
                r"\bact (fast|now)\b", r"\bwithin \d+ (hour|minute)", r"\bexpire[sd]?\b",
                r"\bhurry\b", r"\basap\b", r"!!!+", r"\btoday only\b", r"\blast day\b"],
    "fear_threat": [r"\bblock\w*\b", r"\bsuspend\w*\b", r"\bdeactivat\w*\b", r"\bpenalty\b",
                    r"\bfine\b", r"\bpolice\b", r"\barrest\b", r"\bcourt\b", r"\blegal action\b",
                    r"\baccount.*clos", r"\bdisconnec\w*\b", r"\bunauthori[sz]ed\b", r"\brisk\b"],
    "authority": [r"\bbank\b", r"\brbi\b", r"\bmanager\b", r"\bofficer\b", r"\bcustomer support\b",
                  r"\bcustomer care\b", r"\bhead office\b", r"\bgovt\b", r"\bgovernment\b",
                  r"\bpolice\b", r"\btax\b", r"\bincome tax\b", r"\bboss\b", r"\bhr\b", r"\bceo\b"],
    "reward": [r"\bwon\b", r"\bwinner\b", r"\blottery\b", r"\bprize\b", r"\bcongratulations\b",
               r"\bcongrats\b", r"\bfree gift\b", r"\bcashback\b", r"\boffer\b", r"\bdiscount\b",
               r"\breward\b", r"\bselected\b"],
    "financial_pressure": [r"\bupi\b", r"\bgpay\b", r"\bphonepe\b", r"\bpaytm\b", r"\bpay now\b",
                           r"\btransfer\b", r"\bpayment\b", r"\brefund\b", r"\bfee\b", r"\bdeposit\b",
                           r"\binvest\w*\b", r"\bprofit\b", r"\bdouble.*money\b", r"\bcollect request\b",
                           r"\bqr\b", r"\bscan\b", r"₹", r"\brs\.?\b", r"\bamount\b"],
    "credential_request": [r"\botp\b", r"\bpassword\b", r"\bpin\b", r"\bcvv\b", r"\bcard number\b",
                           r"\baccount number\b", r"\bverify.*account\b", r"\bkyc\b", r"\blogin\b",
                           r"\bcredentials?\b", r"\bshare.*code\b", r"\bforward.*code\b"],
    "curiosity": [r"\bclick.*link\b", r"\bopen.*link\b", r"\bdownload\b", r"\battachment\b",
                  r"\bview (photo|video|document)\b", r"\bcheck this out\b", r"\bsecret\b"],
    "emotional": [r"\btrust me\b", r"\bkeep.*secret\b", r"\bdon't tell\b", r"\bconfidential\b",
                  r"\bhelp me\b", r"\bemergency\b", r"\bkindly\b", r"\bdear\b"],
}

THREAT_KEYWORD_WEIGHTS = {
    "Phishing": ["verify", "suspend", "blocked", "kyc", "login", "account", "security alert", "confirm identity"],
    "Financial scam": ["upi", "pay now", "transfer", "penalty", "electricity", "disconnection", "refund fee", "processing fee"],
    "Fake job scam": ["job", "work from home", "earn", "registration fee", "task", "like videos", "part-time", "offer letter"],
    "Investment scam": ["invest", "profit", "double", "returns", "crypto", "forex", "trading", "guaranteed"],
    "Delivery/refund scam": ["parcel", "courier", "delivery", "customs", "redelivery", "tracking", "refund"],
    "Impersonation": ["boss", "manager", "support", "head office", "sir", "madam", "colleague", "official"],
    "Credential theft": ["password", "otp", "pin", "cvv", "login", "credentials", "reset", "unlock"],
    "Account takeover": ["otp", "verification code", "forward", "takeover", "unauthorized", "secure your account"],
    "Malicious link": ["click", "link", "bit.ly", "tinyurl", "download", "scan qr", "open"],
    "Social engineering": ["urgent", "immediately", "last chance", "secret", "confidential", "act now"],
    "Harassment/blackmail": ["leak", "expose", "private video", "sextortion", "blackmail", "threaten", "publish photos"],
}


def detect_social_engineering(text: str) -> dict:
    norm = normalize_text(text)
    signals = {}
    for name, patterns in SE_PATTERNS.items():
        hits = []
        for p in patterns:
            for m in re.finditer(p, norm, flags=re.IGNORECASE):
                frag = m.group(0)
                # small context window
                s = max(0, m.start() - 20)
                e = min(len(text), m.end() + 20)
                hits.append(text[s:e].strip())
                break  # one hit per pattern is enough
        signals[name] = {"present": len(hits) > 0, "count": len(hits), "examples": hits[:2]}
    return signals


SHORTENERS = ["bit.ly", "tinyurl", "t.co", "goo.gl", "ow.ly", "is.gd", "cutt.ly",
              "rebrand.ly", "shorturl", "tiny.cc", "lnk", "qr"]
SUSP_WORDS = ["verify", "secure", "update", "login", "account", "bank", "free",
              "prize", "gift", "offer", "refund", "kyc", "confirm", "suspend",
              "unlock", "reward", "claim", "bonus", "urgent", "limited"]
KNOWN_BRANDS = ["hdfc", "sbi", "icici", "axis", "paypal", "amazon", "flipkart",
                "google", "apple", "microsoft", "facebook", "instagram", "whatsapp",
                "phonepe", "paytm", "gpay"]


def analyze_single_url(raw: str) -> dict:
    url = raw.strip()
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "http://" + url
    indicators = []
    score_add = 0
    try:
        parsed = urlparse(url)
    except Exception:
        return {"url": raw, "indicators": ["Could not parse URL structure."], "added_risk": 5}

    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    full = url.lower()

    def add(msg, pts):
        nonlocal score_add
        indicators.append(msg)
        score_add += pts

    # scheme
    if parsed.scheme == "http":
        add("Uses HTTP (not HTTPS) — data sent to this site is not encrypted.", 10)
    elif parsed.scheme == "https":
        indicators.append("Uses HTTPS — this only means the connection is encrypted, not that the site is trustworthy.")

    # IP-based
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host) or "[" in host:
        add("Uses a raw IP address instead of a domain name — common in phishing/malware links.", 18)

    # shortener
    if any(s in host or s in full for s in SHORTENERS):
        add("Shortened URL — the real destination is hidden. Expand before clicking.", 12)

    # punycode
    if "xn--" in host:
        add("Contains punycode (xn--) — possible look-alike / homograph domain.", 15)

    # @ symbol
    if "@" in url:
        add("Contains '@' — browsers ignore everything before '@', often abused to fake domains.", 12)

    # excessive subdomains
    dots = host.count(".")
    if dots >= 3:
        add(f"Has {dots+1} domain parts (many subdomains) — e.g. bank.verify.login.{host} can fake a real brand.", 10)

    # look-alike / brand + extra words
    for b in KNOWN_BRANDS:
        if b in host and host not in (f"{b}.com", f"www.{b}.com", f"{b}.in", f"www.{b}.in", f"{b}.co.in"):
            add(f"Contains brand-like word '{b}' inside '{host}' — could be a look-alike domain. Verify the exact domain.", 12)
            break

    # suspicious keywords
    hit_words = [w for w in SUSP_WORDS if w in full]
    if hit_words:
        add(f"Contains pressure/action words in URL: {', '.join(hit_words[:4])} — often used to lure clicks.", 8)

    # special chars / long
    if len(url) > 90:
        add(f"Unusually long URL ({len(url)} chars) — may hide the real path/domain.", 6)
    if full.count("-") >= 3:
        add("Multiple hyphens in URL — look-alike domains often use extra hyphens (e.g. hdfc-bank-secure).", 5)
    if re.search(r"%[0-9a-f]{2}", full):
        indicators.append("Contains percent-encoded characters — sometimes used to obfuscate the destination.")
    if re.search(r"(login|signin|verify).*(login|verify)", full):
        add("Repeats login/verify words in path — typical fake-login-page pattern.", 6)
    # --- ADDITIVE: rarer TLDs, digits, ports, userinfo, unicode, redirect params ---
    try:
        tld = host.rsplit(".", 1)[-1] if "." in host else ""
        if tld in RISKY_TLDS:
            add(f"Uses low-cost/abuse-prone TLD '.{tld}' — common in throwaway scam domains (weak signal alone, NOT proof).", 7)
    except Exception:
        pass
    if re.search(r"\d{4,}", host):
        add("Contains long digit runs in the domain — often auto-generated look-alike domains.", 4)
    try:
        if parsed.port:
            add(f"Uses explicit port :{parsed.port} — unusual for normal links; verify carefully.", 5)
    except Exception:
        pass
    if parsed.username or parsed.password:
        add("Contains username/password section in URL — legitimate sites rarely do this.", 8)
    if re.search(r"[^\x00-\x7F]", url):
        add("Contains non-ASCII/unicode characters — possible homograph trick. Compare letter-by-letter.", 7)
    if re.search(r"(redirect|url=|next=|continue=|goto=)", full):
        indicators.append("Contains redirect parameter (redirect/url=/next=) — the final destination may differ from what you see.")
    if "?" in url and url.count("=") >= 3:
        indicators.append("Many query parameters — sometimes used to pass tracking/stolen data in phishing links.")

    if not indicators:
        indicators.append("No strong structural red flags found — still verify the sender and context before opening.")
    return {"url": raw, "host": host, "indicators": indicators, "added_risk": min(score_add, 40)}


def analyze_urls(urls: list) -> list:
    return [analyze_single_url(u) for u in urls]


# ---------------------------------------------------------------------------
# 5. ADDITIVE: entity extraction, suspicious-text highlighting, SE explanations
#    (new keys only — existing analysis contract unchanged)
# ---------------------------------------------------------------------------

SE_EXPLANATIONS = {
    "urgency": "Rushes you so you act before thinking (e.g. 'immediately', 'last chance', 'expire').",
    "fear_threat": "Scares you with block/penalty/police/legal threats to force compliance.",
    "authority": "Borrows trust of bank/officer/boss/support so you obey without checking.",
    "reward": "Lures with prize/lottery/offer/winnings so you click or pay a 'fee'.",
    "financial_pressure": "Pushes money movement (UPI/fee/refund/invest/QR) — the attacker's payoff.",
    "credential_request": "Asks for OTP/password/PIN/CVV/login — keys to take over accounts.",
    "curiosity": "Baits a click/download/open (photos, docs, links) to deliver phishing/malware.",
    "emotional": "Uses secrecy, kindness or emergency language to lower your guard.",
}

RISKY_TLDS = {"tk", "ml", "ga", "cf", "gq", "xyz", "top", "club", "online",
              "buzz", "site", "icu", "rest", "link", "zip", "mov"}

HIGHLIGHT_COLORS = {
    "urgency": "#ffd32a", "fear_threat": "#ff6b6b", "authority": "#5aa2ff",
    "reward": "#2ed573", "financial_pressure": "#ff9f43", "credential_request": "#e056fd",
    "curiosity": "#48dbfb", "emotional": "#f368e0", "url": "#ffa502",
}


def extract_entities(text: str, sender: str = "") -> dict:
    """Auto-extract sender/contacts/URLs/dates/transactions/UPI/social hints."""
    t = text or ""
    emails = sorted(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", t + " " + (sender or ""))))
    phones = sorted(set(re.findall(r"(?:\+?91[\s-]?)?[6-9]\d{9}|\+\d[\d\s-]{7,}\d", t + " " + (sender or ""))))
    urls = extract_urls(t)
    # dates / times
    dates = sorted(set(re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}:\d{2}\b|(?:today|tomorrow|immediately|within \d+ (?:hour|minute|day)s?)", t, re.I)))
    # amounts
    amounts = sorted(set(re.findall(r"(?:₹|Rs\.?|INR|rupees?)\s?[\d,]+(?:\.\d+)?|\b\d[\d,]*\s?(?:rupees|rs)\b", t, re.I)))
    # UPI / payment ids
    upi_ids = sorted(set(re.findall(r"[a-zA-Z0-9._-]{2,}@[a-zA-Z]{2,}", t)))
    upi_extra = sorted(set(re.findall(r"upi(?:://\S+)?|collect request|VPA|UTR\s*:?\s*\d+|transaction\s*(?:id|no\.?)\s*:?\s*[\w]+", t, re.I)))
    # social / profile hints
    social_hits = sorted(set(re.findall(r"(?:instagram|facebook|whatsapp|telegram|twitter|linkedin|x\.com|profile|followers?|joined|account|handle|@[\w.]+)", t, re.I)))
    # sender name guess: "I am X from", "This is X", leading "Dear <Name>"
    name_guess = ""
    m = re.search(r"(?:i am|this is|i'm)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", t)
    if m:
        name_guess = m.group(1)
    return {"emails": emails, "phones": phones, "urls": urls, "dates_times": dates,
            "amounts": amounts, "upi_ids": upi_ids, "payment_refs": upi_extra,
            "social_hints": social_hits, "sender_name_guess": name_guess,
            "sender_raw": sender or ""}


def suspicious_spans(text: str, se_detail: dict | None = None) -> list:
    """Return [(start, end, label)] for suspicious portions of the ORIGINAL text."""
    if not text:
        return []
    spans = []
    # URLs first
    for u in extract_urls(text):
        try:
            s = text.index(u)
            spans.append((s, s + len(u), "url"))
        except ValueError:
            pass
    # SE pattern matches on original text (case-insensitive)
    for label, patterns in SE_PATTERNS.items():
        for p in patterns:
            for m in re.finditer(p, text, flags=re.IGNORECASE):
                spans.append((m.start(), m.end(), label))
    # merge overlaps (keep first label)
    spans.sort()
    merged = []
    for s, e, lab in spans:
        if merged and s < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e), merged[-1][2])
        else:
            merged.append((s, e, lab))
    return merged


def highlight_html(text: str, spans: list) -> str:
    """HTML with <mark> highlights so users see WHICH words drove the score."""
    import html as _html
    if not text:
        return ""
    if not spans:
        return f"<div class='card'>{_html.escape(text)}</div>"
    out, last = [], 0
    for s, e, lab in sorted(spans):
        s, e = max(0, s), min(len(text), e)
        if s < last:
            continue
        out.append(_html.escape(text[last:s]))
        color = HIGHLIGHT_COLORS.get(lab, "#ffeaa7")
        label = lab.replace("_", " ")
        out.append(f"<mark title='{label}' style='background:{color};color:#111;border-radius:4px;padding:1px 4px;'>{_html.escape(text[s:e])}</mark>")
        last = e
    out.append(_html.escape(text[last:]))
    legend = " ".join(f"<span class='chip' style='border-color:{HIGHLIGHT_COLORS.get(k,'#888')}'>{k.replace('_',' ')}</span>"
                      for k in sorted({l for _, _, l in spans}))
    return f"<div class='card' style='line-height:1.9'>{''.join(out)}<br><br>{legend}</div>"


def url_verdict(url_result: dict) -> str:
    """Distinguish weak single-signal vs multi-signal URLs. Never confirms maliciousness."""
    pts = url_result.get("added_risk", 0)
    n_flags = sum(1 for i in url_result.get("indicators", [])
                  if "only means" not in i and "No strong" not in i and "percent-encoded" not in i)
    if pts >= 20 or n_flags >= 3:
        return "Multiple suspicious signals — treat as high-risk. Do not open; verify independently."
    if pts >= 10 or n_flags >= 1:
        return "One or two risk indicators — suspicious, NOT confirmed malicious. Verify before opening."
    return "No strong structural red flags — still verify sender/context. Indicators alone never prove safety."


# ---------------------------------------------------------------------------
# 4. Classification + risk scoring
# ---------------------------------------------------------------------------

def classify_threat(text: str, urls: list, se: dict, sem: dict) -> tuple:
    norm = normalize_text(text)
    words = set(re.findall(r"[a-z]+", norm))
    struct = {}
    for label, kws in THREAT_KEYWORD_WEIGHTS.items():
        c = sum(1 for k in kws if k in norm)
        struct[label] = c
    # URL presence boosts link-driven threats
    if urls:
        struct["Malicious link"] = struct.get("Malicious link", 0) + 1.5
        struct["Phishing"] = struct.get("Phishing", 0) + 0.75
        struct["Credential theft"] = struct.get("Credential theft", 0) + 0.5
    # combine: 55% structured count + 45% semantic similarity scaled
    combined = {}
    for label in THREAT_KEYWORD_WEIGHTS:
        s_val = struct.get(label, 0)
        sem_val = sem.get(label, 0.0)
        combined[label] = (s_val * 8.0) + (sem_val * 55.0)
    # credential + otp strong driver
    if se.get("credential_request", {}).get("present"):
        combined["Credential theft"] = combined.get("Credential theft", 0) + 12
        combined["Account takeover"] = combined.get("Account takeover", 0) + 10
    if se.get("financial_pressure", {}).get("present"):
        combined["Financial scam"] = combined.get("Financial scam", 0) + 10
        combined["Investment scam"] = combined.get("Investment scam", 0) + 5
    # harassment / blackmail driver (threats + secrecy + payment demand together)
    _hnorm = norm
    if any(k in _hnorm for k in ("blackmail", "sextortion", "leak", "expose", "private video", "publish")):
        combined["Harassment/blackmail"] = combined.get("Harassment/blackmail", 0) + 16
    best = max(combined, key=lambda k: combined[k])
    if combined[best] < 6:
        best = "General suspicious / Social engineering" if norm else "No content provided"
    return best, combined


def risk_level(score: int) -> str:
    if score >= 75:
        return "Critical"
    if score >= 55:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def build_explanation(threat_type, se, url_results, indicators) -> tuple:
    why = []
    for ind in indicators[:8]:
        why.append(ind)
    objective_map = {
        "Phishing": "Steal your login credentials or personal details via a fake page/message.",
        "Financial scam": "Trick you into sending money (UPI/transfer/fee) that cannot be easily recovered.",
        "Fake job scam": "Collect registration fees or personal data under the excuse of a job/task offer.",
        "Investment scam": "Get you to invest, then disappear with the money or show fake profits.",
        "Delivery/refund scam": "Extract a small fee or card/bank details disguised as delivery/refund charges.",
        "Impersonation": "Abuse trust in a known person/organisation to make you comply.",
        "Credential theft": "Capture passwords/OTPs/PINs to take over accounts.",
        "Account takeover": "Hijack your account (bank/social/WhatsApp) using OTP or login theft.",
        "Malicious link": "Get you to open a harmful link/file that steals data or installs malware.",
        "Social engineering": "Manipulate emotion (fear/greed/urgency) to force a quick unsafe decision.",
        "Harassment/blackmail": "Pressure you with threats to leak private data unless you pay or comply. Do not pay — preserve evidence and seek help/report.",
    }
    objective = objective_map.get(threat_type, "Get you to act against your own interest (pay, share data, or click).")
    targeted = []
    if se.get("credential_request", {}).get("present"):
        targeted.append("passwords / OTPs / PINs")
    if se.get("financial_pressure", {}).get("present"):
        targeted.append("money transfer / UPI payment")
    if url_results:
        targeted.append("clicking a link / opening a page")
    if se.get("curiosity", {}).get("present"):
        targeted.append("downloading a file / opening attachment")
    if not targeted:
        targeted.append("your attention / reply / continued engagement")
    safe = ("Do NOT click, pay, or share codes. Verify independently via the official app/website or "
            "customer care number (type it yourself). Keep screenshots and report if needed.")
    return why, objective, "; ".join(targeted), safe


def analyze_threat(message="", url_input="", sender="", channel="Message", extra_context="") -> dict:
    """Main entry used by app.py. Returns a full analysis dict."""
    combined_text = " ".join([t for t in [message, url_input, sender, extra_context] if t]).strip()
    norm = normalize_text(combined_text)
    urls = extract_urls((message or "") + " " + (url_input or ""))
    url_results = analyze_urls(urls)
    se = detect_social_engineering(combined_text)
    sem = semantic_scores(combined_text)

    threat_type, breakdown = classify_threat(combined_text, urls, se, sem)

    # ---- risk score: weighted sum of signals ----
    score = 5.0
    # social engineering signals: each present signal adds weight
    se_weights = {"urgency": 10, "fear_threat": 11, "authority": 9, "reward": 8,
                  "financial_pressure": 13, "credential_request": 15,
                  "curiosity": 6, "emotional": 5}
    indicators = []
    label_map = {"urgency": "Urgency pressure ('act now / expire')",
                 "fear_threat": "Fear/threat language (block / penalty / legal action)",
                 "authority": "Authority impersonation (bank / officer / support)",
                 "reward": "Reward/lottery/offer lure",
                 "financial_pressure": "Payment/money request (UPI / fee / refund)",
                 "credential_request": "Credential/OTP request",
                 "curiosity": "Click/download lure",
                 "emotional": "Emotional manipulation / secrecy"}
    for k, w in se_weights.items():
        if se.get(k, {}).get("present"):
            score += w
            indicators.append(f"{label_map[k]} detected.")

    # semantic support
    top_sem = max(sem.values()) if sem else 0
    score += top_sem * 22

    # structured keyword support
    top_struct = max(breakdown.values()) if breakdown else 0
    score += min(top_struct * 0.55, 16)

    # url risk
    for r in url_results:
        score += r.get("added_risk", 0)
        for ind in r["indicators"]:
            if "only means" not in ind and "No strong" not in ind:
                indicators.append(f"URL [{r['url'][:60]}]: {ind}")

    # sender signal
    if sender and re.search(r"[+0-9]{8,}|@|unknown|private", sender, re.I):
        indicators.append(f"Sender '{sender[:60]}' looks unverified — treat as untrusted until independently verified.")
        score += 4

    # channel nudge
    if channel in ("SMS", "WhatsApp", "Email") and score > 12:
        score += 2

    if not combined_text:
        score = 5
        indicators = ["No content provided yet — paste the message/URL to analyse."]

    score = int(max(0, min(100, round(score))))
    level = risk_level(score)
    confidence = "High" if score >= 60 or len(indicators) >= 4 else ("Medium" if score >= 30 else "Low")
    why, objective, targeted, safe = build_explanation(threat_type, se, url_results, indicators)

    # suspicious indicator chips (short)
    chips = []
    for k in se:
        if se[k]["present"]:
            chips.append(k.replace("_", " ").title())
    for r in url_results:
        if r.get("added_risk", 0) >= 10:
            chips.append("Suspicious URL")

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "channel": channel,
        "threat_type": threat_type,
        "risk_score": score,
        "risk_level": level,
        "confidence": confidence,
        "indicators": indicators,
        "se_signals": {k: v["present"] for k, v in se.items()},
        "se_detail": se,
        "se_explanations": SE_EXPLANATIONS,
        "semantic": {k: round(float(v), 3) for k, v in sem.items()},
        "category_scores": {k: round(float(v), 1) for k, v in breakdown.items()},
        "urls": urls,
        "url_results": url_results,
        "url_verdicts": [url_verdict(r) for r in url_results],
        "chips": sorted(set(chips)),
        "attacker_objective": objective,
        "targeted": targeted,
        "why_risky": why,
        "safe_action": safe,
        "raw_text": combined_text[:2000],
        "sender": sender or "",
        # ADDITIVE keys (old readers ignore them safely):
        "entities": extract_entities(combined_text, sender or ""),
        "highlight_spans": suspicious_spans(message or combined_text, se),
        "highlight_html": highlight_html(message or combined_text, suspicious_spans(message or combined_text, se)),
        "message_only": message or "",
    }
