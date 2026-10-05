"""
CyberTwin: AI-Powered Counterfactual Cyber-Risk Simulator
FRONTEND REDESIGN (left sidebar + landing dashboard + per-page visuals).
Backend logic UNCHANGED — same engines, same calls, same session-state contract.
Detect -> Explain -> Simulate -> Protect -> Report -> Track -> Learn
Run:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime

import plotly.express as px

from threat_engine import analyze_threat, analyze_single_url, url_verdict
from simulation_engine import simulate_action, recommended_action, decision_replay, REPLAY_SCENARIOS
from incident_engine import get_plan, ORDER
from report_generator import generate_complaint, generate_evidence_report
from copilot import answer_question

# ---------------------------------------------------------------- page config
st.set_page_config(page_title="CyberTwin",
                   page_icon="🛡️", layout="wide",
                   initial_sidebar_state="expanded")

# ------------------------------------------------------- session state init (keys UNCHANGED)
defaults = {
    "analysis": None, "sim": None, "history": [], "evidence": {},
    "tracking": [], "copilot_hist": [], "quiz_score": 0, "quiz_done": {},
    "complaint_text": "", "nav": "Dashboard",
    "incident_stage": "Only received the message", "decision": "Verify",
    "screenshot_note": "", "qr_note": "", "qr_data": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Migrate legacy nav values from the top-navbar build -> 11-item sidebar (functionality preserved)
_LEGACY_NAV = {"Home": "Dashboard", "Dashboard": "Dashboard",
               "Threat Analysis": "Threat Analysis",
               "URL Analysis": "URL Analysis",
               "Simulator": "What-If Simulator", "What-If Simulator": "What-If Simulator",
               "Protection": "Protection & Recovery", "Protection & Recovery": "Protection & Recovery",
               "Evidence": "Evidence",
               "Reports": "Complaint Generator", "Complaint Generator": "Complaint Generator",
               "Complaint Tracking": "Complaint Tracking",
               "Copilot": "AI Copilot", "AI Copilot": "AI Copilot",
               "History": "Risk History", "Risk History": "Risk History",
               "Training": "Awareness Training", "Awareness Training": "Awareness Training"}
if st.session_state.nav in _LEGACY_NAV:
    st.session_state.nav = _LEGACY_NAV[st.session_state.nav]

NAV = ["Dashboard", "Threat Analysis", "URL Analysis", "What-If Simulator",
       "Protection & Recovery", "Evidence", "Complaint Generator",
       "Complaint Tracking", "AI Copilot", "Risk History", "Awareness Training", "ML Model Lab"]
ICON = {"Dashboard": "🏠", "Threat Analysis": "🔍", "URL Analysis": "🔗",
        "What-If Simulator": "🔀", "Protection & Recovery": "🛡️", "Evidence": "🗂️",
        "Complaint Generator": "📄", "Complaint Tracking": "📌", "AI Copilot": "🤖",
        "Risk History": "📊", "Awareness Training": "🎓", "ML Model Lab": "🔬"}
if st.session_state.nav not in NAV:
    st.session_state.nav = "Dashboard"

# ------------------------------------------------------------------ PREMIUM CYBER THEME (sidebar + glass)
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root{
  --bg0:#050816; --bg1:#08111F; --bg2:#0B1220;
  --blue:#2563EB; --blue2:#3B82F6; --cyan:#06B6D4; --purple:#7C3AED; --violet:#8B5CF6;
  --ok:#22C55E; --warn:#F59E0B; --bad:#EF4444; --crit:#DC2626;
  --txt:#F8FAFC; --mut:#94A3B8;
}
html,body,[class*="css"]{ font-family:'Inter',system-ui,sans-serif; }
.stApp{ background:
  radial-gradient(1100px 500px at 85% -5%, rgba(124,58,237,.22), transparent 60%),
  radial-gradient(900px 480px at 8% 8%, rgba(37,99,235,.25), transparent 55%),
  radial-gradient(700px 500px at 55% 110%, rgba(6,182,212,.12), transparent 60%),
  linear-gradient(180deg,#050816 0%,#08111F 55%,#0B1220 100%) !important;
  color:var(--txt);
}
/* ---- left sidebar (default Streamlit sidebar, themed only — never hidden) ---- */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,rgba(8,17,31,.97),rgba(11,18,32,.97)) !important;
  border-right:1px solid rgba(139,92,246,.30) !important;
  box-shadow:6px 0 28px rgba(37,99,235,.15);
}
section[data-testid="stSidebar"] .stRadio > div{ gap:6px; }
section[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] p{
  font-size:11px; font-weight:800; letter-spacing:.14em; color:#67e8f9;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label{
  background:rgba(13,25,48,.55); border:1px solid rgba(99,102,241,.22);
  border-radius:12px; padding:9px 12px; margin:2px 0; transition:all .18s ease;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{
  border-color:rgba(34,211,238,.55); background:rgba(37,99,235,.18);
  box-shadow:0 4px 16px rgba(37,99,235,.25); transform:translateX(2px);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){
  background:linear-gradient(90deg,rgba(37,99,235,.35),rgba(124,58,237,.35));
  border-color:#22D3EE; box-shadow:0 0 18px rgba(34,211,238,.35);
}
section[data-testid="stSidebar"] div[role="radiogroup"] p{ font-size:13.5px; font-weight:600; color:var(--txt); }
.side-brand{ font-weight:900; font-size:21px;
  background:linear-gradient(90deg,#60A5FA,#22D3EE,#A78BFA);
  -webkit-background-clip:text; background-clip:text; color:transparent; }
h1,h2,h3,h4{ color:var(--txt)!important; letter-spacing:-.02em; }
.small{ font-size:12.5px; color:var(--mut); }
.grad-text{ background:linear-gradient(90deg,#60A5FA,#22D3EE,#A78BFA);
  -webkit-background-clip:text; background-clip:text; color:transparent; }
.hero{ border-radius:24px; padding:44px 40px; position:relative; overflow:hidden;
  background:linear-gradient(135deg,rgba(37,99,235,.20),rgba(124,58,237,.20) 55%,rgba(6,182,212,.14));
  border:1px solid rgba(139,92,246,.35); box-shadow:0 24px 70px rgba(37,99,235,.25); }
.hero::before{ content:""; position:absolute; inset:-40%; background:
  radial-gradient(circle at 30% 30%, rgba(6,182,212,.20), transparent 40%),
  radial-gradient(circle at 70% 60%, rgba(139,92,246,.25), transparent 42%);
  animation:drift 14s ease-in-out infinite alternate; pointer-events:none; }
@keyframes drift{ from{transform:translate(-2%,-1%) scale(1);} to{transform:translate(2%,2%) scale(1.06);} }
.hero-grid{ position:relative; z-index:1; }
.hero-flex{ position:relative; z-index:1; display:flex; gap:28px; align-items:center; }
.hero-text{ flex:1.3; min-width:0; }
.hero-art{ flex:1; min-width:0; }
.art-img{ width:100%; border-radius:14px; border:1px solid rgba(139,92,246,.4);
  box-shadow:0 14px 40px rgba(37,99,235,.30); }
.hero-kicker{ display:inline-block; font-size:12px; font-weight:700; letter-spacing:.14em; color:#67e8f9;
  border:1px solid rgba(6,182,212,.5); border-radius:999px; padding:5px 14px; background:rgba(6,182,212,.10); }
.hero-title{ font-size:54px; font-weight:900; line-height:1.02; margin:14px 0 6px 0; }
.hero-tag{ font-size:19px; color:#E2E8F0; font-weight:600; }
.hero-desc{ color:#C7D2FE; font-size:14.5px; max-width:640px; }
.glass{ background:rgba(13,25,48,.72); border:1px solid rgba(99,102,241,.28); border-radius:18px;
  padding:18px 20px; box-shadow:0 12px 32px rgba(2,6,23,.55); backdrop-filter:blur(10px); }
.glass:hover{ border-color:rgba(34,211,238,.45); }
.page-banner{ display:flex; gap:18px; align-items:center; border-radius:20px; padding:20px 22px;
  background:linear-gradient(135deg,rgba(37,99,235,.18),rgba(124,58,237,.18));
  border:1px solid rgba(139,92,246,.35); box-shadow:0 14px 40px rgba(37,99,235,.20); margin-bottom:14px; }
.page-banner .art{ flex:0 0 200px; max-width:220px; }
.page-banner .txt{ flex:1; min-width:0; }
.flow-card{ text-align:center; position:relative; }
.flow-num{ font-size:12px; font-weight:800; letter-spacing:.12em; color:#67e8f9; }
.flow-ic{ font-size:30px; }
.feat-ic{ font-size:26px; }
.step-line{ height:2px; background:linear-gradient(90deg,var(--blue2),var(--cyan),var(--violet)); border-radius:2px; margin:10px 0; }
.sev{ display:inline-block; font-weight:800; font-size:13px; border-radius:999px; padding:5px 16px; letter-spacing:.06em; }
.sev-LOW{ background:rgba(34,197,94,.15); color:#4ADE80; border:1px solid #22C55E; }
.sev-MEDIUM{ background:rgba(245,158,11,.15); color:#FBBF24; border:1px solid #F59E0B; }
.sev-HIGH{ background:rgba(239,68,68,.16); color:#FCA5A5; border:1px solid #EF4444; }
.sev-CRITICAL{ background:linear-gradient(90deg,rgba(220,38,38,.35),rgba(239,68,68,.25)); color:#FECACA; border:1px solid #DC2626; box-shadow:0 0 18px rgba(220,38,38,.45); }
.chip{ display:inline-block; background:rgba(37,99,235,.14); border:1px solid rgba(59,130,246,.5); color:#DBEAFE;
  border-radius:999px; padding:3px 12px; margin:2px 4px 2px 0; font-size:12px; }
.riskband{ border-radius:16px; padding:14px 18px; font-weight:700; border:1px solid; }
.rb-Critical{ background:linear-gradient(90deg,rgba(220,38,38,.35),rgba(239,68,68,.15)); border-color:#DC2626; }
.rb-High{ background:rgba(239,68,68,.12); border-color:#EF4444; }
.rb-Medium{ background:rgba(245,158,11,.12); border-color:#F59E0B; }
.rb-Low{ background:rgba(34,197,94,.12); border-color:#22C55E; }
.tl{ border-left:3px solid transparent; border-image:linear-gradient(180deg,#3B82F6,#06B6D4,#8B5CF6) 1; padding-left:16px; margin:10px 0; }
.tl-step{ background:rgba(13,25,48,.72); border:1px solid rgba(99,102,241,.28); border-radius:14px; padding:12px 16px; margin:8px 0; }
.dec-card{ border-radius:18px; padding:16px; border:1px solid rgba(99,102,241,.3); background:rgba(13,25,48,.72); text-align:center; height:100%; }
.dec-best{ border:1px solid #22C55E; box-shadow:0 0 22px rgba(34,197,94,.35); }
.dec-bad{ border:1px solid #EF4444; box-shadow:0 0 22px rgba(239,68,68,.30); }
.footer{ text-align:center; color:var(--mut); font-size:12.5px; padding:26px 10px 8px 10px; }
.stButton>button{ border-radius:12px !important; font-weight:700 !important;
  background:linear-gradient(90deg,#2563EB,#7C3AED) !important; color:#fff !important;
  border:1px solid rgba(139,92,246,.5) !important; box-shadow:0 8px 22px rgba(37,99,235,.35) !important; }
.stButton>button:hover{ filter:brightness(1.12); }
.stDownloadButton>button{ border-radius:12px !important; font-weight:700 !important; }
div[data-testid="stMetric"]{ background:rgba(13,25,48,.72); border:1px solid rgba(99,102,241,.28); border-radius:16px; padding:12px 16px; }
@media (max-width:768px){ .hero{ padding:28px 20px; } .hero-title{ font-size:34px; } .page-banner{ flex-direction:column; } .page-banner .art{ max-width:100%; } .hero-flex{ flex-direction:column; } }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------- helpers (backend UNCHANGED)
def push_history(a, user_action="Analysed"):
    ev = st.session_state.get("evidence", {})
    st.session_state.history.append({
        "time": a["timestamp"], "threat": a["threat_type"], "score": a["risk_score"],
        "level": a["risk_level"], "action": user_action, "reported": "No",
        "recommended": recommended_action(a),
        "evidence_saved": "Yes" if any(ev.values()) else "No",
        "complaint": "Yes" if st.session_state.get("complaint_text") else "No",
    })

def sample_texts():
    return {
        "Bank/UPI scam": "Dear Customer, your HDFC account will be BLOCKED today! Complete KYC urgently. Click http://hdfc-secure-verify.tk/login and share OTP. Pay Rs 99 verification fee via UPI now. Do not tell anyone.",
        "Fake job offer": "Congratulations! Selected for work-from-home job. Earn Rs 5000/day liking videos. Pay Rs 499 registration fee on http://bit.ly/job-offer-2026 and share your bank details + Aadhaar to start.",
        "Delivery scam": "Your parcel is held at customs. Pay Rs 149 redelivery fee now: http://delivery-track99.com/pay?id=8821 to release. Last chance, act immediately!",
        "Benign message": "Hi team, reminder: project meeting tomorrow at 10am. Please confirm availability. Thanks!",
    }

def goto(dest):
    if dest in NAV:
        st.session_state.nav = dest
        st.rerun()

def risk_band(a):
    lvl = a["risk_level"]
    st.markdown(f"<div class='riskband rb-{lvl}'><span class='sev sev-{lvl}'>{lvl}</span>"
                f" &nbsp; <b>{a['risk_score']}/100</b> &nbsp;|&nbsp; {a['threat_type']}"
                f" &nbsp;|&nbsp; Confidence: {a['confidence']}</div>", unsafe_allow_html=True)

# ------------------------------------------------------- visuals: local photos (assets/) with SVG fallback
import os as _os
import base64 as _b64
ASSETS_DIR = _os.path.join(_os.path.dirname(__file__), "assets")
ART_FILE = {"Dashboard": "dashboard", "Threat Analysis": "threat", "URL Analysis": "url",
            "What-If Simulator": "simulator", "Protection & Recovery": "protection",
            "Evidence": "evidence", "Complaint Generator": "complaint",
            "Complaint Tracking": "tracking", "AI Copilot": "copilot",
            "Risk History": "history", "Awareness Training": "awareness", "ML Model Lab": "ml_model_lab"}

def _asset_path(key):
    for ext, mime in (("png", "image/png"), ("jpg", "image/jpeg"),
                      ("jpeg", "image/jpeg"), ("webp", "image/webp")):
        p = _os.path.join(ASSETS_DIR, f"{key}.{ext}")
        if _os.path.exists(p):
            return p, mime
    # shared fallbacks so related pages never look empty
    for fb in ART_FALLBACK.get(key, ()):
        for ext, mime in (("png", "image/png"), ("jpg", "image/jpeg"),
                          ("jpeg", "image/jpeg"), ("webp", "image/webp")):
            p = _os.path.join(ASSETS_DIR, f"{fb}.{ext}")
            if _os.path.exists(p):
                return p, mime
    return None, None

# related pages reuse a sibling photo when their own file is absent
ART_FALLBACK = {"tracking": ("complaint",), "Complaint Tracking": ("complaint",)}

def hero_bg_css():
    """Home hero photographic background (assets/dashboard_bg.*) with dark overlay.
    Returns '' when the file is absent — hero keeps its gradient look."""
    p, mime = _asset_path("dashboard_bg")
    if not p:
        return ""
    try:
        b64 = _b64.b64encode(open(p, "rb").read()).decode()
        return (f"<style>.hero{{background:linear-gradient(135deg,rgba(5,8,22,.88),"
                f"rgba(11,18,32,.82)),url('data:{mime};base64,{b64}') center/cover !important;}}</style>")
    except Exception:
        return ""

def art(key, svg_body, caption):
    """Page visual: local assets/<key>.png|jpg|webp photo if present, else inline SVG. Never a broken link."""
    p, mime = _asset_path(key)
    if p:
        try:
            b64 = _b64.b64encode(open(p, "rb").read()).decode()
            return (f'<div class="glass" style="text-align:center;'
                    f'background:linear-gradient(135deg,rgba(37,99,235,.22),rgba(124,58,237,.22));">'
                    f'<img class="art-img" src="data:{mime};base64,{b64}" alt="{key} visual" />'
                    f'<div class="small" style="margin-top:8px">{caption}</div></div>')
        except Exception:
            pass
    if svg_body == "__HERO__":
        return hero_art()
    return _svg(svg_body, caption)

def _svg(body, caption):
    return (f'<div class="glass" style="text-align:center;'
            f'background:linear-gradient(135deg,rgba(37,99,235,.22),rgba(124,58,237,.22));">'
            f'<svg viewBox="0 0 320 220" width="100%" style="max-width:300px">{body}</svg>'
            f'<div class="small">{caption}</div></div>')

def hero_art():
    return _svg("""
      <defs><linearGradient id="g1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#3B82F6"/><stop offset=".5" stop-color="#06B6D4"/><stop offset="1" stop-color="#8B5CF6"/>
      </linearGradient></defs>
      <circle cx="160" cy="105" r="90" fill="none" stroke="url(#g1)" stroke-width="2" opacity=".5"/>
      <circle cx="160" cy="105" r="66" fill="none" stroke="url(#g1)" stroke-width="1.5" opacity=".7"/>
      <g fill="#22D3EE"><circle cx="160" cy="15" r="4"/><circle cx="160" cy="195" r="4"/>
      <circle cx="70" cy="105" r="4"/><circle cx="250" cy="105" r="4"/>
      <circle cx="98" cy="43" r="3"/><circle cx="222" cy="43" r="3"/></g>
      <path d="M160 48 L212 69 V112 C212 147 189 171 160 183 C131 171 108 147 108 112 V69 Z"
        fill="rgba(37,99,235,.25)" stroke="url(#g1)" stroke-width="3"/>
      <path d="M140 107 L156 123 L183 90" fill="none" stroke="#4ADE80" stroke-width="7"
        stroke-linecap="round" stroke-linejoin="round"/>
      <text x="160" y="212" text-anchor="middle" fill="#94A3B8" font-size="11">AI DECISION SHIELD</text>""",
      "Simulated visualisation — outcomes in-app are plausible scenarios, not certainties.")

VISUALS = {
    "Dashboard": ("AI threat-intelligence overview — live risk posture at a glance.",
        """<circle cx="160" cy="100" r="80" fill="none" stroke="#3B82F6" stroke-width="2" opacity=".6"/>
        <circle cx="160" cy="100" r="55" fill="rgba(37,99,235,.25)" stroke="#06B6D4" stroke-width="2"/>
        <path d="M160 62 L200 78 V108 C200 134 182 152 160 161 C138 152 120 134 120 108 V78 Z"
        fill="rgba(124,58,237,.3)" stroke="#8B5CF6" stroke-width="2.5"/>
        <path d="M145 103 L157 115 L178 90" fill="none" stroke="#4ADE80" stroke-width="6" stroke-linecap="round"/>
        <g stroke="#22D3EE" opacity=".6"><line x1="60" y1="60" x2="105" y2="80"/><line x1="260" y1="60" x2="215" y2="80"/>
        <line x1="60" y1="150" x2="105" y2="130"/><line x1="260" y1="150" x2="215" y2="130"/></g>
        <g fill="#22D3EE"><circle cx="60" cy="60" r="5"/><circle cx="260" cy="60" r="5"/>
        <circle cx="60" cy="150" r="5"/><circle cx="260" cy="150" r="5"/></g>"""),
    "Threat Analysis": ("Phishing & message-threat detection console.",
        """<rect x="70" y="55" width="180" height="110" rx="12" fill="rgba(37,99,235,.2)" stroke="#3B82F6" stroke-width="2"/>
        <rect x="85" y="72" width="150" height="12" rx="6" fill="#EF4444" opacity=".8"/>
        <rect x="85" y="92" width="110" height="10" rx="5" fill="#94A3B8" opacity=".7"/>
        <rect x="85" y="110" width="130" height="10" rx="5" fill="#F59E0B" opacity=".8"/>
        <rect x="85" y="128" width="90" height="10" rx="5" fill="#22D3EE" opacity=".8"/>
        <circle cx="252" cy="52" r="20" fill="rgba(239,68,68,.25)" stroke="#EF4444" stroke-width="2"/>
        <text x="252" y="60" text-anchor="middle" font-size="22">⚠</text>"""),
    "URL Analysis": ("Web-link & domain security inspection.",
        """<circle cx="160" cy="105" r="60" fill="none" stroke="#06B6D4" stroke-width="2"/>
        <ellipse cx="160" cy="105" rx="60" ry="22" fill="none" stroke="#3B82F6" stroke-width="1.5"/>
        <line x1="160" y1="45" x2="160" y2="165" stroke="#3B82F6" stroke-width="1.5"/>
        <rect x="105" y="150" width="150" height="26" rx="13" fill="rgba(239,68,68,.2)" stroke="#EF4444" stroke-width="2"/>
        <text x="180" y="168" text-anchor="middle" fill="#FCA5A5" font-size="12">http://fake-login.tk</text>"""),
    "What-If Simulator": ("Counterfactual decision tree — compare five futures.",
        """<circle cx="160" cy="40" r="16" fill="rgba(139,92,246,.4)" stroke="#8B5CF6" stroke-width="2"/>
        <line x1="160" y1="56" x2="80" y2="110" stroke="#22D3EE" stroke-width="2"/>
        <line x1="160" y1="56" x2="160" y2="110" stroke="#3B82F6" stroke-width="2"/>
        <line x1="160" y1="56" x2="240" y2="110" stroke="#EF4444" stroke-width="2"/>
        <circle cx="80" cy="125" r="15" fill="rgba(34,197,94,.3)" stroke="#22C55E" stroke-width="2"/>
        <circle cx="160" cy="125" r="15" fill="rgba(59,130,246,.3)" stroke="#3B82F6" stroke-width="2"/>
        <circle cx="240" cy="125" r="15" fill="rgba(239,68,68,.3)" stroke="#EF4444" stroke-width="2"/>
        <line x1="80" y1="140" x2="80" y2="175" stroke="#22C55E" stroke-width="1.5"/>
        <line x1="240" y1="140" x2="240" y2="175" stroke="#EF4444" stroke-width="1.5"/>"""),
    "Protection & Recovery": ("Defence shield & incident recovery timeline.",
        """<path d="M160 35 L220 60 V115 C220 155 192 180 160 192 C128 180 100 155 100 115 V60 Z"
        fill="rgba(34,197,94,.18)" stroke="#22C55E" stroke-width="3"/>
        <path d="M140 108 L156 124 L184 92" fill="none" stroke="#4ADE80" stroke-width="7" stroke-linecap="round"/>
        <g fill="#22D3EE"><circle cx="70" cy="170" r="5"/><circle cx="120" cy="185" r="5"/><circle cx="250" cy="170" r="5"/></g>"""),
    "Evidence": ("Digital forensics vault — sealed evidence chain.",
        """<rect x="90" y="70" width="140" height="100" rx="10" fill="rgba(37,99,235,.2)" stroke="#8B5CF6" stroke-width="2.5"/>
        <rect x="130" y="60" width="60" height="20" rx="8" fill="rgba(139,92,246,.4)" stroke="#8B5CF6" stroke-width="2"/>
        <line x1="110" y1="100" x2="210" y2="100" stroke="#22D3EE" stroke-width="2"/>
        <line x1="110" y1="120" x2="190" y2="120" stroke="#94A3B8" stroke-width="2"/>
        <line x1="110" y1="140" x2="200" y2="140" stroke="#94A3B8" stroke-width="2"/>"""),
    "Complaint Generator": ("Structured cyber-incident report drafting.",
        """<rect x="100" y="40" width="120" height="140" rx="8" fill="rgba(13,25,48,.9)" stroke="#3B82F6" stroke-width="2"/>
        <rect x="115" y="58" width="90" height="10" rx="5" fill="#60A5FA"/>
        <rect x="115" y="78" width="90" height="7" rx="3.5" fill="#475569"/>
        <rect x="115" y="94" width="70" height="7" rx="3.5" fill="#475569"/>
        <rect x="115" y="110" width="80" height="7" rx="3.5" fill="#F59E0B"/>
        <rect x="115" y="126" width="60" height="7" rx="3.5" fill="#475569"/>
        <circle cx="232" cy="150" r="22" fill="rgba(34,197,94,.25)" stroke="#22C55E" stroke-width="2"/>
        <path d="M223 150 L230 157 L242 143" fill="none" stroke="#4ADE80" stroke-width="4" stroke-linecap="round"/>"""),
    "Complaint Tracking": ("Case timeline & status tracking workflow.",
        """<line x1="60" y1="105" x2="260" y2="105" stroke="#3B82F6" stroke-width="3"/>
        <circle cx="90" cy="105" r="14" fill="rgba(34,197,94,.35)" stroke="#22C55E" stroke-width="2"/>
        <circle cx="160" cy="105" r="14" fill="rgba(245,158,11,.35)" stroke="#F59E0B" stroke-width="2"/>
        <circle cx="230" cy="105" r="14" fill="rgba(59,130,246,.35)" stroke="#3B82F6" stroke-width="2"/>
        <text x="90" y="145" text-anchor="middle" fill="#94A3B8" font-size="11">Filed</text>
        <text x="160" y="145" text-anchor="middle" fill="#94A3B8" font-size="11">Review</text>
        <text x="230" y="145" text-anchor="middle" fill="#94A3B8" font-size="11">Closed</text>"""),
    "AI Copilot": ("Conversational cyber-defence assistant.",
        """<rect x="105" y="55" width="110" height="85" rx="24" fill="rgba(124,58,237,.3)" stroke="#8B5CF6" stroke-width="2.5"/>
        <circle cx="140" cy="95" r="8" fill="#22D3EE"/><circle cx="180" cy="95" r="8" fill="#22D3EE"/>
        <rect x="140" y="118" width="40" height="8" rx="4" fill="#22D3EE" opacity=".7"/>
        <line x1="160" y1="140" x2="160" y2="165" stroke="#8B5CF6" stroke-width="3"/>
        <rect x="120" y="165" width="80" height="14" rx="7" fill="rgba(139,92,246,.3)" stroke="#8B5CF6"/>"""),
    "Risk History": ("Risk analytics over time — trends & distribution.",
        """<line x1="60" y1="160" x2="260" y2="160" stroke="#475569" stroke-width="2"/>
        <line x1="60" y1="160" x2="60" y2="50" stroke="#475569" stroke-width="2"/>
        <polyline points="70,140 110,120 150,128 190,85 230,95" fill="none" stroke="#22D3EE" stroke-width="3"/>
        <g fill="#8B5CF6"><circle cx="110" cy="120" r="5"/><circle cx="190" cy="85" r="5"/></g>
        <rect x="215" y="45" width="30" height="60" fill="rgba(239,68,68,.4)"/>
        <rect x="180" y="65" width="30" height="40" fill="rgba(245,158,11,.4)"/>"""),
    "Awareness Training": ("Security learning & safer-decision practice.",
        """<path d="M60 90 L160 50 L260 90 L160 130 Z" fill="rgba(37,99,235,.3)" stroke="#3B82F6" stroke-width="2"/>
        <rect x="130" y="130" width="60" height="35" fill="rgba(124,58,237,.3)" stroke="#8B5CF6" stroke-width="2"/>
        <circle cx="235" cy="140" r="18" fill="rgba(34,197,94,.25)" stroke="#22C55E" stroke-width="2"/>
        <path d="M227 140 L233 146 L244 134" fill="none" stroke="#4ADE80" stroke-width="3.5" stroke-linecap="round"/>"""),
    "ML Model Lab": ("Model Intelligence",
        """<circle cx="160" cy="110" r="40" fill="rgba(6, 182, 212, 0.2)" stroke="#06B6D4" stroke-width="2"/>
        <line x1="160" y1="70" x2="160" y2="30" stroke="#06B6D4" stroke-width="2"/>
        <line x1="160" y1="150" x2="160" y2="190" stroke="#06B6D4" stroke-width="2"/>
        <line x1="120" y1="110" x2="80" y2="110" stroke="#06B6D4" stroke-width="2"/>
        <line x1="200" y1="110" x2="240" y2="110" stroke="#06B6D4" stroke-width="2"/>
        <circle cx="160" cy="110" r="10" fill="#3B82F6"/>"""),
}

