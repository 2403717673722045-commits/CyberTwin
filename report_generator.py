"""
CyberTwin - report_generator.py
Evidence-aware complaint draft generation.
Never fabricates complaint numbers, authority responses, or official status.
"""

from datetime import datetime


def generate_complaint(evidence: dict, analysis: dict, what_happened: str, extra_notes: str = "") -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append("CYBERTWIN — CYBER INCIDENT COMPLAINT DRAFT (for user review)")
    lines.append(f"Prepared on: {ts}")
    lines.append("NOTE: This is a USER-PREPARED draft, not an official complaint. Review, edit,")
    lines.append("and submit it yourself through your official cybercrime reporting channel.")
    lines.append("=" * 70)
    lines.append(f"Incident type (AI assessment): {analysis.get('threat_type','-')}  |  Risk: {analysis.get('risk_score','-')}/100 ({analysis.get('risk_level','-')})  |  Confidence: {analysis.get('confidence','-')}")
    lines.append(f"Date/time of incident: {evidence.get('datetime','-')}")
    lines.append(f"Channel: {analysis.get('channel','-')}")
    lines.append(f"What already happened: {what_happened}")
    lines.append("")
    lines.append("--- DESCRIPTION ---")
    lines.append(evidence.get("description") or analysis.get("raw_text","-") or "-")
    lines.append("")
    lines.append("--- SENDER / CONTACT ---")
    lines.append(f"Sender email/phone/profile: {evidence.get('sender','-')}")
    lines.append(f"Social profile info: {evidence.get('social','-')}")
    ent = (analysis.get("entities") or {}) if isinstance(analysis, dict) else {}
    if ent:
        if ent.get("emails"): lines.append(f"Extracted emails: {', '.join(ent['emails'][:5])}")
        if ent.get("phones"): lines.append(f"Extracted phones: {', '.join(ent['phones'][:5])}")
        if ent.get("sender_name_guess"): lines.append(f"Sender-name hint: {ent['sender_name_guess']}")
    lines.append("")
    lines.append("--- URL / LINK ---")
    lines.append(f"URL: {evidence.get('url','-')}")
    lines.append("")
    lines.append("--- TRANSACTION (if any) ---")
    lines.append(f"Details: {evidence.get('transaction','-')}")
    lines.append(f"UPI / payment info (masked): {evidence.get('upi','-')}")
    if ent and (ent.get("amounts") or ent.get("upi_ids")):
        lines.append(f"Extracted amounts: {', '.join(ent.get('amounts', [])[:5]) or '-'}")
        lines.append(f"Extracted UPI IDs: {', '.join(ent.get('upi_ids', [])[:5]) or '-'}")
    lines.append("")
    lines.append("--- EVIDENCE AVAILABLE ---")
    lines.append(f"{evidence.get('evidence_desc','-')}")
    if evidence.get("screenshot_note"): lines.append(f"Screenshot: {evidence.get('screenshot_note')}")
    if evidence.get("qr_note"): lines.append(f"QR info: {evidence.get('qr_note')}")
    lines.append("")
    lines.append("--- AI DETECTED INDICATORS (supporting info, not proof) ---")
    for ind in analysis.get("indicators", [])[:12]:
        lines.append(f" - {ind}")
    if not analysis.get("indicators"):
        lines.append(" - None recorded")
    se = analysis.get("se_signals", {}) if isinstance(analysis, dict) else {}
    found_se = [k for k, v in se.items() if v]
    if found_se:
        lines.append(f"Social-engineering signals: {', '.join(found_se)}")
    lines.append("")
    lines.append("--- POTENTIAL IMPACT ---")
    lines.append(f"Attacker objective (assessed): {analysis.get('attacker_objective','-')}")
    lines.append(f"Targeted: {analysis.get('targeted','-')}")
    lines.append("")
    lines.append("--- RECOMMENDED ACTIONS ---")
    lines.append(f"{analysis.get('safe_action','-')}")
    lines.append("")
    if extra_notes:
        lines.append("--- ADDITIONAL NOTES BY USER ---")
        lines.append(extra_notes)
        lines.append("")
    lines.append("--- DECLARATION ---")
    lines.append("I confirm the above details are true to my knowledge. I understand this draft")
    lines.append("must be reviewed and submitted by me through official channels.")
    lines.append("")
    lines.append("Name: ______________________   Signature: ____________   Date: __________")
    return "\n".join(lines)


