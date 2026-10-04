"""
CyberTwin - copilot.py
Contextual rule-based AI Cyber Copilot (no external API needed).
Uses current threat analysis + simulation context to answer questions.
Upgrade point: plug an LLM here with the same function signature.
"""

import re


def answer_question(question: str, analysis: dict | None, sim: dict | None = None,
                    evidence: dict | None = None, incident: str | None = None) -> str:
    q = (question or "").lower().strip()
    if not q:
        return "Ask me e.g. 'Why is this risky?', 'I clicked the link, what now?', 'How do I verify this?'"

    has = analysis is not None and analysis.get("threat_type")
    ttype = (analysis.get("threat_type") if has else "unknown")
    risk = (f"{analysis.get('risk_score')}/100 ({analysis.get('risk_level')})" if has else "unknown (analyse a message first)")

    def ctx(prefix=""):
        parts = []
        if has:
            parts.append(f"{ttype}, risk {risk}")
            if analysis.get("sender"):
                parts.append(f"sender '{str(analysis.get('sender'))[:50]}'")
            if analysis.get("urls"):
                parts.append(f"URL(s): {', '.join(analysis.get('urls', [])[:2])[:80]}")
        else:
            return f"{prefix}No analysis yet — paste a message in Threat Analysis first."
        extra = ""
        if sim and isinstance(sim, dict):
            try:
                rec = min(sim.items(), key=lambda kv: kv[1].get("residual_risk", 99))[0]
                extra += f" Safest simulated option right now: {rec}."
            except Exception:
                pass
        if incident:
            extra += f" Your selected incident stage: {incident}."
        if evidence and isinstance(evidence, dict) and any(evidence.values()):
            extra += " Evidence is saved for this case."
        return f"{prefix}Current case: {'; '.join(parts)}.{extra}"

    if re.search(r"why.*risk|why.*danger|explain|reasons?", q):
        if not has:
            return ctx()
        inds = analysis.get("indicators", [])[:6]
        why = "\n".join(f"• {i}" for i in inds) if inds else "• No strong indicators recorded."
        return (f"This looks risky because:\n{why}\n\nAttacker objective (assessed): {analysis.get('attacker_objective','-')}\n"
                f"Targeted: {analysis.get('targeted','-')}\n{ctx(chr(10))}\nThese are risk indicators, not proof — verify independently.")

    if re.search(r"clicked|opened.*link|tapped", q):
        if has and analysis.get("urls"):
            pre = f"For THIS case ({ttype}): the link(s) {', '.join(analysis['urls'][:2])[:100]} carry risk {risk}. "
        elif has:
            pre = f"For THIS case ({ttype}, risk {risk}): "
        else:
            pre = ""
        return (pre + "If you clicked but entered NOTHING:\n1) Close the tab, don't grant permissions/downloads.\n"
                "2) Run an antivirus/mobile scan, clear cache.\n3) Keep the URL + screenshots as evidence.\n\n"
                "If you ENTERED credentials/codes, treat it as compromised: change the password from the official site, "
                "enable 2-step verification, revoke unknown sessions. " + ctx("\n"))

    if re.search(r"password|credential|login.*enter|changed?", q):
        return ("Treat the password as exposed:\n1) Change it NOW via the official site/app (type the address yourself).\n"
                "2) Change it everywhere you reused it.\n3) Turn on 2-step verification + check recent activity.\n"
                "Never share passwords/OTPs with anyone. " + ctx("\n"))

    if re.search(r"otp|code.*shar", q):
        return ("Sharing an OTP is critical:\n1) Call your bank/provider IMMEDIATELY from the official number.\n"
                "2) Ask to freeze/review recent activity; note transaction IDs.\n3) Change passwords, watch statements.\n"
                "File a complaint quickly — time matters. " + ctx("\n"))

    if re.search(r"pay|payment|upi|money|transaction|refund|sent.*amount", q):
        return ("If money was sent:\n1) Call your bank/UPI provider NOW, request hold/recall (save UTR/transaction ID).\n"
                "2) Never pay a 'refund fee' to get it back — that's a second scam.\n"
                "3) Prepare transaction screenshots + IDs for your complaint draft. " + ctx("\n"))

    if re.search(r"verif|real.*or.*fake|genuine|trust|official", q):
        return ("How to verify:\n1) STOP — don't use links/numbers inside the suspicious message.\n"
                "2) Open the official app/website independently or call the number on your card/official site.\n"
                "3) Check exact domain spelling, HTTPS alone proves nothing.\n"
                "4) Ask: did you expect this message? Is there urgency/threat/reward pressure? " + ctx("\n"))

    if re.search(r"evidence|preserve|screenshot|proof|collect", q):
        return ("Preserve:\n• Full message text + sender ID/number\n• URL (copy exactly, don't open)\n• Date/time + channel (SMS/WhatsApp/email)\n"
                "• Screenshots of message + any payment screens\n• Transaction IDs / UPI IDs (mask when sharing)\n"
                "Use the Evidence page — it feeds directly into your complaint draft.")

    if re.search(r"report|complaint|police|cybercrime|fir", q):
        return ("To report:\n1) Organise evidence (Evidence page).\n2) Generate the complaint draft (Complaint page), review + edit it.\n"
                "3) Submit yourself via your country's official cybercrime portal / local police / bank.\n"
                "CyberTwin does NOT file on your behalf and never invents complaint numbers. "
                "Track your reference on the Tracking page (internal/user-entered only).")

    if re.search(r"\bdangerous\b|is this.*(scam|fraud|fake|safe)|should i worry", q):
        if not has:
            return ctx()
        inds = "; ".join(analysis.get("indicators", [])[:4]) or "see Threat Analysis"
        return (f"My assessment of THIS message: {ttype}, risk {risk} (confidence {analysis.get('confidence','-')}). "
                f"Top indicators: {inds}. Safe action: {analysis.get('safe_action','Verify independently.')}. "
                "This is decision support, not proof — verify independently." + ctx("\n"))

    if re.search(r"download|file|apk|attachment|malware|virus", q):
        return ("If you downloaded a file:\n1) Don't open it again — delete it.\n2) Run a full antivirus scan, update OS/apps.\n"
                "3) Change important passwords from a clean device; watch bank statements. " + ctx("\n"))

    if re.search(r"what.*do|action|safest|should i|next step|recommend", q):
        if has:
            return (f"Safest path: {analysis.get('safe_action','Verify independently.')}\n"
                    "General rule: Verify through an official channel + Report (preserve evidence). Ignoring protects you; "
                    "verifying + reporting protects you and others. " + ctx("\n"))
        return ctx()

    if re.search(r"hi|hello|hey|who are you", q):
        return ("Hi! I'm your CyberTwin Copilot. I can explain your current risk result, guide verification, "
                "or walk you through post-incident steps. " + ctx("\n") + " Try: 'Why is this risky?' or 'I clicked the link, what now?'")

    # fallback: echo context
    if has:
        return (f"Based on your current result ({ttype}, risk {risk}): avoid proceeding. "
                f"Key indicators: {'; '.join(analysis.get('indicators', [])[:3]) or 'see Threat Analysis'}. "
                "Ask me specifically: verification steps, clicked-link recovery, payment recovery, or evidence help.")
    return ("I don't have an analysis for that yet. Paste the suspicious message/URL in Threat Analysis first, "
            "then ask me e.g. 'Why is this risky?' or 'How do I verify this?'")