def banner(title, subtitle, nav_key, badge=""):
    # single-line HTML (no newlines): indented/blank lines inside st.markdown
    # can be parsed as code blocks and shown as literal code text
    cap, body = VISUALS.get(nav_key, ("CyberTwin", "Cybersecurity intelligence and decision support."))
    parts = [f'<div class="page-banner"><div class="art">{art(ART_FILE.get(nav_key, "unknown"), body, cap)}</div>',
             f'<div class="txt"><h2 style="margin:0">{title}</h2>',
             f'<div class="small">{subtitle}</div>']
    if badge:
        parts.append(f"<div style='margin-top:8px'><span class='chip'>{badge}</span></div>")
    parts.append('</div></div>')
    st.markdown(''.join(parts), unsafe_allow_html=True)

# ------------------------------------------------------------------ LEFT SIDEBAR (all 11 items)
with st.sidebar:
    st.markdown("<div style='font-size:26px'>🛡️</div><div class='side-brand'>CyberTwin</div>"
                "<div class='small'>AI-Powered Counterfactual<br>Cyber-Risk Simulator</div>",
                unsafe_allow_html=True)
    st.markdown("")
    sel = st.radio("NAVIGATE", NAV, index=NAV.index(st.session_state.nav),
                   format_func=lambda n: f"{ICON[n]}  {n}")
    st.session_state.nav = sel
    st.divider()
    _a = st.session_state.analysis
    if _a:
        st.markdown("**📌 Current case**")
        st.markdown(f"<span class='chip'>{_a['threat_type']}</span>"
                    f"<span class='chip'>{_a['risk_level']} {_a['risk_score']}/100</span>",
                    unsafe_allow_html=True)
    else:
        st.caption("No case analysed yet. Go to Threat Analysis.")
    st.divider()
    st.caption("⚠️ Risk assessments support decisions, not certainty. Never enter real passwords/OTPs.")

