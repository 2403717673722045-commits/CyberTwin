"""
CyberTwin - incident_engine.py
Protection & Recovery guidance based on what already happened.
Never asks for real passwords or OTPs.
"""

PLANS = {
    "Only received the message": {
        "urgency": "Low — no interaction yet.",
        "steps": [
            "Do NOT click links, scan QR, download files, or reply.",
            "Take screenshots; note sender ID/number, date and time.",
            "Block and report the sender inside the app (SMS/WhatsApp/Email > Report spam).",
            "If it claims to be your bank/company, verify via the official app or number you already know.",
            "Share a warning with family if the same message is spreading.",
        ],
    },
    "Clicked the link": {
        "urgency": "Medium — device/browser may be exposed.",
        "steps": [
            "Disconnect from the internet briefly; close the suspicious tab — do NOT enter anything.",
            "Do NOT grant permissions or download anything the site offers.",
            "Clear browser cache / run a reputable mobile/antivirus scan.",
            "If you entered NO credentials, still change nothing but stay alert for follow-up messages.",
            "Preserve the URL + screenshots as evidence; report the link.",
        ],
    },
    "Entered credentials": {
        "urgency": "High — assume the password/username is compromised.",
        "steps": [
            "Immediately change that password from a CLEAN device via the OFFICIAL site/app (type address yourself).",
            "Turn on 2-step verification where available; review active sessions and log out unknown ones.",
            "If you reuse that password anywhere, change it everywhere (use a password manager).",
            "Check account activity (login alerts, linked email/phone changes).",
            "Watch for OTP-scam follow-ups — NEVER share OTPs with callers.",
            "Preserve evidence (URL, screenshots, time) for your complaint draft.",
        ],
    },
    "Shared OTP": {
        "urgency": "Critical — OTPs give instant access or authorize transactions.",
        "steps": [
            "Call your bank / service provider IMMEDIATELY from their official number; ask to freeze or review recent activity.",
            "Change passwords + revoke sessions for the affected account.",
            "Check bank/wallet statements for unknown debits; note transaction IDs.",
            "Enable SIM-lock awareness: if calls/SMS stop working, contact your telecom provider (possible SIM-swap).",
            "File a complaint quickly — time matters for financial fraud. Keep evidence ready.",
        ],
    },
    "Made a payment": {
        "urgency": "Critical — money has moved.",
        "steps": [
            "Call your bank/UPI provider NOW (official number) — request hold/recall of the transaction.",
            "Save UTR / transaction ID, recipient UPI ID/number, amount, date-time and screenshots.",
            "Do NOT pay any 'refund fee' the scammer demands to return money — it is a second scam.",
            "File a cybercrime complaint with transaction evidence; also inform your bank in writing.",
            "Monitor statements for 2-4 weeks; alert bank of any further suspicious debits.",
        ],
    },
    "Downloaded a file": {
        "urgency": "High — malware risk.",
        "steps": [
            "Do NOT open the file again. Delete it; disconnect from Wi-Fi if the device behaves oddly.",
            "Run a full antivirus/mobile-security scan; update OS and apps.",
            "Change important passwords from a different clean device.",
            "Back up important data; if banking apps were on the device, check statements closely.",
            "Keep the file name/source info as evidence (do not forward the file).",
        ],
    },
}

ORDER = list(PLANS.keys())


def get_plan(stage: str) -> dict:
    return PLANS.get(stage, PLANS["Only received the message"])


def mask_value(v: str, keep: int = 2) -> str:
    """Mask sensitive strings: keep first/last few chars only."""
    if not v:
        return ""
    v = str(v).strip()
    if len(v) <= 4:
        return "*" * len(v)
    return v[:keep] + "*" * (len(v) - keep * 2) + v[-keep:]