def generate_evidence_report(evidence: dict, analysis: dict | None, sim: dict | None,
                             what_happened: str = "", decision: str = "",
                             protection_steps: list | None = None) -> str:
    """Single coherent incident/evidence pack (Req 13): original input + media +
    entities + classification + scores + signals + explanation + paths + guidance + draft."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    L = []
    L.append("CYBERTWIN — FULL INCIDENT / EVIDENCE REPORT (user-managed)")
    L.append(f"Generated: {ts}")
    L.append("This pack organises YOUR inputs for reporting/follow-up. It is not an official filing.")
    L.append("=" * 70)
    a = analysis or {}
    L.append(f"Threat classification: {a.get('threat_type','-')}")
    L.append(f"Risk score: {a.get('risk_score','-')}/100 | Level: {a.get('risk_level','-')} | Confidence: {a.get('confidence','-')}")
    L.append(f"Channel: {a.get('channel','-')} | Time analysed: {a.get('timestamp','-')}")
    L.append(f"What happened: {what_happened or '-'} | Selected decision: {decision or '-'}")
    L.append("")
    L.append("--- 1. ORIGINAL INPUT ---")
    L.append((evidence.get("description") or a.get("raw_text") or "-"))
    L.append("")
    if evidence.get("screenshot_note") or evidence.get("qr_note"):
        L.append("--- 2. SCREENSHOT / QR ---")
        L.append(f"Screenshot: {evidence.get('screenshot_note','-')}")
        L.append(f"QR: {evidence.get('qr_note','-')}")
        L.append(f"QR decoded data: {(evidence.get('qr_data','-') or '-')[:500]}")
        L.append("")
    L.append("--- 3. EXTRACTED SENDER / CONTACT DETAILS ---")
    ent = (a.get("entities") or {})
    L.append(f"Sender field: {evidence.get('sender') or a.get('sender') or '-'}")
    for k in ("emails", "phones", "urls", "dates_times", "amounts", "upi_ids", "payment_refs", "social_hints"):
        L.append(f"{k}: {', '.join(ent.get(k, [])[:8]) or '-'}")
    L.append(f"Social profile field: {evidence.get('social','-')}")
    L.append("")
    L.append("--- 4. DETECTED INDICATORS ---")
    for ind in (a.get("indicators") or [])[:15]:
        L.append(f" - {ind}")
    L.append("")
    L.append("--- 5. SOCIAL-ENGINEERING SIGNALS ---")
    se = a.get("se_signals", {}) or {}
    exp = a.get("se_explanations", {}) or {}
    for k, v in se.items():
        L.append(f" - {k}: {'YES — ' + exp.get(k,'') if v else 'not detected'}")
    L.append("")
    L.append("--- 6. EXPLANATION ---")
    for w in (a.get("why_risky") or [])[:10]:
        L.append(f" - {w}")
    L.append(f"Attacker objective: {a.get('attacker_objective','-')}")
    L.append(f"Targeted: {a.get('targeted','-')}")
    L.append("")
    L.append("--- 7. ATTACK PATH + RISK COMPARISON ---")
    if sim:
        for act, d in sim.items():
            L.append(f"[{act}] residual ~{d.get('residual_risk')}/100 — {' → '.join(d.get('chain', []))[:300]}")
    L.append(f"Recommended: {a.get('safe_action','-')}")
    L.append("")
    L.append("--- 8. PROTECTION / RECOVERY GUIDANCE ---")
    for s in (protection_steps or []):
        L.append(f" - {s}")
    L.append("")
    L.append("--- 9. COMPLAINT DRAFT (edit before submitting) ---")
    L.append(generate_complaint(evidence, a, what_happened or "Only received the message"))
    return "\n".join(L)