page = st.session_state.nav

# ================================================================ DASHBOARD
if page == "Dashboard":
    _bg = hero_bg_css()
    if _bg:
        st.markdown(_bg, unsafe_allow_html=True)
    # Single self-contained hero block (Streamlit closes divs per-block, so no
    # Streamlit columns may live inside the hero div — flex layout instead).
    st.markdown(f"""<div class="hero"><div class="hero-flex">
      <div class="hero-text">
        <span class='hero-kicker'>AI CYBERSECURITY • DECISION INTELLIGENCE</span>
        <div class='hero-title'>CYBER<span class='grad-text'>TWIN</span></div>
        <h3 style="margin:4px 0">AI-Powered Counterfactual Cyber-Risk Simulator</h3>
        <div class='hero-tag'>"Don't just detect the threat. Understand what happens next."</div>
        <div class='hero-desc'>CyberTwin analyses suspicious messages, links, QR codes and incidents,
        explains why they are risky, simulates what each decision could lead to, and guides you to
        protection, evidence, reporting and learning.</div>
        <div class='small' style="margin-top:8px">"See the consequences before you make the decision."</div>
      </div>
      <div class="hero-art">{art("dashboard", "__HERO__", "CyberTwin — threat intelligence at a glance")}</div>
      </div></div>""", unsafe_allow_html=True)
    hb1, hb2 = st.columns(2)
    with hb1:
        if st.button("🚀 Analyze a Threat", type="primary", use_container_width=True):
            goto("Threat Analysis")
    with hb2:
        if st.button("🔀 Explore CyberTwin", use_container_width=True):
            goto("What-If Simulator")

    st.markdown("### Cyber safety is more than detection.")
    st.markdown("Most security tools simply say **“This looks suspicious.”** CyberTwin goes further: **“What could happen if you continue?”**")
    flow = [
        ("01", "🔍", "Detect", "Suspicious messages, URLs, QR codes, incidents."),
        ("02", "💡", "Explain", "Why the content is risky, in plain language."),
        ("03", "🔀", "Simulate", "Consequences of Proceed / Ignore / Verify / Report / Block."),
        ("04", "🛡️", "Protect", "Safer action + incident recovery guidance."),
        ("05", "📄", "Report", "Evidence pack + editable complaint draft."),
        ("06", "📌", "Track", "Personal reference & follow-up tracker."),
        ("07", "🎓", "Learn", "Turn incidents into awareness practice."),
    ]
    fc = st.columns(7)
    for col, (n, ic, name, desc) in zip(fc, flow):
        with col:
            st.markdown(f"<div class='glass flow-card'><div class='flow-num'>{n}</div>"
                        f"<div class='flow-ic'>{ic}</div><b>{name}</b><br><span class='small'>{desc}</span></div>",
                        unsafe_allow_html=True)
    st.markdown("<div class='step-line'></div>", unsafe_allow_html=True)

    st.markdown("## WHY CYBERTWIN?")
    feats = [
        ("🧠", "AI-Powered Threat Analysis", "Message, URL, QR and screenshot signals with explainable risk."),
        ("🔀", "Counterfactual Simulation", "See plausible outcomes before taking an action."),
        ("💡", "Explainable Risk", "Highlighted triggers, entities, verdicts — never a black box."),
        ("🛠️", "Incident Recovery", "Step-by-step protection for six incident stages."),
        ("🗂️", "Evidence & Reporting", "Vault + complaint draft + full evidence pack download."),
        ("🎓", "Adaptive Awareness", "Scenario training mapped to real threat patterns."),
    ]
    fcols = st.columns(3)
    for i, (ic, t, d) in enumerate(feats):
        with fcols[i % 3]:
            st.markdown(f"<div class='glass'><div class='feat-ic'>{ic}</div><b>{t}</b><br><span class='small'>{d}</span></div>",
                        unsafe_allow_html=True)

    st.markdown("## HOW CYBERTWIN WORKS")
    for i, s in enumerate(["User Input (message / URL / screenshot / QR)",
                           "Threat Analysis (classification + signals)",
                           "Risk Assessment (score + severity + confidence)",
                           "Counterfactual Simulation (5 decisions + replay)",
                           "Protection (incident-specific recovery)",
                           "Evidence / Report (vault + complaint + tracking)",
                           "Learning (awareness scenarios)"], 1):
        st.markdown(f"<div class='tl-step'><b>{i}.</b> {s}</div>", unsafe_allow_html=True)

    st.markdown("## 📊 Live Dashboard")
    h = st.session_state.history
    m1, m2, m3, m4, m5 = st.columns(5)
    total = len(h)
    hc = sum(1 for x in h if x["level"] in ("High", "Critical")) if total else 0
    m1.metric("Threats Analyzed", total)
    m2.metric("High/Critical Risks", hc)
    m3.metric("Tracked References", len(st.session_state.tracking))
    m4.metric("Evidence Saved", "Yes" if any(st.session_state.evidence.values()) else "No")
    m5.metric("Marked Reported", sum(1 for x in h if x.get("reported") == "Yes") if total else 0)
    d1, d2 = st.columns([2, 1])
    with d1:
        st.markdown("#### Threat statistics (your session data)")
        if h:
            df = pd.DataFrame(h)
            st.plotly_chart(px.bar(df["threat"].value_counts().reset_index(),
                                   x="threat", y="count", title="Threat Categories",
                                   color="threat", template="plotly_dark"), use_container_width=True)
            st.plotly_chart(px.pie(df, names="level", title="Risk Distribution",
                                   color="level",
                                   color_discrete_map={"Critical": "#DC2626", "High": "#EF4444",
                                                       "Medium": "#F59E0B", "Low": "#22C55E"},
                                   template="plotly_dark"), use_container_width=True)
        else:
            st.info("No scans yet — try a demo case to light up the dashboard.")
            samples = sample_texts()
            choice = st.selectbox("Load a demo case", list(samples.keys()))
            if st.button("▶ Load into Threat Analysis"):
                st.session_state["demo_text"] = samples[choice]
                goto("Threat Analysis")
    with d2:
        st.markdown("#### Recent incidents")
        if h:
            for x in reversed(h[-5:]):
                st.markdown(f"<div class='glass'><b>{x['threat']}</b><br><span class='small'>{x['time']}</span><br>"
                            f"<span class='sev sev-{x['level']}'>{x['level']} {x['score']}</span></div>",
                            unsafe_allow_html=True)
        else:
            st.caption("History will appear here after analyses.")
    st.markdown("<div class='glass' style='text-align:center'><h3>Ready to analyze your next cyber threat?</h3>",
                unsafe_allow_html=True)
    if st.button("Start Analysis →", type="primary"):
        goto("Threat Analysis")
    st.markdown("</div>", unsafe_allow_html=True)

