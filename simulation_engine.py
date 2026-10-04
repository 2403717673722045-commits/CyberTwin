"""
CyberTwin - simulation_engine.py
Counterfactual What-If Simulator.

Given a threat analysis, generates plausible consequence paths for:
 Proceed / Ignore / Verify / Report.
These are SIMULATED plausible outcomes, not guaranteed predictions.
"""

ACTIONS = ["Proceed", "Ignore", "Verify", "Report", "Block"]


def _residual(base_score: int, kind: str) -> int:
    """Threat-dependent residual risk (not blindly hard-coded)."""
    b = base_score
    if kind == "Ignore":
        # high original risk -> still some exposure (re-targeting); low -> near zero
        return max(5, min(40, 5 + b // 5))
    if kind == "Verify":
        return 5
    if kind == "Report":
        return max(4, min(15, 4 + b // 20))
    if kind == "Block":
        return max(3, min(12, 3 + b // 25))
    return b


def _proceed_chain(threat_type, risk_score):
    t = (threat_type or "").lower()
    if "job" in t:
        chain = ["Threat: fake job/task offer", "You proceed: pay 'registration fee' / share ID + bank details",
                 "Attacker: keeps fee, asks for more 'unlock higher earnings'",
                 "Consequence: money lost + personal data exposed", "Impact: financial loss, identity misuse risk"]
        consequence = "Likely fee theft and follow-up demands for more money or data."
    elif "invest" in t:
        chain = ["Threat: fake investment pitch", "You proceed: transfer initial amount",
                 "Attacker: shows fake profits, pushes bigger deposit",
                 "Consequence: larger deposit stolen, contact disappears", "Impact: significant financial loss"]
        consequence = "Classic advance-fee pattern: small win shown, then bigger theft."
    elif "bank" in t or ("financial" in t and "phish" not in t) or "upi" in t or "payment" in t:
        chain = ["Threat: banking/payment scam", "You proceed: click link → fake banking page",
                 "Attacker: fake page captures credentials + card/OTP",
                 "Consequence: credentials/payment info exposed → unauthorised debits", "Impact: account/financial risk, possible full balance loss"]
        consequence = "Fake banking page harvests login + payment data for immediate theft."
    elif "impersonation" in t or "social engineering" in t or "social" in t:
        chain = ["Threat: social-media impersonation", "You proceed: continue conversation, share personal info",
                 "Attacker: social engineering — builds trust, requests codes/money",
                 "Consequence: personal data leaked, possible account/privacy compromise", "Impact: account/privacy risk + follow-up scams on contacts"]
        consequence = "Continued chat hands the impersonator data and leverage over you and your contacts."
    elif "harassment" in t or "blackmail" in t:
        chain = ["Threat: harassment/blackmail", "You proceed: pay or send more content under pressure",
                 "Attacker: keeps demanding more — never deletes material",
                 "Consequence: repeated extortion, deeper exposure", "Impact: financial + severe emotional/privacy harm"]
        consequence = "Paying blackmail rarely ends it — it signals you will pay again. Preserve evidence, seek help, report."
    elif "deliver" in t or "refund" in t:
        chain = ["Threat: delivery/refund lure", "You proceed: pay small 'fee' + enter card details",
                 "Attacker: harvests card/bank data, attempts more charges",
                 "Consequence: card fraud / repeated debits", "Impact: financial + credential exposure"]
        consequence = "Small fee leads to card-data capture and further fraud attempts."
    elif "credential" in t or "phish" in t or "account" in t or "malicious link" in t:
        chain = ["Threat: phishing / fake login link", "You proceed: click link → open fake website",
                 "Attacker: fake page records what you type",
                 "Consequence: credentials/OTP captured → account compromise", "Impact: account takeover, possible money/data loss"]
        consequence = "Entering credentials or codes on the fake page hands over account control."
    elif "impersonation" in t:
        chain = ["Threat: impersonated authority/contact", "You proceed: follow instructions (pay/share code)",
                 "Attacker: exploits trust, escalates demands",
                 "Consequence: payment sent / account codes shared", "Impact: financial loss or account loss"]
        consequence = "Acting on trust alone lets the impersonator convert authority into money/access."
    elif "financial" in t:
        chain = ["Threat: payment/scam request", "You proceed: approve UPI/collect request or transfer",
                 "Attacker: withdraws quickly, blocks contact",
                 "Consequence: money sent, hard to reverse", "Impact: direct financial loss"]
        consequence = "Once UPI/money is sent to a scammer, recovery is difficult."
    else:
        chain = ["Threat: suspicious message", "You proceed: click / reply / share requested info",
                 "Attacker: uses your response to escalate (more links, fees, codes)",
                 "Consequence: deeper engagement → higher chance of loss", "Impact: moderate-high, depends on what is shared"]
        consequence = "Continuing the conversation gives the attacker more leverage."
    risk = min(100, max(risk_score, 70) + 5)
    return chain, consequence, risk


def simulate_action(threat_result: dict) -> dict:
    threat_type = threat_result.get("threat_type", "Unknown")
    risk_score = threat_result.get("risk_score", 50)

    p_chain, p_cons, p_risk = _proceed_chain(threat_type, risk_score)

    out = {
        "Proceed": {
            "chain": p_chain,
            "consequence": p_cons,
            "impact": "High — money, account or data loss is plausible.",
            "residual_risk": p_risk,
            "verdict": "Unsafe",
        },
        "Ignore": {
            "chain": ["Threat arrives", "You ignore: no click, no reply, no payment",
                      "Attacker: gets no response, moves on",
                      "Consequence: no data shared, no money moved",
                      "Impact: none — you stay safe but attacker is not stopped"],
            "consequence": "Ignoring protects you personally but the scam may reach others.",
            "impact": "None to you; threat unresolved for others.",
            "residual_risk": _residual(risk_score, "Ignore"),
            "verdict": "Safe for you",
        },
        "Verify": {
            "chain": ["Threat arrives", "You verify: contact official source independently (official app/number)",
                      "Attacker claim collapses under independent check",
                      "Consequence: scam identified before any action",
                      "Impact: full protection + clarity"],
            "consequence": "Independent verification is the strongest personal defence.",
            "impact": "Full protection, no loss.",
            "residual_risk": _residual(risk_score, "Verify"),
            "verdict": "Safest ✓",
        },
        "Report": {
            "chain": ["Threat arrives", "You report: save evidence + report (platform / cybercrime portal / bank)",
                      "Attacker: account/link may get flagged; evidence preserved",
                      "Consequence: helps takedown + your complaint record",
                      "Impact: protects you and others"],
            "consequence": "Reporting preserves evidence and helps protect the community.",
            "impact": "Protection + community benefit.",
            "residual_risk": _residual(risk_score, "Report"),
            "verdict": "Recommended alongside Verify",
        },
        "Block": {
            "chain": ["Threat arrives", "You block: sender blocked, thread deleted without clicking",
                      "Attacker: cannot re-contact from same ID; moves on",
                      "Consequence: no engagement, fewer follow-ups",
                      "Impact: personal protection + less noise (pair with Report to help others)"],
            "consequence": "Blocking cuts contact and follow-up pressure. Best paired with Report so the scam is also flagged.",
            "impact": "Low personal risk; report separately for community benefit.",
            "residual_risk": _residual(risk_score, "Block"),
            "verdict": "Safe + quiet",
        },
    }
    return out


# ---------------------------------------------------------------------------
# ADDITIVE: Decision Replay — "What if you had…"
# ---------------------------------------------------------------------------

REPLAY_SCENARIOS = [
    "clicked the link", "entered your password", "shared the OTP",
    "made the payment", "downloaded the file", "verified first",
]

REPLAY_GUIDE = {
    "clicked the link": ("Close tab, grant nothing, scan device, keep URL as evidence.",
                         "If credentials were then entered, change password officially + enable 2FA."),
    "entered your password": ("Change it NOW via official site, everywhere reused; enable 2FA; revoke sessions.",
                              "Check activity + linked email/phone changes."),
    "shared the OTP": ("Call bank/provider IMMEDIATELY; freeze/review; note transaction IDs; file complaint fast.",
                       "Time matters — OTPs authorise access/transfers instantly."),
    "made the payment": ("Call bank/UPI provider for hold/recall (save UTR); never pay a 'refund fee'; file complaint.",
                         "Monitor statements 2-4 weeks."),
    "downloaded the file": ("Delete, do not reopen; full antivirus scan; change passwords from clean device.",
                            "Watch bank statements if banking apps were on the device."),
    "verified first": ("Independent check via official app/number exposes the scam before loss.",
                       "Then block + report with evidence."),
}


def decision_replay(threat_result: dict, scenario: str) -> dict:
    """Plausible attack path + safer alternative for a past/future micro-decision."""
    t = (threat_result.get("threat_type") or "suspicious message")
    s = (scenario or "").lower()
    if "click" in s:
        chain = [f"Threat: {t}", "You click the link → fake page/app opens",
                 "Attacker: page mimics brand, records input / offers download",
                 "Consequence: device exposed; any typed data captured", "Impact: account/data risk if you continue"]
    elif "password" in s or "credential" in s:
        chain = [f"Threat: {t}", "You enter username/password on fake page",
                 "Attacker: replays credentials on real site, changes recovery options",
                 "Consequence: account takeover", "Impact: high — data, money, impersonation of you"]
    elif "otp" in s:
        chain = [f"Threat: {t}", "You share the OTP/code",
                 "Attacker: instantly authorises login or transaction",
                 "Consequence: account or money gone in seconds", "Impact: critical"]
    elif "payment" in s or "pay" in s:
        chain = [f"Threat: {t}", "You approve transfer/UPI collect/fee",
                 "Attacker: withdraws fast, vanishes", "Consequence: money lost, hard to reverse",
                 "Impact: direct financial loss"]
    elif "download" in s or "file" in s:
        chain = [f"Threat: {t}", "You download/open the file",
                 "Attacker: malware/spyware installs or steals session/data",
                 "Consequence: device compromise", "Impact: high — passwords, bank apps at risk"]
    else:  # verified first
        chain = [f"Threat: {t}", "You pause and verify via official channel",
                 "Attacker claim fails the check", "Consequence: scam identified, nothing lost",
                 "Impact: full protection"]
    g1, g2 = REPLAY_GUIDE.get(scenario, ("Verify independently; preserve evidence; block + report.", ""))
    return {"scenario": scenario, "chain": chain,
            "consequence": chain[3] if len(chain) > 3 else "",
            "impact": chain[4] if len(chain) > 4 else "",
            "safer_alternative": f"{g1} {g2}".strip()}


def recommended_action(threat_result: dict) -> str:
    lvl = threat_result.get("risk_level", "Medium")
    if lvl in ("Critical", "High"):
        return "Verify + Report — do not proceed. Verify independently, preserve evidence, and report."
    if lvl == "Medium":
        return "Verify first — confirm through an official channel before any action."
    return "Stay cautious — verify if anything asks for money, codes, or clicks."