# ========================================================= THREAT ANALYSIS
elif page == "Threat Analysis":
    banner("🔍 Threat Intelligence Center",
           "Message / email / SMS / WhatsApp + screenshot OCR + QR decode — one engine, full explainability.",
           "Threat Analysis")
    samples = sample_texts()
    with st.expander("⚡ Try a demo case", expanded=False):
        dc = st.selectbox("Demo", list(samples.keys()))
        if st.button("Fill demo text"):
            st.session_state["demo_text"] = samples[dc]
            st.rerun()
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown("**🖥️ Smart Input Analysis** <span class='small'>— paste text, a URL, or upload an image. CyberTwin will automatically detect and route it.</span>", unsafe_allow_html=True)
    
    smart_text = st.text_area("Paste a message, email, URL, or incident description", value=st.session_state.pop("demo_text", ""), height=120, placeholder="Paste suspicious content here…")
    smart_image = st.file_uploader("OR Upload an Image (Screenshot / QR Code)", type=["png", "jpg", "jpeg", "webp"], key="smart_up")
    
    c3a, c3b = st.columns(2)
    with c3a:
        sender = st.text_input("Sender email / phone / profile (optional)", placeholder="e.g. +91-98XXXXXX or support@hdfc-secure.tk")
        payment = st.text_input("Payment / scam request details (optional)", placeholder="e.g. UPI collect request of ₹4,999")
    with c3b:
        social = st.text_input("Social media / profile info (optional)", placeholder="e.g. Instagram profile, 12 followers, joined this month")
        incident = st.text_area("Additional context (optional)", height=68, placeholder="What happened so far?")
        
    if st.button("🔎 Analyze Threat", type="primary", use_container_width=True):
        if not (smart_text or smart_image or payment or social or incident):
            st.warning("Please provide some input (text, URL, or image) to analyze.")
        else:
            with st.spinner("Analyzing input and routing to ML models…"):
                from src.input_detection.input_classifier import detect_input_type
                
                pil_img = None
                if smart_image:
                    try:
                        from PIL import Image as _Img
                        pil_img = _Img.open(smart_image).convert("RGB")
                        st.image(pil_img, caption="Uploaded Image", use_container_width=True)
                    except Exception as e:
                        st.error(f"Image load failed: {e}")
                
                # Detect input type
                detection = detect_input_type(smart_text, pil_img)
                
                # Show detection summary UI
                st.markdown("### 🤖 Automatic Input Detection")
                c_d1, c_d2, c_d3 = st.columns(3)
                c_d1.metric("Detected Type", detection["primary_type"])
                c_d2.metric("Detection Method", detection["detection_method"])
                c_d3.metric("Components Used", ", ".join(detection["components"]) if detection["components"] else "None")
                
                if detection["routing"]:
                    st.info(f"**Analysis Pipeline:** Input → {' → '.join(detection['routing'])} → Risk Engine")
                    
                if detection.get("extracted_text") and smart_image:
                    with st.expander("OCR extracted text (added to analysis)"):
                        st.write(detection["extracted_text"])
                if detection.get("extracted_urls") and smart_image:
                    with st.expander("Extracted URL(s)"):
                        for u in detection["extracted_urls"]:
                            st.write(u)
                
                # Extract combined inputs for Threat Engine
                message = detection["extracted_text"]
                url_input = " ".join(detection["extracted_urls"])
                
                # If there's extra manual context, append it
                cnn_context = ""
                if detection.get("cnn_predictions"):
                    cnn_context = f"[Image Type: {detection['image_type']} | CNN Objects: {', '.join(detection['cnn_predictions'])}]"
                    with st.expander("CNN Image Classification"):
                        st.write(f"**Image Type:** {detection['image_type']}")
                        st.write(f"**Detected Objects:** {', '.join(detection['cnn_predictions'])}")
                    
                if payment or social or incident:
                    message += "\n" + " ".join(filter(None, [payment, social, incident]))
                
                res = analyze_threat(message=message, url_input=url_input, sender=sender,
                                     channel="Auto-detected", extra_context=cnn_context)
                st.session_state.analysis = res
                st.session_state.sim = simulate_action(res)
                st.session_state.evidence = {
                    "sender": sender, "url": "; ".join(res.get("urls", [])),
                    "description": message or res.get("raw_text", ""),
                    "datetime": res.get("timestamp", ""),
                    "transaction": payment, "upi": payment, "social": social,
                    "evidence_desc": incident,
                    "screenshot_note": f"Type: {detection['primary_type']}" if smart_image else "",
                    "qr_note": "",
                    "qr_data": url_input if "QR" in detection["primary_type"] else "",
                }
                push_history(res)
            st.success("Analysis complete — results below feed Simulator, Copilot, Evidence & Complaint pages.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='glass'>ℹ️ <b>Privacy</b> <span class='small'>— never paste real passwords or OTPs. "
                "Sensitive items are masked in reports.</span><br>🧠 <span class='small'>Text normalisation + TF-IDF prototype "
                "similarity + structured URL / social-engineering signals + weighted risk layer.</span></div>",
                unsafe_allow_html=True)

    a = st.session_state.analysis
    if a:
        st.markdown("### Risk Verdict")
        risk_band(a)
        for c in a["chips"]:
            st.markdown(f"<span class='chip'>{c}</span>", unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("🎯 Threat Category", a["threat_type"])
        k2.metric("📊 Risk Score", f"{a['risk_score']}/100")
        k3.metric("📶 Severity", a["risk_level"])
        k4.metric("🎲 Confidence", a["confidence"])
        st.markdown("#### 💡 Threat Explanation")
        st.markdown(f"<div class='glass'><b>Attacker objective (assessed):</b> {a['attacker_objective']}<br>"
                    f"<b>Targeted:</b> {a['targeted']}<br><b>Safe action:</b> {a['safe_action']}</div>",
                    unsafe_allow_html=True)
                    
        st.markdown("#### 🧠 Psychology Attack Chain")
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        for idx, step in enumerate(a.get("psychology_chain", [])):
            st.markdown(f"**{step}**")
            if idx < len(a.get("psychology_chain", [])) - 1:
                st.markdown("⬇️")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("#### ✅ Recommended Defensive Actions")
        for rec in a.get("recommendations", []):
            st.info(rec)

        with st.expander("Why this is risky", expanded=True):
            for w in a["why_risky"]:
                st.markdown(f"- {w}")
        r1, r2 = st.columns(2)
        with r1:
            st.markdown("#### 🚩 Suspicious Indicators")
            st.markdown("<div class='glass'>" + "<br>".join(f"• {i}" for i in a["indicators"] or ["No strong indicators."]) + "</div>",
                        unsafe_allow_html=True)
        with r2:
            st.markdown("#### 🧠 Social-Engineering Signals")
            exp_map = a.get("se_explanations", {}) or {}
            for kk, vv in a["se_signals"].items():
                st.markdown(f"<div class='tl-step'>{'🔴 <b>YES</b>' if vv else '🟢 not detected'} — <b>{kk.replace('_', ' ').title()}</b>"
                            f"<br><span class='small'>{exp_map.get(kk, '')}</span></div>", unsafe_allow_html=True)
        st.markdown("#### 🖍️ Suspicious Text — what drove the score")
        st.markdown(a.get("highlight_html", ""), unsafe_allow_html=True)
        st.markdown("#### 🧷 Extracted Entities")
        ent = a.get("entities", {}) or {}
        ec = st.columns(4)
        ec[0].markdown(f"<div class='glass'><b>📧 Emails</b><br>{', '.join(ent.get('emails', [])) or '—'}</div>", unsafe_allow_html=True)
        ec[1].markdown(f"<div class='glass'><b>📞 Phones</b><br>{', '.join(ent.get('phones', [])) or '—'}</div>", unsafe_allow_html=True)
        ec[2].markdown(f"<div class='glass'><b>💸 Amounts / UPI</b><br>{', '.join((ent.get('amounts', []) + ent.get('upi_ids', []))) or '—'}</div>", unsafe_allow_html=True)
        ec[3].markdown(f"<div class='glass'><b>🕒 Dates / 👤 Social</b><br>{', '.join((ent.get('dates_times', []) + ent.get('social_hints', []))) or '—'}</div>", unsafe_allow_html=True)
        st.markdown("#### 🔗 URL Verdicts")
        if a["url_results"]:
            for rr, vv in zip(a["url_results"], a.get("url_verdicts", [])):
                with st.expander(f"🔗 {rr['url'][:70]} (+{rr['added_risk']})"):
                    for ind in rr["indicators"]:
                        st.markdown(f"- {ind}")
                    if vv:
                        st.info(f"Verdict: {vv}")
        else:
            st.caption("No URLs detected in the input.")
        with st.expander("Advanced: semantic similarity + category scores"):
            st.json({"semantic": a["semantic"], "category_scores": a["category_scores"]})
        n1, n2, n3 = st.columns(3)
        if n1.button("🔀 Open in Simulator →"):
            goto("What-If Simulator")
        if n2.button("🗂️ Send to Evidence →"):
            st.session_state.evidence = {"sender": a["sender"], "url": "; ".join(a["urls"]),
                                         "description": a.get("message_only") or a["raw_text"],
                                         "datetime": a["timestamp"],
                                         "screenshot_note": st.session_state.get("screenshot_note", ""),
                                         "qr_note": st.session_state.get("qr_note", ""),
                                         "qr_data": st.session_state.get("qr_data", "")}
            goto("Evidence")
        if n3.button("🤖 Ask Copilot →"):
            goto("AI Copilot")

# ============================================================== URL ANALYSIS
elif page == "URL Analysis":
    banner("🔗 URL Threat Analyzer",
           "HTTPS status, domain signals, look-alike / shortened-URL checks, keyword & structure review — indicators, never proof from one flag.",
           "URL Analysis")
    u = st.text_input("Paste URL to inspect", placeholder="http://example-secure-login.tk/verify")
    if st.button("Inspect URL", type="primary") and u:
        r = analyze_single_url(u)
        st.markdown(f"<div class='glass'><b>Host:</b> <code>{r.get('host', '-')}</code> &nbsp;|&nbsp; "
                    f"<b>Added risk:</b> +{r['added_risk']}</div>", unsafe_allow_html=True)
        for ind in r["indicators"]:
            st.markdown(f"- {ind}")
        st.info(f"Verdict: {url_verdict(r)}")
    a = st.session_state.analysis
    if a and a.get("url_results"):
        st.divider()
        st.markdown("### URLs from current case")
        for r, v in zip(a["url_results"], a.get("url_verdicts", [])):
            with st.expander(f"🔗 {r['url'][:80]} (+{r['added_risk']})"):
                for ind in r["indicators"]:
                    st.markdown(f"- {ind}")
                if v:
                    st.info(f"Verdict: {v}")

# ========================================================= WHAT-IF SIMULATOR
elif page == "What-If Simulator":
    banner("🔀 Counterfactual Decision Lab",
           "“What happens if you continue?” — plausible simulations per threat type, not certainties.",
           "What-If Simulator")
    a = st.session_state.analysis
    if not a:
        st.warning("Run a Threat Analysis first to use the What-If Simulator.")
        st.stop()
    sim = st.session_state.sim or simulate_action(a)
    st.session_state.sim = sim
    risk_band(a)
    st.success(f"✅ Recommended: **{recommended_action(a)}**")
    st.markdown("### Choose a decision")
    order = ["Proceed", "Ignore", "Verify", "Report", "Block"]
    dc = st.columns(5)
    for col, act in zip(dc, order):
        with col:
            d0 = sim[act]
            best = act in ("Verify", "Report", "Block")
            bad = act == "Proceed"
            st.markdown(f"<div class='dec-card {'dec-best' if best else ''} {'dec-bad' if bad else ''}'>"
                        f"<b>{act}</b><br><span class='sev sev-{'LOW' if d0['residual_risk'] <= 12 else ('MEDIUM' if d0['residual_risk'] <= 30 else ('HIGH' if d0['residual_risk'] <= 70 else 'CRITICAL'))}'>~{d0['residual_risk']}</span>"
                        f"<br><span class='small'>{d0['verdict']}</span><br><span class='small'>{d0['consequence'][:90]}…</span></div>",
                        unsafe_allow_html=True)
            if st.button(f"Select {act}", key=f"sel_{act}", use_container_width=True,
                         type="primary" if st.session_state.get("decision") == act else "secondary"):
                st.session_state.decision = act
                st.rerun()
    choice = st.session_state.get("decision", "Verify")
    d = sim[choice]
    st.markdown(f"### ⚡ If you **{choice}** → {d['verdict']} (residual ≈ {d['residual_risk']}/100)")
    st.markdown("<div class='glass'><b>ATTACK PATH</b></div>", unsafe_allow_html=True)
    for i, step in enumerate(d["chain"]):
        st.markdown(f"<div class='tl'><div class='tl-step'><b>Step {i + 1}.</b> {step}</div></div>", unsafe_allow_html=True)
    st.markdown(f"**Consequence:** {d['consequence']}  \n**Impact:** {d['impact']}")
    st.markdown("### 📊 Risk comparison")
    comp = pd.DataFrame([{"Action": k, "Residual risk": v["residual_risk"]} for k, v in sim.items()])
    st.plotly_chart(px.bar(comp, x="Action", y="Residual risk", color="Action", template="plotly_dark",
                            color_discrete_map={"Proceed": "#EF4444", "Ignore": "#F59E0B", "Verify": "#22C55E",
                                                "Report": "#3B82F6", "Block": "#8B5CF6"}),
                    use_container_width=True)
    with st.expander("All paths detail"):
        for k, v in sim.items():
            st.markdown(f"**{k}** ({v['verdict']}, ~{v['residual_risk']}): " + " → ".join(v["chain"]))
    if st.button("📌 Record my decision in history"):
        push_history(a, user_action=choice)
        st.success(f"Recorded '{choice}' in Risk History.")
    st.markdown("### 🕰️ Decision Replay — “What if you had…”")
    scen = st.selectbox("Replay scenario", [f"If you had {s}…" for s in REPLAY_SCENARIOS])
    rp = decision_replay(a, scen.replace("If you had ", "").replace("…", ""))
    for i, step in enumerate(rp["chain"]):
        st.markdown(f"<div class='tl'><div class='tl-step'><b>Step {i + 1}.</b> {step}</div></div>", unsafe_allow_html=True)
    st.markdown(f"**Consequence:** {rp['consequence']}  \n**Impact:** {rp['impact']}  \n**Safer alternative:** {rp['safer_alternative']}")

# ==================================================== PROTECTION & RECOVERY
elif page == "Protection & Recovery":
    banner("🛡️ Protection & Recovery Center",
           "Incident-specific next steps for six stages. We never ask for real passwords/OTPs.",
           "Protection & Recovery", badge=f"Stage: {st.session_state.get('incident_stage', '')}")
    stage = st.selectbox("What already happened?", ORDER,
                         index=ORDER.index(st.session_state.get("incident_stage", ORDER[0])))
    st.session_state.incident_stage = stage
    plan = get_plan(stage)
    st.markdown(f"<div class='glass' style='border-left:5px solid {'#DC2626' if 'Critical' in plan['urgency'] else ('#F59E0B' if 'High' in plan['urgency'] or 'Medium' in plan['urgency'] else '#22C55E')}'>"
                f"<b>Incident status:</b> {stage}<br><b>Urgency:</b> {plan['urgency']}</div>", unsafe_allow_html=True)
    st.markdown("### Recovery timeline")
    for i, s in enumerate(plan["steps"], 1):
        done = st.checkbox(f"{i:02d} — {s}", key=f"prot_{stage}_{i}")
        st.markdown(f"<div class='tl-step'>{'✅' if done else f'<b>{i:02d}</b>'} {s}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("🗂️ Collect evidence →"):
        goto("Evidence")
    if c2.button("🤖 Ask Copilot about recovery →"):
        goto("AI Copilot")

# ================================================================= EVIDENCE
elif page == "Evidence":
    banner("🗂️ Digital Evidence Vault",
           "Auto-extracted contacts + messages + media, masked and ready for reporting.",
           "Evidence")
    e = st.session_state.evidence
    a = st.session_state.analysis
    ent0 = (a.get("entities", {}) or {}) if a else {}
    vault = [("👤 Sender", e.get("sender", "")), ("📞 Phone", (ent0.get("phones", [""])[0] if ent0.get("phones") else "")),
             ("📧 Email", (ent0.get("emails", [""])[0] if ent0.get("emails") else "")),
             ("🔗 URL", e.get("url", "")), ("💬 Message", (e.get("description", "") or "")[:120]),
             ("🕒 Date/Time", e.get("datetime", "")), ("💳 Transaction", e.get("transaction", "")),
             ("💸 UPI", e.get("upi", "")), ("👥 Social", e.get("social", "")),
             ("📷 Screenshot", e.get("screenshot_note", "") or st.session_state.get("screenshot_note", "")),
             ("◧ QR", e.get("qr_note", "") or st.session_state.get("qr_note", ""))]
    vc = st.columns(4)
    for i, (t, v) in enumerate(vault):
        with vc[i % 4]:
            st.markdown(f"<div class='glass'><b>{t}</b><br><span class='small'>{v or '—'}</span></div>", unsafe_allow_html=True)
    with st.form("ev"):
        sender = st.text_input("Sender name", value=e.get("sender", a["sender"] if a else ""))
        phone = st.text_input("Phone", value=(ent0.get("phones", [""])[0] if ent0.get("phones") else e.get("phone", "")))
        email = st.text_input("Email", value=(ent0.get("emails", [""])[0] if ent0.get("emails") else e.get("email", "")))
        url = st.text_input("URL", value=e.get("url", "; ".join(a["urls"]) if a else ""))
        msg = st.text_area("Message", value=e.get("description", a["raw_text"] if a else ""), height=120)
        dt = st.text_input("Date / time of incident", value=e.get("datetime", a["timestamp"] if a else datetime.now().strftime("%Y-%m-%d %H:%M")))
        txn = st.text_input("Transaction details (ID, amount)", value=e.get("transaction", ""))
        upi = st.text_input("UPI / payment information", value=e.get("upi", ""))
        social = st.text_input("Social profile", value=e.get("social", ""))
        edesc = st.text_area("Screenshot / evidence description", value=e.get("evidence_desc", ""), height=80)
        shot_note = st.text_input("Screenshot note", value=e.get("screenshot_note", st.session_state.get("screenshot_note", "")))
        qr_note = st.text_input("QR information", value=e.get("qr_note", st.session_state.get("qr_note", "")))
        ok = st.form_submit_button("💾 Save evidence", type="primary")
        if ok:
            from incident_engine import mask_value
            st.session_state.evidence = {"sender": sender, "phone": phone, "email": email, "url": url,
                                         "description": msg, "datetime": dt,
                                         "transaction": mask_value(txn, 3) if txn else "",
                                         "upi": mask_value(upi, 2) if upi else "",
                                         "social": social, "evidence_desc": edesc,
                                         "screenshot_note": shot_note, "qr_note": qr_note,
                                         "qr_data": st.session_state.get("qr_data", "")}
            st.success("Evidence saved — it now feeds the Complaint Generator.")
    if st.session_state.evidence:
        with st.expander("Saved evidence JSON"):
            st.json(st.session_state.evidence)
        if st.session_state.analysis:
            plan = get_plan(st.session_state.get("incident_stage", ORDER[0]))
            full = generate_evidence_report(st.session_state.evidence, st.session_state.analysis,
                                            st.session_state.sim, st.session_state.get("incident_stage", ""),
                                            st.session_state.get("decision", ""), plan["steps"])
            st.download_button("⬇️ Generate Evidence Pack (.txt)", data=full,
                               file_name=f"cybertwin_evidence_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                               mime="text/plain", use_container_width=True)

# ======================================================== COMPLAINT GENERATOR
elif page == "Complaint Generator":
    banner("📄 Cyber Incident Report",
           "Editable user-reviewed draft. Nothing is auto-filed; no official numbers are invented.",
           "Complaint Generator")
    a = st.session_state.analysis
    e = st.session_state.evidence
    if not a:
        st.warning("Run Threat Analysis first so AI indicators can be included.")
    else:
        cI1, cI2, cI3 = st.columns(3)
        cI1.markdown(f"<div class='glass'><b>Incident type</b><br><span class='small'>{a['threat_type']}</span></div>", unsafe_allow_html=True)
        cI2.markdown(f"<div class='glass'><b>Date / time</b><br><span class='small'>{e.get('datetime', a['timestamp'])}</span></div>", unsafe_allow_html=True)
        cI3.markdown(f"<div class='glass'><b>Risk</b><br><span class='small'>{a['risk_score']}/100 ({a['risk_level']}) • {a['confidence']}</span></div>", unsafe_allow_html=True)
        what = st.selectbox("What happened?", ORDER,
                            index=ORDER.index(st.session_state.get("incident_stage", ORDER[0])))
        notes = st.text_area("Extra notes (optional)", height=70)
        if st.button("✨ Generate Complaint", type="primary"):
            st.session_state.complaint_text = generate_complaint(
                {"sender": e.get("sender", a.get("sender", "")), "url": e.get("url", "; ".join(a.get("urls", []))),
                 "description": e.get("description", a.get("raw_text", "")), "datetime": e.get("datetime", a.get("timestamp", "")),
                 "transaction": e.get("transaction", ""), "upi": e.get("upi", ""),
                 "social": e.get("social", ""), "evidence_desc": e.get("evidence_desc", ""),
                 "screenshot_note": e.get("screenshot_note", ""), "qr_note": e.get("qr_note", ""),
                 "qr_data": e.get("qr_data", "")},
                a, what, notes)
        txt = st.text_area("Review & edit before downloading", value=st.session_state.complaint_text, height=420)
        st.session_state.complaint_text = txt
        if txt:
            st.download_button("⬇️ Download Complaint (.txt)", data=txt,
                               file_name=f"cybertwin_complaint_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                               mime="text/plain", use_container_width=True)
            if st.button("Mark as reported in history"):
                if st.session_state.history:
                    st.session_state.history[-1]["reported"] = "Yes"
                st.success("Marked. Track your reference in Complaint Tracking (user-entered/internal only).")

# ======================================================== COMPLAINT TRACKING
elif page == "Complaint Tracking":
    banner("📌 Incident Tracking Center",
           "Your personal reference tracker with timeline — not official government status.",
           "Complaint Tracking", badge=f"{len(st.session_state.tracking)} reference(s)")
    st.warning("YOUR personal tracker — not official government status. Only you enter/update these fields.")
    with st.form("trk", clear_on_submit=True):
        ref = st.text_input("Reference / acknowledgement number *")
        auth = st.text_input("Reporting authority (e.g. cybercrime portal / bank / platform)")
        dt = st.date_input("Date reported")
        status = st.selectbox("Current status (your own update)", ["Draft", "Submitted", "Under review (per authority)", "Info requested", "Resolved", "Closed"])
        fup = st.date_input("Follow-up date")
        if st.form_submit_button("Add / update entry", type="primary"):
            if not ref:
                st.error("Reference number is required.")
            else:
                st.session_state.tracking.append({"ref": ref, "authority": auth, "date": str(dt), "status": status, "followup": str(fup)})
                st.success("Tracker updated.")
    if st.session_state.tracking:
        st.markdown("### Timeline")
        for t in reversed(st.session_state.tracking):
            st.markdown(f"<div class='tl'><div class='tl-step'><b>{t['ref']}</b> — {t['status']}<br>"
                        f"<span class='small'>{t['authority']} • reported {t['date']} • follow-up {t['followup']}</span></div></div>",
                        unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(st.session_state.tracking), use_container_width=True)
    else:
        st.caption("No entries yet.")

# ================================================================== AI COPILOT
elif page == "AI Copilot":
    banner("🤖 CyberTwin AI Copilot",
           "Contextual assistant answering from your live threat, simulation, evidence & incident state.",
           "AI Copilot")
    a = st.session_state.analysis
    if a:
        risk_band(a)
        st.markdown(f"<span class='chip'>📌 {a['threat_type']}</span>"
                    f"<span class='chip'>Risk {a['risk_score']}/100 ({a['risk_level']})</span>"
                    + (f"<span class='chip'>🔗 {len(a.get('urls', []))} URL(s)</span>" if a.get("urls") else "")
                    + (f"<span class='chip'>🧾 Evidence saved</span>" if any(st.session_state.get("evidence", {}).values()) else "")
                    + f"<span class='chip'>Stage: {st.session_state.get('incident_stage', '')}</span>",
                    unsafe_allow_html=True)
    else:
        st.info("No case loaded — answers will be generic until you run a Threat Analysis.")
    st.markdown("**Try:**")
    presets = ["Is this message dangerous?", "I clicked the link. What should I do?",
               "I entered my password. What now?", "I shared the OTP. What should I do?",
               "I already made the payment.", "How can I verify this?",
               "What evidence should I preserve?", "Why is this risky?"]
    pc = st.columns(4)
    q = st.chat_input("Ask: Why is this risky? I clicked the link, what now? How do I verify?")
    for i, p in enumerate(presets):
        with pc[i % 4]:
            st.markdown(f"<div class='glass' style='padding:10px 12px'>💬 <span class='small'>{p}</span></div>",
                        unsafe_allow_html=True)
            if st.button("Ask →", key=f"preset_{i}"):
                q = p
    for role, msg in st.session_state.copilot_hist:
        with st.chat_message(role):
            st.markdown(msg)
    if q:
        st.session_state.copilot_hist.append(("user", q))
        with st.chat_message("user"):
            st.markdown(q)
        ans = answer_question(q, a, st.session_state.sim, st.session_state.get("evidence"), st.session_state.get("incident_stage"))
        st.session_state.copilot_hist.append(("assistant", ans))
        with st.chat_message("assistant"):
            st.markdown(ans)
        st.rerun()
    if a:
        with st.expander("Current context sent to Copilot"):
            st.json({"threat": a.get("threat_type"), "risk": a.get("risk_score"),
                     "urls": a.get("urls", []),
                     "incident": st.session_state.get("incident_stage"),
                     "decision": st.session_state.get("decision"),
                     "evidence_saved": bool(any(st.session_state.get("evidence", {}).values()))})

# ================================================================== RISK HISTORY
elif page == "Risk History":
    banner("📊 Cyber Risk History",
           "Every analysis with decisions and outcomes — your real session data only.",
           "Risk History", badge=f"{len(st.session_state.history)} scan(s)")
    h = st.session_state.history
    if not h:
        st.info("No analyses yet this session.")
    else:
        df = pd.DataFrame(h)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total scans", len(df))
        m2.metric("Avg risk", f"{df['score'].mean():.1f}/100")
        m3.metric("Critical", int((df["level"] == "Critical").sum()))
        m4.metric("Reported", int((df["reported"] == "Yes").sum()))
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.pie(df, names="level", title="Risk Distribution",
                                   color="level",
                                   color_discrete_map={"Critical": "#DC2626", "High": "#EF4444",
                                                       "Medium": "#F59E0B", "Low": "#22C55E"},
                                   template="plotly_dark"), use_container_width=True)
        with g2:
            st.plotly_chart(px.bar(df["threat"].value_counts().reset_index(), x="threat", y="count",
                                   title="Threat Categories", color="threat", template="plotly_dark"),
                            use_container_width=True)
        st.plotly_chart(px.line(df.reset_index(), x="index", y="score", markers=True,
                                title="Risk Timeline", template="plotly_dark"), use_container_width=True)
        if "action" in df.columns:
            st.plotly_chart(px.bar(df["action"].value_counts().reset_index(), x="action", y="count",
                                   title="Decision Outcomes", color="action", template="plotly_dark"),
                            use_container_width=True)
        st.markdown("### 🕒 Timeline")
        for x in reversed(h):
            st.markdown(f"<div class='tl'><div class='tl-step'><b>{x['time']}</b> — {x['threat']} "
                        f"<span class='sev sev-{x['level']}'>{x['level']} {x['score']}</span><br>"
                        f"<span class='small'>Decision: {x.get('action', '—')} • Recommended: {str(x.get('recommended', '—'))[:80]} • "
                        f"Evidence: {x.get('evidence_saved', '—')} • Complaint: {x.get('complaint', '—')} • Reported: {x.get('reported', '—')}</span></div></div>",
                        unsafe_allow_html=True)
        with st.expander("Full table + CSV"):
            st.dataframe(df, use_container_width=True)
            st.download_button("⬇️ Download history (.csv)", data=df.to_csv(index=False).encode(),
                               file_name="cybertwin_history.csv", mime="text/csv")

# ============================================================ AWARENESS TRAINING
elif page == "Awareness Training":
    banner("🎓 Cyber Awareness Lab",
           "Threat-typed scenarios with difficulty, progress, feedback and safety lessons.",
           "Awareness Training")
    scenarios = [
        {"t": "Phishing", "d": "Easy", "q": "SMS: 'Bank account blocked! Verify now: http://bank-secure01.tk/login'. You need to check.", "opts": ["Click and login now", "Ignore + verify via official app/number", "Reply with OTP to unblock"], "ans": 1,
         "why": "Links can be fake login pages. Always verify independently via the official app or number you already know."},
        {"t": "Investment scam", "d": "Easy", "q": "Telegram: 'Double your money in 1 hour, guaranteed profit! Invest now.'", "opts": ["Invest a small amount to test", "Send to friends first", "Treat as investment scam: don't pay, report"], "ans": 2,
         "why": "Guaranteed high returns + urgency = classic investment scam. Real investments never guarantee profit."},
        {"t": "Credential theft", "d": "Medium", "q": "Caller: 'I'm from customer care, share the OTP to stop a fraud transaction.'", "opts": ["Share OTP quickly to stop fraud", "Refuse, hang up, call official number yourself", "Ask them to read your balance first"], "ans": 1,
         "why": "No genuine support asks for OTPs. Sharing it authorises the fraud. Hang up and call back officially."},
        {"t": "Malicious QR", "d": "Medium", "q": "QR at a shop: sticker pasted over the original QR code.", "opts": ["Scan it — QR codes are always safe", "Pay a small test amount", "Don't scan; ask staff / use official QR"], "ans": 2,
         "why": "Overlaid QR stickers redirect money to scammers. Verify the source before scanning/paying."},
        {"t": "Fake job scam", "d": "Medium", "q": "Job offer: 'Pay ₹499 registration to unlock ₹5,000/day task job.'", "opts": ["Pay — it's a small amount", "Pay then verify", "Real jobs don't charge fees: verify company independently"], "ans": 2,
         "why": "Upfront fees for jobs/tasks are a fake-job-scam hallmark. Verify the company through official channels."},
        {"t": "Impersonation", "d": "Hard", "q": "Instagram DM from 'friend' (2 followers, new account): 'Need ₹2000 urgently, UPI now, don't call.'", "opts": ["Send immediately to help", "Verify via call/known number; treat as impersonation until proven", "Share your UPI PIN to confirm"], "ans": 1,
         "why": "Impersonation: new/low-follower account + urgency + 'don't call' = verify through a separate trusted channel."},
        {"t": "Delivery scam", "d": "Medium", "q": "Email: 'Parcel held — pay ₹149 customs at delivery-track99.top/pay to release.'", "opts": ["Pay now to avoid return", "Enter card on the link + pay", "Check via official courier site/app; don't use the link"], "ans": 2,
         "why": "Delivery/refund scam: fee + look-alike link + urgency. Track only on the official site."},
        {"t": "Harassment", "d": "Hard", "q": "Unknown number: 'I have your private video. Pay ₹10,000 in Bitcoin or I leak it.'", "opts": ["Pay quietly to stop the leak", "Send more photos to negotiate", "Do NOT pay; preserve evidence, block, report, seek trusted help"], "ans": 2,
         "why": "Harassment/blackmail: paying never guarantees deletion and invites repeat demands. Preserve evidence and report."},
    ]
    done = sum(1 for i in range(len(scenarios)) if st.session_state.get(f"quiz_{i}") is not None)
    st.progress(done / len(scenarios), text=f"Progress: {done}/{len(scenarios)} answered")
    score = 0
    for i, s in enumerate(scenarios):
        st.markdown(f"<div class='glass'><span class='chip'>{s['t']}</span> <span class='chip'>{s['d']}</span><br>"
                    f"<b>Q{i + 1}.</b> {s['q']}<br><span class='small'>Choose the safe decision:</span></div>",
                    unsafe_allow_html=True)
        pick = st.radio(f"Your choice (Q{i + 1})", s["opts"], key=f"quiz_{i}", index=None)
        if pick is not None:
            if pick == s["opts"][s["ans"]]:
                st.success(f"✅ Correct — safe decision. {s['why']}")
                score += 1
            else:
                st.error(f"❌ Safer decision: **{s['opts'][s['ans']]}**. {s['why']}")
    st.divider()
    st.metric("Your score", f"{score}/{len(scenarios)}")
    if score == len(scenarios):
        st.balloons()
        st.success("🏆 Cyber-safe champion! Lesson: pause, verify independently, never share codes/pay under pressure.")

# ============================================================ ML MODEL LAB
elif page == "ML Model Lab":
    banner("🔬 ML Model Lab", "Insight into the ML models driving CyberTwin.", "ML Model Lab")
    import json
    import os
    from src.models.model_loader import get_text_model, get_url_model
    
    st.markdown("### Model Health Status")
    text_model = get_text_model()
    url_model = get_url_model()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Machine Learning Models**")
        if text_model:
            st.success("✓ Text Model: Loaded")
        else:
            st.error("✗ Text Model: Failed to load (Retrain required)")
            
        if url_model:
            st.success("✓ URL Model: Loaded")
        else:
            st.error("✗ URL Model: Failed to load (Retrain required)")
            
    with col2:
        st.markdown("**Image Processing**")
        st.success("✓ OCR (Optical Character Recognition)")
        st.success("✓ QR Decoder")
    
    st.divider()
    
    text_meta_path = os.path.join(os.path.dirname(__file__), "models", "metadata", "text_model_metadata.json")
    url_meta_path = os.path.join(os.path.dirname(__file__), "models", "metadata", "url_model_metadata.json")
    
    t1, t2, t3 = st.tabs(["Text Model", "URL Model", "Image Processing"])
    
    with t1:
        if os.path.exists(text_meta_path):
            with open(text_meta_path, "r") as f:
                t_meta = json.load(f)
            st.markdown(f"**Dataset:** {t_meta['dataset']}")
            st.markdown(f"**Training Date:** {t_meta['training_date']}")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Test Accuracy", f"{t_meta['metrics']['test_accuracy']:.2%}")
            c2.metric("Test F1-Score", f"{t_meta['metrics']['test_f1']:.2%}")
            c3.metric("Test Precision", f"{t_meta['metrics']['test_precision']:.2%}")
            c4.metric("Test Recall", f"{t_meta['metrics']['test_recall']:.2%}")
            
            p1, p2 = st.columns(2)
            with p1:
                st.markdown("### Confusion Matrix")
                try:
                    st.image("reports/figures/text_confusion_matrix.png", use_container_width=True)
                except Exception:
                    st.info("Confusion matrix image not available.")
            with p2:
                st.markdown("### PCA / SVD Visualization")
                try:
                    st.image("reports/figures/text_pca_scatter.png", use_container_width=True)
                except Exception:
                    st.info("PCA visualization not available. Retrain the model.")
        else:
            st.warning("Text model metadata not found. Train the model first.")

    with t2:
        if os.path.exists(url_meta_path):
            with open(url_meta_path, "r") as f:
                u_meta = json.load(f)
            st.markdown(f"**Dataset:** {u_meta['dataset']}")
            st.markdown(f"**Training Date:** {u_meta['training_date']}")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Test Accuracy", f"{u_meta['metrics']['test_accuracy']:.2%}")
            c2.metric("Test F1-Score", f"{u_meta['metrics']['test_f1']:.2%}")
            c3.metric("Test Precision", f"{u_meta['metrics']['test_precision']:.2%}")
            c4.metric("Test Recall", f"{u_meta['metrics']['test_recall']:.2%}")
            
            p1, p2 = st.columns(2)
            with p1:
                st.markdown("### Confusion Matrix")
                try:
                    st.image("reports/figures/url_confusion_matrix.png", use_container_width=True)
                except Exception:
                    st.info("Confusion matrix image not available.")
            with p2:
                st.markdown("### PCA Visualization")
                try:
                    st.image("reports/figures/url_pca_scatter.png", use_container_width=True)
                except Exception:
                    st.info("PCA visualization not available. Retrain the model.")
        else:
            st.warning("URL model metadata not found. Train the model first.")

    with t3:
        st.markdown("### 📊 Status")
        st.markdown("✓ **CNN Classifier (MobileNetV2):** Available (if TF installed)\n✓ **OCR:** Available  \n✓ **QR Decoder:** Available")
        
        st.markdown("### 🖼️ Image Input Types")
        st.markdown("- Screenshot\n- Image containing text\n- Image containing QR code\n- Screenshot containing suspicious URL/text")
        
        st.markdown("### 🧠 CNN Image Engine")
        st.markdown("**Model:** MobileNetV2 (Pre-trained on ImageNet)  \n**Library:** `tensorflow` / `keras`  \n**Input:** Images / Screenshots  \n**Output:** Semantic Object Probabilities & Interface Type (e.g., 'Login Screen')")

        st.markdown("### 👁️ OCR Engine")
        st.markdown("**Engine:** Tesseract  \n**Library:** `pytesseract`  \n**Input:** Images / Screenshots  \n**Output:** Extracted Text  \n**Preprocessing:** None (Raw PIL Image to string)")
        
        st.markdown("### ◧ QR Decoder")
        st.markdown("**Library:** OpenCV (`cv2.QRCodeDetector`)  \n**Input:** QR Images  \n**Output:** Decoded Payload / URL  \n**Error Handling:** Fallback to `detectAndDecodeMulti` if primary decode fails.")
        
        st.markdown("### 🔄 Pipeline")
        st.code('''Image
 ↓
Preprocessing (OpenCV BGR Conversion / MobileNetV2 Normalization)
 ↓
CNN Feature Extraction + OCR + QR Detection
 ↓
Text / URL Extraction & Image Type Detection
 ↓
Text Model / URL Model
 ↓
Risk Engine''', language="text")
        
        st.markdown("### 📈 Evaluation")
        st.info("No labelled image-processing evaluation dataset is currently configured.")
        
        st.markdown("### 🛠️ Implementation Details")
        st.markdown("**Source:** `media_utils.py`  \n**Libraries:** `pytesseract`, `cv2` (OpenCV), `numpy`, `Pillow`")


st.markdown("""<div class="footer">🛡️ <b>CyberTwin</b> — AI-Powered Counterfactual Cyber-Risk Simulator<br>
<span class="small">Explainable ML + heuristic layer •
Simulations are plausible, not certain • Drafts & tracking are user-managed, not official filings.</span></div>""",
            unsafe_allow_html=True)

