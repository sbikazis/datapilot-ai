from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO
import csv
import json
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from universal_engine import profile_dataset, grouped_summary, time_summary
from time_intelligence import analyze_time_series
from domain_intelligence import assess_domain
from recommendation_engine import rank_findings, build_next_questions
from report_intelligence import build_report_data, render_html_report, report_workbook_sheets
from visualizations import build_time_figure
from studio_logic import recommend_visualization, numeric_summary, safe_correlation, category_summary, build_evidence_findings, detect_delimiter, selected_point_values, selected_point_indices
from semantic_engine import infer_semantic_fields

st.set_page_config(
    page_title="DataPilot AI — Intelligence Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ──────────────────────────────────────────────────────────
defaults = {
    "workspace_name": "My workspace",
    "theme_mode": "Light",
    "density": "Comfortable",
    "workspace_mark": "◈",
    "workspace_subtitle": "ADAPTIVE DATA INTELLIGENCE",
    "workspace_logo_upload": None,
    "accent_palette": "Violet",
    "precision": 2,
    "default_top_n": 12,
    "show_method_notes": True,
    "nav_page": "Overview",
    "active_filters": {},
    "role_overrides": {},
    "chart_type": "Recommended",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, dict) else value


def reset_workspace_preferences():
    for key, value in defaults.items():
        st.session_state[key] = value.copy() if isinstance(value, dict) else value


def go_to_page(page, mode=None):
    st.session_state["nav_page"] = page
    if mode:
        st.session_state["chart_type"] = mode
        st.session_state.pop("studio_mode", None)


def apply_analysis_defaults():
    st.session_state.pop("studio_mode", None)
    st.session_state.pop("cmp_limit", None)



def investigate_signal(item):
    """Carry a selected evidence signal into the analysis workspace."""
    st.session_state["selected_signal"] = {
        "title": str(item.get("title", "Selected signal")),
        "detail": str(item.get("detail", "")),
        "kind": str(item.get("kind", "observation")),
        "next_step": str(item.get("next_step", item.get("action", "Inspect the supporting records"))),
    }
    kind = str(item.get("kind", "")).lower()
    title = str(item.get("title", "")).lower()
    if any(token in kind + " " + title for token in ("time", "date", "trend", "period")):
        mode = "Time trend"
    elif any(token in kind + " " + title for token in ("correlation", "relationship", "association")):
        mode = "Relationship"
    elif any(token in kind + " " + title for token in ("distribution", "outlier", "spread")):
        mode = "Distribution"
    elif any(token in kind + " " + title for token in ("category", "segment", "group", "concentration")):
        mode = "Compare groups"
    else:
        mode = "Recommended"
    st.session_state["nav_page"] = "Analysis Studio"
    if mode != "Recommended":
        st.session_state["chart_type"] = mode
        st.session_state.pop("studio_mode", None)

# ── Design system ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--ink:#182239;--muted:#75819a;--line:#e6eaf2;--surface:#fff;--canvas:#f4f6fb;--violet:#6955e8;--violet2:#8a78f5;--cyan:#21b8b2;--gold:#e5a83f;--rose:#dc6c9b}
.stApp{background:radial-gradient(ellipse at 4% -8%,rgba(105,85,232,.10),transparent 30%),radial-gradient(ellipse at 100% 5%,rgba(33,184,178,.08),transparent 25%),var(--canvas);color:var(--ink);font-family:'DM Sans',sans-serif}
.block-container{max-width:1540px;padding:1.45rem 2.4rem 4rem}
h1,h2,h3,h4{font-family:'Manrope',sans-serif!important;letter-spacing:-.035em;color:var(--ink)!important}
h1{font-weight:800!important;font-size:2.05rem!important} h2{font-weight:800!important;font-size:1.45rem!important} h3{font-weight:750!important;font-size:1.12rem!important}
p,li{line-height:1.62}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#111a30 0%,#202b4a 70%,#302b5b 100%);border-right:1px solid rgba(255,255,255,.08)}
[data-testid="stSidebar"] *{color:#eef1ff}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#aab4d0}
[data-testid="stSidebar"] [data-testid="stFileUploader"]{background:rgba(255,255,255,.06);border:1px dashed rgba(255,255,255,.25);border-radius:15px}
[data-testid="stSidebar"] [data-testid="stFileUploader"] section{background:transparent}
[data-testid="stMetric"]{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:17px;padding:15px 17px;box-shadow:0 7px 22px rgba(25,39,74,.045);min-height:108px}
[data-testid="stMetricLabel"]{font-size:.78rem;font-weight:700;color:var(--muted)!important}
[data-testid="stMetricValue"]{font-family:'Manrope',sans-serif;font-size:1.65rem;font-weight:800;color:var(--ink)}
.stButton>button,.stDownloadButton>button{border:1px solid #e2e5f0;border-radius:11px;background:#fff;color:#303c59;font-weight:700;min-height:2.55rem;transition:all .16s ease}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:#9d91f1;color:#5945d5;background:#f7f5ff}
button[kind="primary"]{background:linear-gradient(110deg,#6250dc,#8a70ef)!important;color:white!important;border:0!important}
[data-testid="stTabs"] button{font-weight:700}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:13px;overflow:hidden}
[data-testid="stPlotlyChart"]{background:#fff;border:1px solid var(--line);border-radius:16px;padding:8px 8px 0;box-shadow:0 5px 18px rgba(25,39,74,.025)}
[data-testid="stExpander"]{background:#fff;border:1px solid var(--line);border-radius:13px}
[data-testid="stAlert"]{border-radius:13px}
[data-testid="stSelectbox"],[data-testid="stMultiSelect"],[data-testid="stTextInput"]{border-radius:10px}
.brand{display:flex;align-items:center;gap:10px;margin:5px 0 19px}
.brandmark{width:39px;height:39px;border-radius:13px;background:linear-gradient(135deg,#806bf4,#39c7c0);display:grid;place-items:center;color:#fff;font-size:23px;font-weight:800;box-shadow:0 7px 18px #080e2266}
.brandname{font-family:Manrope,sans-serif;font-weight:800;font-size:1.1rem;letter-spacing:-.04em}
.brandtag{font-size:.59rem;letter-spacing:.16em;color:#aeb8d7;font-weight:800}
.hero{position:relative;overflow:hidden;border-radius:23px;padding:27px 30px;background:linear-gradient(112deg,#111a30 0%,#29345d 58%,#564a9b 100%);color:#fff;margin:0 0 21px;box-shadow:0 17px 42px rgba(30,35,78,.14)}
.hero:before{content:"";position:absolute;width:360px;height:360px;right:-90px;top:-210px;border:1px solid #ffffff1c;border-radius:50%;box-shadow:0 0 0 35px #ffffff08,0 0 0 75px #ffffff06}
.hero:after{content:"";position:absolute;width:160px;height:160px;right:16%;bottom:-120px;background:#35c6bb30;filter:blur(4px);border-radius:50%}
.hero .eyebrow{color:#86e4dc;font-size:.68rem;letter-spacing:.19em;font-weight:800;margin-bottom:9px}
.hero h1{color:white!important;font-size:2.05rem!important;margin:0 0 8px}
.hero p{color:#d7def5;margin:0;max-width:900px;font-size:.96rem}
.hero .hero-meta{margin-top:17px;color:#c4cceb;font-size:.76rem;letter-spacing:.02em}
.pagehead{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin:7px 0 17px}
.kicker{color:#7565d9;text-transform:uppercase;letter-spacing:.15em;font-size:.68rem;font-weight:800}
.subtle{color:var(--muted);font-size:.88rem}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:17px 19px;box-shadow:0 6px 20px rgba(25,39,74,.035);height:100%}
.card-label{color:#78849b;font-size:.72rem;font-weight:800;text-transform:uppercase;letter-spacing:.1em}
.card-title{color:#202c46;font-family:Manrope,sans-serif;font-size:1rem;font-weight:800;margin:6px 0}
.card-copy{color:#77839a;font-size:.84rem;line-height:1.55}
.insight{background:#fff;border:1px solid var(--line);border-left:4px solid #7965e8;border-radius:14px;padding:15px 17px;margin:9px 0;box-shadow:0 5px 17px rgba(30,42,75,.03)}
.insight .kind{font-size:.65rem;letter-spacing:.13em;text-transform:uppercase;font-weight:800;color:#7565d9}
.insight strong{display:block;color:#202b45;margin:4px 0;font-size:.98rem}
.insight p{margin:3px 0;color:#56627a;font-size:.88rem}
.insight .next{color:#7d879c;font-size:.79rem;margin-top:7px}
.sectionline{height:1px;background:var(--line);margin:19px 0}
.pill{display:inline-block;padding:4px 9px;border-radius:99px;background:#f0edff;color:#6755d9;font-size:.69rem;font-weight:800}
.empty{background:#fff;border:1px dashed #ccd3e2;border-radius:17px;padding:28px;text-align:center;color:#77839a}
.upload-panel{background:linear-gradient(135deg,#fff 0%,#f7f6ff 100%);border:1px solid #dedaf8;border-radius:19px;padding:19px 22px 12px;box-shadow:0 10px 28px rgba(45,42,100,.055)}
.upload-guidance{height:100%;min-height:150px;background:#fff;border:1px solid var(--line);border-radius:17px;padding:18px 19px;box-shadow:0 6px 20px rgba(25,39,74,.035)}
.format-list{display:flex;flex-wrap:wrap;gap:7px;margin:12px 0 3px}
.format-list span{display:inline-flex;align-items:center;padding:5px 9px;border-radius:8px;background:#f1efff;color:#5948c9;font-size:.7rem;font-weight:800;letter-spacing:.04em}
.loaded-dataset{display:flex;align-items:center;gap:12px;padding:12px 16px;margin:0 0 18px;background:#fff;border:1px solid #dcece8;border-radius:13px}
.loaded-dataset strong{color:var(--ink);font-size:.9rem}
.loaded-dot{width:9px;height:9px;border-radius:50%;background:#21a783;box-shadow:0 0 0 4px #e4f6f0;flex:none}
.overview-intro{display:flex;justify-content:space-between;align-items:center;gap:18px;margin:4px 0 18px}
.overview-live{display:flex;align-items:center;gap:8px;padding:8px 12px;border:1px solid #cdece3;border-radius:999px;background:#f0fbf7;color:#247b64;font-size:.67rem;font-weight:800;letter-spacing:.08em;white-space:nowrap}
.overview-live span{width:7px;height:7px;border-radius:50%;background:#25a77e;box-shadow:0 0 0 4px #d9f4e9}
.signal-card{background:#fff;border:1px solid var(--line);border-radius:15px;padding:15px 17px;margin:9px 0;box-shadow:0 5px 18px rgba(25,39,74,.035)}
.signal-top{display:flex;align-items:center;gap:9px;margin-bottom:7px}
.signal-index{font-size:.68rem;font-weight:800;color:#9aa3b5;letter-spacing:.08em}
.signal-kind{font-size:.64rem;letter-spacing:.12em;text-transform:uppercase;font-weight:800;color:#6c5ad5}
.signal-title{font-family:Manrope,sans-serif;font-weight:800;font-size:.98rem;color:#202b45}
.signal-card p{font-size:.82rem;color:#68758c;line-height:1.55;margin:5px 0}
.signal-next{font-size:.69rem;color:#7565d9;font-weight:700;letter-spacing:.025em;margin-top:8px}
.signal-meta{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.signal-meta span{font-size:.64rem;color:#6b7690;background:#f3f4fa;border-radius:7px;padding:4px 7px}
.health-card,.domain-card{background:#fff;border:1px solid var(--line);border-radius:15px;padding:15px 16px;margin:8px 0 13px}
.health-heading{display:flex;justify-content:space-between;align-items:center;color:#65718a;font-size:.8rem;font-weight:700}
.health-heading strong{font-family:Manrope,sans-serif;font-size:1.25rem;color:#202b45}
.health-track{height:8px;border-radius:99px;background:#edf0f6;overflow:hidden;margin:12px 0 8px}
.health-track span{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#6955e8,#21b8b2)}
.health-foot{font-size:.72rem;color:#8993a7}
.health-row{display:flex;justify-content:space-between;align-items:center;padding:9px 2px;border-bottom:1px solid #edf0f5}
.health-row:last-child{border-bottom:0}
.health-row div{display:flex;flex-direction:column;gap:2px}
.health-row strong{font-size:.81rem;color:#34415c}
.health-row span{font-size:.69rem;color:#8993a7}
.health-row b{font-family:Manrope,sans-serif;font-size:.92rem;color:#202b45}
.next-step{padding:11px 12px;border:1px solid #e8e6f6;border-radius:12px;background:#fbfaff;margin:8px 0}
.next-step strong{font-size:.82rem;color:#303858}
.next-step p{font-size:.76rem;color:#6e7890;margin:4px 0}
.next-step span{font-size:.67rem;color:#8176c7}
[data-testid="stFileUploader"]{border:1px dashed #aaa0e9;border-radius:14px;background:rgba(255,255,255,.78);padding:8px}
[data-testid="stFileUploader"] section{background:transparent}
[data-testid="stFileUploader"] button{border-radius:9px}
@media(max-width:900px){.block-container{padding:1rem 1rem 3rem}.hero{padding:22px}.hero h1{font-size:1.6rem!important}.upload-panel{padding:16px}.upload-guidance{min-height:0}.pagehead{align-items:flex-start;flex-direction:column}.overview-intro{align-items:flex-start;flex-direction:column}.overview-live{align-self:flex-start}}

/* ── COSMIC INTELLIGENCE DESIGN LAYER ───────────────────────────────────── */
:root{--space-950:#080d20;--space-900:#0d1530;--space-800:#172348;--nebula-violet:#927cff;--nebula-cyan:#55d9e8;--nebula-blue:#5b9cff;--nebula-gold:#f2c879;--glow-violet:rgba(145,124,255,.24);--glow-cyan:rgba(85,217,232,.18)}
.stApp{background:radial-gradient(ellipse at 12% 0%,rgba(112,91,232,.13),transparent 33%),radial-gradient(ellipse at 92% 8%,rgba(47,190,211,.10),transparent 28%),linear-gradient(180deg,#f6f7ff 0%,#f1f5fc 54%,#f7f8fc 100%);background-attachment:fixed}
.block-container{max-width:1600px;padding-top:1.25rem;padding-bottom:4.5rem}
[data-testid="stSidebar"]{background:radial-gradient(ellipse at 50% 0%,rgba(104,91,209,.28),transparent 43%),linear-gradient(165deg,#090f25 0%,#111d3c 56%,#211e4b 100%);box-shadow:12px 0 38px rgba(17,25,57,.12)}
[data-testid="stSidebar"] [data-testid="stRadio"] label{border-radius:11px;padding:.35rem .55rem;transition:background .2s ease}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:rgba(153,139,255,.13)}
.brandmark{position:relative;isolation:isolate;border:1px solid rgba(255,255,255,.28);box-shadow:0 0 0 5px rgba(142,125,255,.08),0 0 28px rgba(83,206,231,.25)}
.brandmark:after{content:"";position:absolute;inset:-5px;border:1px solid rgba(107,220,235,.22);border-radius:16px;z-index:-1}
.brandname{letter-spacing:-.055em}
.hero{isolation:isolate;min-height:220px;padding:34px 38px;background:radial-gradient(ellipse at 80% 18%,rgba(118,103,242,.55),transparent 30%),radial-gradient(ellipse at 100% 100%,rgba(42,192,211,.27),transparent 34%),linear-gradient(118deg,#080f27 0%,#17254c 53%,#34306c 100%);border:1px solid rgba(176,185,255,.18);box-shadow:0 22px 60px rgba(23,29,74,.22),inset 0 1px rgba(255,255,255,.12)}
.hero:before{width:410px;height:410px;right:-80px;top:-250px;border:1px solid rgba(196,201,255,.28);box-shadow:0 0 0 24px rgba(255,255,255,.035),0 0 0 54px rgba(255,255,255,.025),0 0 0 88px rgba(255,255,255,.018),0 0 70px rgba(128,113,255,.22)}
.hero:after{width:220px;height:220px;right:19%;bottom:-165px;background:radial-gradient(circle,rgba(72,223,229,.28),rgba(72,223,229,0) 68%);filter:blur(2px)}
.hero .eyebrow{color:#8deaf0;letter-spacing:.22em}
.hero h1{font-size:clamp(2rem,4vw,3rem)!important;letter-spacing:-.065em;text-shadow:0 4px 28px rgba(138,129,255,.22)}
.hero p{max-width:820px;color:#e1e7ff;font-size:1rem}
.hero .hero-meta{color:#b9c8ef;letter-spacing:.12em}
.kicker{color:#7161dc;letter-spacing:.18em}
.pagehead{padding:16px 19px;border:1px solid rgba(139,148,211,.17);border-radius:18px;background:linear-gradient(110deg,rgba(255,255,255,.82),rgba(248,249,255,.66));box-shadow:0 8px 25px rgba(37,48,95,.045)}
.card,.signal-card,.health-card,.domain-card,.upload-guidance,.upload-panel{border-color:rgba(128,137,193,.22);box-shadow:0 10px 28px rgba(33,43,89,.055),inset 0 1px rgba(255,255,255,.8);transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease}
.card:hover,.signal-card:hover,.health-card:hover,.domain-card:hover{transform:translateY(-2px);border-color:rgba(126,111,231,.42);box-shadow:0 15px 34px rgba(48,53,117,.10),0 0 24px rgba(120,105,230,.06)}
[data-testid="stMetric"]{position:relative;overflow:hidden;border-color:rgba(128,137,193,.22);background:linear-gradient(145deg,rgba(255,255,255,.98),rgba(247,248,255,.94));box-shadow:0 10px 26px rgba(33,43,89,.065)}
[data-testid="stMetric"]:before{content:"";position:absolute;left:0;top:0;right:0;height:3px;background:linear-gradient(90deg,#8a75f5,#55d9e8,#f2c879)}
[data-testid="stMetricValue"]{letter-spacing:-.055em}
[data-testid="stPlotlyChart"]{border:1px solid rgba(126,139,198,.22);border-radius:18px;background:linear-gradient(145deg,rgba(255,255,255,.98),rgba(249,250,255,.94));box-shadow:0 12px 30px rgba(31,43,92,.06),inset 0 1px rgba(255,255,255,.9);transition:box-shadow .2s ease,border-color .2s ease}
[data-testid="stPlotlyChart"]:hover{border-color:rgba(112,103,224,.4);box-shadow:0 16px 36px rgba(31,43,92,.10),0 0 26px rgba(110,100,226,.07)}
.signal-card{border-left:3px solid transparent;border-image:linear-gradient(180deg,#907cff,#55d9e8) 1;background:linear-gradient(120deg,#fff 0%,#fbfbff 100%)}
.signal-index{color:#7f83a8}
.signal-kind{color:#6e60d7}
.signal-next{color:#6558cb}
.overview-live{box-shadow:0 0 0 4px rgba(54,188,151,.06)}
.upload-panel{background:radial-gradient(ellipse at 90% 0%,rgba(125,111,238,.12),transparent 45%),linear-gradient(135deg,#fff 0%,#f7f7ff 100%)}
.upload-guidance{background:linear-gradient(145deg,#fff,#f9faff)}
.format-list span{background:linear-gradient(135deg,#f0edff,#e9faff);border:1px solid rgba(129,115,230,.10)}
.loaded-dataset{box-shadow:0 7px 20px rgba(31,130,111,.06)}
.stButton>button,.stDownloadButton>button{border-color:rgba(126,137,193,.25);box-shadow:0 3px 10px rgba(37,45,91,.035);transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-1px);box-shadow:0 8px 18px rgba(82,73,174,.12);border-color:#9385ef}
button[kind="primary"]{background:linear-gradient(112deg,#6655dc 0%,#8874ef 54%,#3abac8 140%)!important;box-shadow:0 8px 20px rgba(104,84,220,.24)!important}
button[kind="primary"]:hover{box-shadow:0 12px 28px rgba(104,84,220,.34)!important}
[data-testid="stSelectbox"]>div,[data-testid="stMultiSelect"]>div,[data-testid="stTextInput"]>div,[data-testid="stNumberInput"]>div{border-radius:12px}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{border-radius:11px}
[data-testid="stTabs"] button[aria-selected="true"]{color:#6657d5;border-bottom-color:#7565e7}
[data-testid="stProgress"]>div>div>div{background:linear-gradient(90deg,#7664e8,#55d9e8)}
[data-testid="stFileUploader"]{border:1px dashed rgba(119,105,220,.55);background:linear-gradient(145deg,rgba(255,255,255,.88),rgba(246,247,255,.9));box-shadow:inset 0 0 22px rgba(121,105,224,.035)}
[data-testid="stAlert"]{border:1px solid rgba(126,137,193,.18);box-shadow:0 6px 18px rgba(33,43,89,.04)}
:focus-visible{outline:3px solid rgba(82,194,219,.8)!important;outline-offset:2px!important}
@media(max-width:900px){.hero{min-height:0;padding:25px 23px}.hero:before{right:-180px}.block-container{padding-left:1rem;padding-right:1rem}.pagehead{padding:14px}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{transition:none!important;animation:none!important;scroll-behavior:auto!important}}
/* Dark theme keeps the same nebula identity with readable contrast. */
.stApp:has([data-testid="stSidebar"]) .unused-cosmic-hook{display:none}

</style>
""", unsafe_allow_html=True)


accent_colors = {
    "Violet": ("#6955e8", "#8a78f5"),
    "Ocean": ("#1679c5", "#39b7d8"),
    "Emerald": ("#16866f", "#42b99b"),
    "Amber": ("#b87516", "#e5ad4b"),
}
accent_primary, accent_secondary = accent_colors.get(st.session_state.accent_palette, accent_colors["Violet"])
st.markdown(f"<style>:root{{--violet:{accent_primary};--violet2:{accent_secondary}}}.brandmark{{background:linear-gradient(135deg,{accent_primary},{accent_secondary})}}.stButton>button[kind='primary']{{background:linear-gradient(110deg,{accent_primary},{accent_secondary})!important}}</style>", unsafe_allow_html=True)

if st.session_state.theme_mode == "Dark":
    st.markdown("""
    <style>
    .stApp{background:#101626;color:#e8ecf8}
    h1,h2,h3,h4{color:#edf0ff!important}
    .card,.insight,.signal-card,.health-card,.domain-card,[data-testid="stMetric"],[data-testid="stPlotlyChart"],[data-testid="stExpander"],[data-testid="stDataFrame"]{background:#192238!important;border-color:#2c3854!important;color:#e8ecf8}
    .card-title,.insight strong,.signal-title,.health-heading strong,.health-row strong,.health-row b,.loaded-dataset strong{color:#edf0ff!important}
    .card-copy,.insight p,.signal-card p,.health-row span,.health-foot,.subtle{color:#aab5ce!important}
    .next-step{background:#202a43!important;border-color:#374360!important}
    .next-step strong{color:#edf0ff!important}
    .health-track{background:#303b55!important}
    .loaded-dataset{background:#192238!important;border-color:#2c5b51!important}
    .overview-live{background:#17352f!important;border-color:#285c50!important;color:#a5e4cf!important}
    .signal-meta span{background:#29354f!important;color:#c0c9df!important}
    .pagehead,.upload-panel,.upload-guidance,.signal-card{background:#192238!important;border-color:#2c3854!important}
    .upload-panel h2,.upload-guidance .card-label,.pagehead h2{color:#edf0ff!important}
    .upload-panel p,.upload-guidance .card-copy,.pagehead .subtle{color:#aab5ce!important}
    .format-list span{background:#29354f!important;color:#c0c9df!important;border-color:#3b4866!important}
    [data-testid="stMetric"]{background:linear-gradient(145deg,#1b2945,#192238)!important}
    [data-testid="stPlotlyChart"]{background:#192238!important}
    .stTextInput input,.stSelectbox div[data-baseweb="select"],.stMultiSelect div[data-baseweb="select"]{background:#192238;color:#edf0ff}
    [data-testid="stMetricValue"]{color:#edf0ff}
    [data-testid="stMetricLabel"]{color:#aab5ce!important}
    </style>
    """, unsafe_allow_html=True)
# Keep Plotly visuals consistent with the scientific / nebula design language.
plot_text = "#dce6ff" if st.session_state.theme_mode == "Dark" else "#53617d"
plot_grid = "rgba(190,202,232,.14)" if st.session_state.theme_mode == "Dark" else "rgba(114,132,177,.14)"
px.defaults.color_discrete_sequence = ["#7664e8", "#36bfc9", "#4f91df", "#e5ae52", "#d879a8", "#6ab89d"]
px.defaults.color_continuous_scale = ["#d9d5ff", "#9382f4", "#4ccbd2", "#236c9b"]
px.defaults.template = go.layout.Template(layout=go.Layout(
    font=dict(family="DM Sans, sans-serif", color=plot_text),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=True, gridcolor=plot_grid, zerolinecolor=plot_grid, linecolor=plot_grid),
    yaxis=dict(showgrid=True, gridcolor=plot_grid, zerolinecolor=plot_grid, linecolor=plot_grid),
    colorway=["#7664e8", "#36bfc9", "#4f91df", "#e5ae52", "#d879a8", "#6ab89d"],
))

if st.session_state.density == "Compact":
    st.markdown("<style>.block-container{padding-top:.8rem;padding-bottom:2rem}[data-testid='stMetric']{min-height:84px;padding:10px 13px}.card,.insight{padding:12px 14px;margin-bottom:7px}</style>", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────
def read_upload(upload, sheet_name=None):
    name = upload.name.lower()
    payload = upload.getvalue()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        book = pd.ExcelFile(BytesIO(payload))
        selected = sheet_name if sheet_name in book.sheet_names else book.sheet_names[0]
        return pd.read_excel(BytesIO(payload), sheet_name=selected), book.sheet_names
    if name.endswith(".json"):
        try:
            parsed = json.loads(payload.decode("utf-8-sig"))
            if isinstance(parsed, dict):
                for key in ("data", "records", "results", "items"):
                    if isinstance(parsed.get(key), list):
                        parsed = parsed[key]
                        break
            return pd.json_normalize(parsed), []
        except Exception:
            return pd.read_json(BytesIO(payload)), []
    if name.endswith(".tsv"):
        return pd.read_csv(BytesIO(payload), sep="\t", encoding="utf-8-sig"), []
    try:
        sample = payload[:8192].decode("utf-8-sig")
        encoding = "utf-8-sig"
    except UnicodeDecodeError:
        sample = payload[:8192].decode("latin-1")
        encoding = "latin-1"
    delimiter = detect_delimiter(sample)
    return pd.read_csv(BytesIO(payload), sep=delimiter, encoding=encoding), []

def fmt(value, decimals=None):
    decimals = st.session_state.get("precision", 2) if decimals is None else decimals
    if value is None or pd.isna(value):
        return "—"
    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)

def make_profile(frame):
    return profile_dataset(frame)

def safe_corr(a, b):
    pair = pd.DataFrame({"a": a, "b": b}).dropna()
    if len(pair) < 3 or pair["a"].nunique() < 2 or pair["b"].nunique() < 2:
        return None, len(pair)
    return float(pair["a"].corr(pair["b"])), len(pair)

def recommend_chart(frame, numeric, categorical, dates):
    if dates and numeric:
        return "Time trend", "A date field and numeric measure support a time trend."
    if categorical and numeric:
        return "Ranked comparison", "A category and numeric measure support group comparison."
    if len(numeric) >= 2:
        return "Relationship scatter", "Two numeric measures support a relationship view."
    if numeric:
        return "Distribution", "A numeric measure supports a distribution view."
    return "Category frequency", "Categorical fields support frequency and composition analysis."

def to_html_report(title, filename, profile, frame, filtered, findings, workspace, include_method_notes=True, precision=2, next_questions=None, filters=None):
    report = build_report_data(
        frame, filtered, profile.numeric_columns, profile.columns, profile.quality,
        findings, next_questions or [], filters or {},
        title=title, dataset=filename, domain=profile.dataset_kind,
        workspace=workspace, precision=precision,
    )
    return render_html_report(report, include_method_notes=include_method_notes)


def excel_export(frame, profile, filtered, report=None):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name="Analyzed data", index=False)
        filtered.to_excel(writer, sheet_name="Filtered data", index=False)
        if report is None:
            pd.DataFrame(profile.columns).to_excel(writer, sheet_name="Field profile", index=False)
            pd.DataFrame(profile.insights).to_excel(writer, sheet_name="Findings", index=False)
        else:
            for sheet_name, table in report_workbook_sheets(report).items():
                table.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return output.getvalue()

# ── Sidebar shell ───────────────────────────────────────────────────────────
with st.sidebar:
    brand_icon, brand_text = st.columns([1, 3])
    with brand_icon:
        logo_upload = st.session_state.get("workspace_logo_upload")
        if logo_upload is not None:
            st.image(logo_upload.getvalue(), width=42)
        else:
            st.markdown(f'<div class="brandmark">{escape(st.session_state.workspace_mark[:3])}</div>', unsafe_allow_html=True)
    with brand_text:
        st.markdown('<div class="brandname">DataPilot AI</div><div class="brandtag">INTELLIGENCE STUDIO</div>', unsafe_allow_html=True)
    st.caption(escape(st.session_state.get("workspace_subtitle", "YOUR DATA. UNDERSTOOD.")))
    st.markdown("---")
    page = st.radio(
        "WORKSPACE",
        ["Overview", "Analysis Studio", "Data Explorer", "Reports", "Settings"],
        key="nav_page",
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**WORKSPACE STATUS**")
    st.caption("Your dataset and analysis stay in this active app session.")
    st.markdown("---")
    st.markdown("**WORKSPACE**")
    st.caption(st.session_state.workspace_name)
    st.caption("Session workspace · preferences are not synced to an account")

# ── Welcome / no-data state ─────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
 <div class="eyebrow">ADAPTIVE DATA INTELLIGENCE · {st.session_state.workspace_name.upper()}</div>
 <h1>Make your data make sense.</h1>
 <p>Explore the signals, compare what matters, understand data quality, and turn evidence into your next question — with analysis shaped around the file you bring.</p>
 <div class="hero-meta">DISCOVER &nbsp;·&nbsp; INVESTIGATE &nbsp;·&nbsp; EXPLAIN &nbsp;·&nbsp; DECIDE</div>
</div>
""", unsafe_allow_html=True)

# Primary upload action belongs in the workspace, not hidden in the sidebar.
upload_left, upload_right = st.columns([1.35, .65], gap="large")
with upload_left:
    st.markdown("""
    <div class="upload-panel">
      <div class="kicker">START YOUR ANALYSIS</div>
      <h2 style="margin:5px 0 7px">Bring your dataset into DataPilot</h2>
      <p class="subtle" style="margin:0">Drop a file here or browse your device. Your original values remain the source of truth.</p>
    </div>
    """, unsafe_allow_html=True)
    upload = st.file_uploader(
        "Choose a dataset",
        type=["csv", "tsv", "xlsx", "xls", "json"],
        help="Supported formats: CSV, TSV, Excel and JSON",
        key="workspace_dataset_upload",
        label_visibility="collapsed",
    )
with upload_right:
    st.markdown("""
    <div class="upload-guidance">
      <div class="card-label">SUPPORTED FORMATS</div>
      <div class="format-list"><span>CSV</span><span>TSV</span><span>XLSX</span><span>XLS</span><span>JSON</span></div>
      <div class="sectionline"></div>
      <div class="card-label">YOUR DATA</div>
      <p class="card-copy">Files are processed in this active app session. Avoid uploading sensitive personal or confidential data.</p>
      <p class="card-copy">No account, cloud project or external AI processing is implied.</p>
    </div>
    """, unsafe_allow_html=True)
if upload is not None:
    st.markdown(
        f'<div class="loaded-dataset"><span class="loaded-dot"></span><div><strong>{escape(upload.name)}</strong><div class="subtle">Dataset ready · processed in this session</div></div></div>',
        unsafe_allow_html=True,
    )

if upload is None:
    if page == "Settings":
        st.markdown("## Workspace settings")
        st.caption("These controls customize this active browser session. They do not create an account or persist across sessions.")
        st.text_input("Workspace name", key="workspace_name", max_chars=48)
        st.selectbox("Appearance", ["Light", "Dark"], key="theme_mode")
        st.selectbox("Interface density", ["Comfortable", "Compact"], key="density")
        st.info("Workspace branding and interface preferences are session-local in this release. Persistent user accounts and cloud-saved settings are not implemented.")
    else:
        left, right = st.columns([1.15, .85], gap="large")
        with left:
            st.markdown("## An analysis that adapts to your file")
            st.write("Upload a dataset and DataPilot will profile its fields, check data quality, identify useful comparisons, and recommend a starting analysis. You stay in control of the definitions and calculations.")
            st.markdown('<div class="card"><div class="card-label">THE PRODUCT PRINCIPLE</div><div class="card-title">Your schema comes first.</div><div class="card-copy">A sales export, a customer table, an operations log and a workforce dataset should not receive the same canned dashboard. The detected structure shapes the available analysis.</div></div>', unsafe_allow_html=True)
        with right:
            st.markdown("### Your analysis journey")
            for n, title, detail in [
                ("01", "Understand", "Detect fields, roles, dates, measures and categories."),
                ("02", "Validate", "Review missingness, duplicates, unusual values and assumptions."),
                ("03", "Investigate", "Filter, compare, drill into records and inspect relationships."),
                ("04", "Communicate", "Create a clear report with evidence, limitations and next steps."),
            ]:
                st.markdown(f'<div class="card" style="margin-bottom:10px"><div class="card-label">{n}</div><div class="card-title">{title}</div><div class="card-copy">{detail}</div></div>', unsafe_allow_html=True)
        st.markdown("### Designed for different kinds of data")
        cols = st.columns(4)
        for col, name, desc in zip(cols, ["Commerce", "Customers", "Operations", "People & more"], ["Orders, products and transactions", "Segments, cohorts and activity", "Events, metrics and time series", "Workforce and general tabular data"]):
            with col:
                st.markdown(f'<div class="card"><div class="card-title">{name}</div><div class="card-copy">{desc}</div></div>', unsafe_allow_html=True)
    st.stop()

if upload is not None:
    # ── Load and profile ───────────────────────────────────────────────────────
    try:
        sheet_names = []
        chosen_sheet = None
        if upload.name.lower().endswith((".xlsx", ".xls")):
            book = pd.ExcelFile(BytesIO(upload.getvalue()))
            sheet_names = book.sheet_names
            if "selected_sheet" not in st.session_state or st.session_state.selected_sheet not in sheet_names:
                st.session_state.selected_sheet = sheet_names[0]
            chosen_sheet = st.session_state.selected_sheet
        raw, _ = read_upload(upload, chosen_sheet)
        raw.columns = [str(c).strip() or f"unnamed_{i+1}" for i, c in enumerate(raw.columns)]
        if raw.empty:
            st.error("This file contains no data rows. Check the header row and selected sheet.")
            st.stop()
        if sheet_names:
            chosen_sheet = st.sidebar.selectbox("Excel worksheet", sheet_names, index=sheet_names.index(chosen_sheet), key="selected_sheet")
            if chosen_sheet != st.session_state.get("_loaded_sheet"):
                raw, _ = read_upload(upload, chosen_sheet)
                st.session_state["_loaded_sheet"] = chosen_sheet
        profile = make_profile(raw)
        semantic_by_column = {item["column"]: item for item in infer_semantic_fields(raw)}
        for field_meta in profile.columns:
            field_meta.update(semantic_by_column.get(field_meta["column"], {}))
    except Exception as exc:
        st.error(f"DataPilot could not read this file: {exc}")
        st.info("Check the file format, headers, worksheet and encoding. If it is a nested JSON export, try exporting it as a flat table.")
        st.stop()

    # Optional semantic role review; the raw file remains untouched.
    with st.sidebar:
        with st.expander("Review detected field roles", expanded=False):
            role_options = ["Automatic", "Measure", "Category", "Date / time", "Identifier"]
            for row in profile.columns:
                colname = row["column"]
                current = st.session_state.role_overrides.get(colname, "Automatic")
                st.selectbox(colname, role_options, index=role_options.index(current), key=f"role_{colname}",
                             on_change=lambda c=colname: st.session_state.role_overrides.update({c: st.session_state[f"role_{c}"]}))

    # Rebuild role lists from the user's explicit overrides. Parsing is conservative.
    numeric_cols, category_cols, date_cols, id_cols = [], [], [], []
    data = profile.data.copy()
    for meta in profile.columns:
        col = meta["column"]
        override = st.session_state.role_overrides.get(col, "Automatic")
        if override == "Automatic":
            role = meta["role"]
        else:
            role = override
            meta["role"] = f"{override} · user override"
        if role == "Measure":
            converted = pd.to_numeric(data[col], errors="coerce")
            if converted.notna().any():
                data[col] = converted
                numeric_cols.append(col)
            else:
                category_cols.append(col)
        elif role == "Date / time":
            converted = pd.to_datetime(data[col], errors="coerce", format="mixed")
            if converted.notna().any():
                data[col] = converted
                date_cols.append(col)
            else:
                category_cols.append(col)
        elif role == "Identifier":
            id_cols.append(col)
            category_cols.append(col)
        elif role == "Category":
            category_cols.append(col)
        elif role == "Numeric measure":
            numeric_cols.append(col)
        elif role == "Date / time":
            date_cols.append(col)
        elif "Identifier" in role or "Category" in role:
            category_cols.append(col)
        else:
            category_cols.append(col)

    numeric_cols = list(dict.fromkeys(numeric_cols))
    category_cols = list(dict.fromkeys(category_cols))
    date_cols = list(dict.fromkeys(date_cols))
    id_cols = list(dict.fromkeys(id_cols))

    # Domain lens is inferred from schema evidence and can be corrected by the user.
    domain_options = ["Automatic", "Sales & commerce", "Customer & audience", "People & workforce", "Finance & accounting", "Marketing & acquisition", "Operations & service", "General / mixed data"]
    if "domain_override" not in st.session_state:
        st.session_state["domain_override"] = "Automatic"
    selected_domain_override = st.sidebar.selectbox(
        "Dataset domain lens",
        domain_options,
        key="domain_override",
        help="Automatic uses column-name and field-role evidence. You can override the lens; unavailable templates remain disabled.",
    )
    domain_assessment = assess_domain(
        data,
        profile.columns,
        numeric_cols,
        category_cols,
        date_cols,
        override=selected_domain_override,
    )
    profile.dataset_kind = domain_assessment["domain"]

    # Build a profile view that respects role corrections.
    profile.numeric_columns = numeric_cols
    profile.categorical_columns = category_cols
    profile.date_columns = date_cols
    profile.data = data
    profile.insights = build_evidence_findings(data, numeric_cols, category_cols, date_cols)
    recommendation, recommendation_reason = recommend_visualization(numeric_cols, category_cols, date_cols)

    # Global filters apply across every workspace page.
    st.sidebar.markdown("---")
    st.sidebar.markdown("**GLOBAL FILTERS**")
    filtered = data.copy()
    with st.sidebar.expander("Filter this dataset", expanded=False):
        filterable = category_cols[:12]
        for col in filterable:
            unique = data[col].dropna().astype(str).unique().tolist()
            if 1 < len(unique) <= 150:
                selected = st.multiselect(col, unique, default=st.session_state.active_filters.get(col, []), key=f"global_filter_{col}")
                st.session_state.active_filters[col] = selected
                if selected:
                    filtered = filtered[filtered[col].astype(str).isin(selected)]
            elif len(unique) > 150:
                st.caption(f"{col}: {len(unique):,} values — use Data Explorer search.")
    st.sidebar.caption(f"{len(filtered):,} / {len(data):,} rows in current view")
    if st.sidebar.button("Clear all filters", use_container_width=True):
        st.session_state.active_filters = {}
        for field in filterable:
            st.session_state.pop(f"global_filter_{field}", None)
        st.rerun()

    # Recalculate and prioritize findings against the active global filter.
    raw_findings = build_evidence_findings(filtered, numeric_cols, category_cols, date_cols)
    profile.insights = rank_findings(raw_findings, row_count=len(filtered), limit=20)
    next_questions = build_next_questions(
        domain_assessment["domain"], numeric_cols, category_cols, date_cols, limit=4
    )

    # Common source context header
    st.markdown(f'<div class="pagehead"><div><div class="kicker">{profile.dataset_kind} · DATASET PROFILE</div><h2 style="margin:3px 0">{upload.name}</h2><div class="subtle">{len(data):,} rows · {len(data.columns):,} fields · recommended starting point: {recommendation}</div></div><span class="pill">LIVE SESSION</span></div>', unsafe_allow_html=True)

    # ── Overview ───────────────────────────────────────────────────────────────
    if page == "Overview":
        st.markdown("""
        <div class="overview-intro">
          <div>
            <div class="kicker">YOUR INTELLIGENCE BRIEF</div>
            <h2 style="margin:4px 0 5px">What is happening in this dataset?</h2>
            <p class="subtle" style="margin:0">A live view of the evidence detected, the quality of your data, and where to investigate next.</p>
          </div>
          <div class="overview-live"><span></span> ANALYSIS READY</div>
        </div>
        """, unsafe_allow_html=True)

        total_cells = max(1, int(data.size))
        missing_cells = int(data.isna().sum().sum())
        completeness = max(0.0, min(100.0, (1 - missing_cells / total_cells) * 100))
        active_rows = len(filtered)
        source_rows = len(data)
        duplicate_rows = int(profile.quality["duplicate_rows"])
        signal_count = len(profile.insights)

        metrics = st.columns(4, gap="medium")
        metrics[0].metric("Records in view", f"{active_rows:,}", f"{source_rows-active_rows:,} excluded by filters")
        metrics[1].metric("Data completeness", f"{completeness:.1f}%", f"{missing_cells:,} missing cells")
        metrics[2].metric("Priority signals", f"{signal_count:,}", "Ranked review opportunities")
        metrics[3].metric("Exact duplicates", f"{duplicate_rows:,}", "Review before removing")

        st.markdown('<div class="sectionline"></div>', unsafe_allow_html=True)
        main_col, side_col = st.columns([1.35, .85], gap="large")

        with main_col:
            st.markdown("### Priority signals")
            st.caption("Ranked by finding type and available sample support. Scores organize review order; they are not probabilities or significance tests.")
            if profile.insights:
                for index, item in enumerate(profile.insights[:4], start=1):
                    kind = escape(str(item.get("kind", "observation")).upper())
                    title = escape(str(item.get("title", "Untitled observation")))
                    detail = escape(str(item.get("detail", "")))
                    next_step = escape(str(item.get("next_step", item.get("action", "Inspect the supporting records"))))
                    evidence_level = escape(str(item.get("evidence_level", "Exploratory")))
                    priority_score = item.get("priority_score")
                    score_label = f"{int(priority_score)}/100 review score" if isinstance(priority_score, (int, float)) else "Review priority"
                    sample_label = escape(str(item.get("sample_label", "Not stated")))
                    priority_reason = escape(str(item.get("priority_reason", "")))
                    st.markdown(
                        f'<div class="signal-card"><div class="signal-top"><span class="signal-index">{index:02d}</span><span class="signal-kind">{kind}</span></div><div class="signal-title">{title}</div><p>{detail}</p><div class="signal-next">NEXT STEP · {next_step}</div><div class="signal-meta"><span>{evidence_level}</span><span>{score_label}</span><span>Sample: {sample_label}</span></div><p class="subtle">{priority_reason}</p></div>',
                        unsafe_allow_html=True,
                    )
                    st.button("Investigate this signal", key=f"investigate_signal_{index}", on_click=investigate_signal, args=(item,))
                st.button("Open full Analysis Studio", type="primary", key="overview_investigate_signals", on_click=go_to_page, args=("Analysis Studio",))
            else:
                st.markdown('<div class="empty"><strong>No strong automatic signals yet.</strong><p>Start with a field or data-quality review, then choose a question in Analysis Studio.</p></div>', unsafe_allow_html=True)
                st.button("Open Analysis Studio", type="primary", key="overview_empty_studio", on_click=go_to_page, args=("Analysis Studio",))

            st.markdown("### Explore the shape of your data")
            chart_left, chart_right = st.columns(2, gap="medium")
            with chart_left:
                if category_cols:
                    category_field = st.selectbox("Category snapshot", category_cols, key="overview_category_field")
                    category_data = category_summary(filtered[category_field], top_n=7).rename(columns={"category": category_field})
                    fig = px.bar(category_data.sort_values("records"), x="records", y=category_field, orientation="h", color="records", color_continuous_scale=["#c9c2fb", "#7664e8"])
                    fig.update_layout(height=300, margin=dict(t=15,b=15,l=8,r=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
                    st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False}, key="overview_category_chart")
                    st.caption(f"Top categories by record count · {category_field}")
                else:
                    st.markdown('<div class="empty">No category fields are available for a composition snapshot.</div>', unsafe_allow_html=True)
            with chart_right:
                if numeric_cols:
                    measure_field = st.selectbox("Measure snapshot", numeric_cols, key="overview_measure_field")
                    measure_values = pd.to_numeric(filtered[measure_field], errors="coerce").replace([float("inf"), float("-inf")], pd.NA).dropna()
                    if len(measure_values):
                        measure_frame = pd.DataFrame({measure_field: measure_values})
                        fig = px.histogram(measure_frame, x=measure_field, nbins=24, color_discrete_sequence=["#21b8b2"])
                        fig.update_layout(height=300, margin=dict(t=15,b=15,l=8,r=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False}, key="overview_measure_chart")
                        st.caption(f"Observed distribution · {len(measure_values):,} valid values")
                    else:
                        st.info("No valid numeric values remain under the active filters.")
                else:
                    st.markdown('<div class="empty">No numeric measures are available for a distribution snapshot.</div>', unsafe_allow_html=True)

        with side_col:
            st.markdown("### Data health")
            st.markdown(f'<div class="health-card"><div class="health-heading"><span>Completeness</span><strong>{completeness:.1f}%</strong></div><div class="health-track"><span style="width:{completeness:.1f}%"></span></div><div class="health-foot">{missing_cells:,} missing of {total_cells:,} cells in the source table</div></div>', unsafe_allow_html=True)
            health_items = [
                ("Rows", f"{source_rows:,}", "Source records"),
                ("Fields", f"{len(data.columns):,}", "Detected columns"),
                ("Measures", f"{len(numeric_cols):,}", "Numeric fields"),
                ("Date fields", f"{len(date_cols):,}", "Recognized time fields"),
                ("Constant fields", f"{len(profile.quality['constant_columns']):,}", "Fields with one distinct value"),
            ]
            for label, value, note in health_items:
                st.markdown(f'<div class="health-row"><div><strong>{label}</strong><span>{note}</span></div><b>{value}</b></div>', unsafe_allow_html=True)

            st.markdown("### Dataset understanding")
            st.markdown(f'<div class="domain-card"><div class="card-label">DETECTED DATA LENS</div><div class="card-title">{escape(str(domain_assessment["domain"]))}</div><div class="card-copy">{escape(str(domain_assessment["description"]))}</div></div>', unsafe_allow_html=True)
            if domain_assessment["is_overridden"]:
                st.caption(f"Manually selected lens · automatic assessment: {domain_assessment['automatic_domain']}.")
            elif domain_assessment["confidence"]:
                st.caption(f"Schema evidence score: {domain_assessment['confidence']}% (not a statistical probability).")
            else:
                st.caption("No specialist domain had enough independent field-name evidence.")

            st.markdown("### Questions worth exploring")
            if next_questions:
                for question in next_questions[:3]:
                    st.markdown(f'<div class="next-step"><strong>{escape(str(question["question"]))}</strong><p>{escape(str(question["why"]))}</p><span>Fields: {escape(str(question["fields"]))}</span></div>', unsafe_allow_html=True)
            else:
                st.info("No focused question can be suggested until usable measure, category or date fields are identified.")

            st.markdown("### Available playbooks")
            available_templates = [item for item in domain_assessment["templates"] if item["available"]]
            if available_templates:
                for template in available_templates[:2]:
                    st.markdown(f'<div class="next-step"><strong>{escape(str(template["title"]))}</strong><p>{escape(str(template["question"]))}</p><span>Fields: {escape(", ".join(template["required_fields"]) or "Review schema")}</span></div>', unsafe_allow_html=True)
                st.button("Build an analysis", type="primary", use_container_width=True, key="overview_build_analysis", on_click=go_to_page, args=("Analysis Studio",))
            else:
                st.info("Review detected field roles to unlock a suitable starting analysis.")

        st.markdown('<div class="sectionline"></div>', unsafe_allow_html=True)
        footer_left, footer_right = st.columns([1, 1], gap="large")
        with footer_left:
            st.markdown("**Need the exact source records?**")
            st.caption("Open Data Explorer to search rows, review field roles and trace values back to the uploaded file.")
            st.button("Open Data Explorer", key="overview_open_explorer", on_click=go_to_page, args=("Data Explorer",))
        with footer_right:
            st.markdown("**Ready to share what you found?**")
            st.caption("Create a portable report from the current data and filter state. HTML, Excel and JSON exports are available.")
            st.button("Create a report", key="overview_open_reports", on_click=go_to_page, args=("Reports",))

        st.caption("All observations are computed from the uploaded dataset and active filters. Priority scores organize review order; they do not establish probability, causality, forecasts or business outcomes.")

    # ── Analysis Studio ────────────────────────────────────────────────────────
    elif page == "Analysis Studio":
        st.markdown("## Analysis Studio")
        st.caption("Choose the question, dimensions, measures and method. All views use the active global filters.")
        selected_signal = st.session_state.get("selected_signal")
        if selected_signal:
            st.markdown(f'<div class="signal-card"><div class="signal-kind">INVESTIGATION CONTEXT · {escape(selected_signal["kind"].upper())}</div><div class="signal-title">{escape(selected_signal["title"])}</div><p>{escape(selected_signal["detail"])}</p><div class="signal-next">SUGGESTED NEXT STEP · {escape(selected_signal["next_step"])}</div></div>', unsafe_allow_html=True)
            if st.button("Clear investigation context", key="clear_selected_signal"):
                st.session_state.pop("selected_signal", None)
                st.rerun()
        if not numeric_cols and not category_cols and not date_cols:
            st.warning("No analyzable fields were detected. Review field roles in the sidebar.")
        mode_options = ["Compare groups", "Time trend", "Distribution", "Relationship", "Category composition"]
        recommended_mode = {"Ranked comparison":"Compare groups","Time trend":"Time trend","Distribution":"Distribution","Relationship scatter":"Relationship","Category frequency":"Category composition"}.get(recommendation, "Compare groups")
        configured_mode = st.session_state.get("chart_type", "Recommended")
        default_mode = configured_mode if configured_mode in mode_options else recommended_mode
        mode = st.segmented_control("Analysis type", mode_options, default=default_mode, key="studio_mode")
        mode = mode or default_mode
        if mode == "Compare groups":
            if numeric_cols and category_cols:
                a,b,c = st.columns([1.15,1.15,.9])
                with a: dimension = st.selectbox("Dimension", category_cols, key="cmp_dimension")
                with b: measure = st.selectbox("Measure", numeric_cols, key="cmp_measure")
                with c: agg = st.selectbox("Aggregation", ["sum","mean","median","min","max","count"], key="cmp_agg")
                limit = st.slider("Show groups", 3, 50, int(st.session_state.get("default_top_n", 12)), key="cmp_limit")
                summary = grouped_summary(filtered, dimension, measure, agg).head(limit)
                if summary.empty:
                    st.info("No rows remain for this comparison. Adjust the global filters.")
                else:
                    chart = st.selectbox("Chart style", ["Horizontal bars","Vertical bars","Treemap","Box plot"], key="cmp_chart")
                    if chart == "Horizontal bars":
                        fig = px.bar(summary.sort_values("value"), x="value", y=dimension, orientation="h", color="value", color_continuous_scale=["#c7c0fb","#6955e8","#21b8b2"])
                    elif chart == "Vertical bars":
                        fig = px.bar(summary, x=dimension, y="value", color="value", color_continuous_scale=["#c7c0fb","#6955e8","#21b8b2"])
                    elif chart == "Treemap":
                        fig = px.treemap(summary, path=[dimension], values="value", color="value", color_continuous_scale="Tealgrn")
                    else:
                        fig = px.box(filtered, x=dimension, y=measure, points="outliers")
                    fig.update_layout(height=440, margin=dict(t=25,b=20,l=15,r=15), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
                    event = st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False,"scrollZoom":True}, on_select="rerun", selection_mode="points", key="group_comparison_chart")
                    label_fields = {"Horizontal bars": ["y"], "Vertical bars": ["x"], "Treemap": ["label"], "Box plot": ["x"]}[chart]
                    selected_groups = selected_point_values(event, label_fields)
                    if selected_groups:
                        drilldown = filtered[filtered[dimension].astype(str).isin(selected_groups)]
                        st.markdown("### Selected groups · source records")
                        st.caption(f"{len(drilldown):,} source rows from: {', '.join(selected_groups)}")
                        st.dataframe(drilldown.head(500), use_container_width=True, hide_index=True)
                        st.download_button("Download selected source rows", drilldown.to_csv(index=False).encode("utf-8-sig"), "datapilot_selected_groups.csv", "text/csv", key="download_selected_groups")
                    else:
                        st.caption("Select one or more marks in the chart to inspect their exact source records.")
                    top = summary.iloc[0]
                    total = summary["value"].sum()
                    share = float(top["value"] / total * 100) if total and agg == "sum" else None
                    st.info(f"Highest {agg} of {measure}: **{top[dimension]}** ({fmt(top['value'])})." + (f" This is {share:.1f}% of the displayed total." if share is not None else ""))
                    st.markdown("### Exact values")
                    st.dataframe(summary, use_container_width=True, hide_index=True)
                    st.download_button("Download comparison (CSV)", summary.to_csv(index=False).encode("utf-8-sig"), "datapilot_comparison.csv", "text/csv")
            else:
                st.info("Group comparison requires at least one category/dimension and one numeric measure. Correct field roles in the sidebar if needed.")
        elif mode == "Time trend":
            if date_cols and numeric_cols:
                a,b,c = st.columns(3)
                with a: date_col = st.selectbox("Date field", date_cols)
                with b: measure = st.selectbox("Measure", numeric_cols, key="trend_measure")
                with c: grain = st.selectbox("Time grain", ["Day","Week","Month","Quarter","Year"], index=2)
                agg = st.selectbox("Aggregation", ["sum","mean","median","min","max","count"], key="trend_agg")
                trend = time_summary(filtered, date_col, measure, grain, agg)
                if trend.empty:
                    st.warning("No valid date-and-measure pairs remain after filters.")
                else:
                    fig = build_time_figure(trend)
                    st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False,"scrollZoom":True})

                    # Evidence-led diagnostics: missing periods, broad shifts and abrupt changes.
                    time_result = analyze_time_series(trend)
                    t1, t2, t3 = st.columns(3)
                    t1.metric("Valid periods", f"{time_result['valid_periods']:,}")
                    t2.metric("Missing periods", "Not inferred" if time_result["missing_periods"] is None else f"{time_result['missing_periods']:,}")
                    t3.metric("Comparison checks", "Ready" if time_result["eligible_for_comparison"] else "Limited sample")
                    if time_result["findings"]:
                        st.markdown("### What changed over time")
                        for finding in time_result["findings"]:
                            with st.container(border=True):
                                st.caption(finding["kind"].upper())
                                st.markdown(f"**{finding['title']}**")
                                st.write(finding["detail"])
                                st.caption("Next: " + finding["action"])
                    else:
                        st.info("No material time signal was detected by the current checks. This does not prove the series is stable.")
                    if len(trend) > 1:
                        first, last = float(trend.iloc[0]["value"]), float(trend.iloc[-1]["value"])
                        delta = last-first
                        m1,m2,m3 = st.columns(3)
                        m1.metric("First period", fmt(first))
                        m2.metric("Latest period", fmt(last), fmt(delta) + " vs first")
                        m3.metric("Periods", f"{len(trend):,}")
                    st.dataframe(trend, use_container_width=True, hide_index=True)
                    st.download_button("Download time series (CSV)", trend.to_csv(index=False).encode("utf-8-sig"), "datapilot_time_series.csv", "text/csv")
            else:
                st.info("Time analysis needs one date field and one numeric measure.")
        elif mode == "Distribution":
            if numeric_cols:
                measure = st.selectbox("Measure", numeric_cols, key="dist_field")
                chart = st.selectbox("Distribution view", ["Histogram + box","Violin","ECDF"])
                if chart == "Histogram + box":
                    fig = px.histogram(filtered, x=measure, marginal="box", nbins=40, color_discrete_sequence=["#6955e8"])
                elif chart == "Violin":
                    fig = px.violin(filtered, y=measure, box=True, points="outliers", color_discrete_sequence=["#21b8b2"])
                else:
                    fig = px.ecdf(filtered, x=measure, color_discrete_sequence=["#6955e8"])
                fig.update_layout(height=430, margin=dict(t=25,b=20,l=15,r=15), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False})
                s = pd.to_numeric(filtered[measure], errors="coerce").dropna()
                if len(s):
                    stats = numeric_summary(s)
                    m = st.columns(5)
                    for col, label, value in zip(m, ["Count","Mean","Median","IQR outliers","90th percentile"], [stats["count"],stats["mean"],stats["median"],stats["iqr_outliers"],stats["p90"]]):
                        col.metric(label, fmt(value))
                    st.caption("Statistics are calculated after global filters. Standard deviation is sample-based.")
            else:
                st.info("No numeric measures are available. Review detected field roles.")
        elif mode == "Relationship":
            if len(numeric_cols) >= 2:
                a,b = st.columns(2)
                with a: x = st.selectbox("X measure", numeric_cols, key="rel_x")
                with b: y = st.selectbox("Y measure", [v for v in numeric_cols if v != x], key="rel_y")
                color_options = ["None"] + category_cols
                color = st.selectbox("Color by dimension (optional)", color_options)
                plot_data = filtered.copy()
                plot_data[x] = pd.to_numeric(plot_data[x], errors="coerce")
                plot_data[y] = pd.to_numeric(plot_data[y], errors="coerce")
                plot_data = plot_data.dropna(subset=[x,y])
                if color != "None":
                    fig = px.scatter(plot_data, x=x, y=y, color=color, opacity=.75)
                else:
                    fig = px.scatter(plot_data, x=x, y=y, opacity=.75, color_discrete_sequence=["#6955e8"])
                fig.update_traces(marker={"size":9,"line":{"width":1,"color":"white"}})
                fig.update_layout(height=450, hovermode="closest", margin=dict(t=25,b=20,l=15,r=15), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                plot_data = plot_data.reset_index(drop=True)
                event = st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False,"scrollZoom":True}, on_select="rerun", selection_mode="points", key="relationship_scatter_chart")
                selected_indices = [i for i in selected_point_indices(event) if i < len(plot_data)]
                if selected_indices:
                    selected_rows = plot_data.iloc[selected_indices]
                    st.markdown("### Selected points · source records")
                    st.dataframe(selected_rows, use_container_width=True, hide_index=True)
                    st.download_button("Download selected points", selected_rows.to_csv(index=False).encode("utf-8-sig"), "datapilot_selected_points.csv", "text/csv", key="download_selected_points")
                else:
                    st.caption("Select scatter points to inspect the matching source rows.")
                corr, n = safe_correlation(plot_data, x, y)
                if corr is not None:
                    st.metric("Pearson correlation", f"{corr:.3f}", f"{n:,} paired observations")
                    st.caption("Correlation describes linear association, not causation. Inspect the scatter plot for clusters and influential observations.")
            else:
                st.info("Relationship analysis requires at least two numeric measures.")
        elif mode == "Category composition":
            if category_cols:
                dim = st.selectbox("Category field", category_cols)
                counts = category_summary(filtered[dim], top_n=20).rename(columns={"category": dim})
                chart = st.selectbox("Composition view", ["Donut","Treemap","Bar"])
                if chart == "Donut":
                    fig = px.pie(counts, names=dim, values="records", hole=.58)
                elif chart == "Treemap":
                    fig = px.treemap(counts, path=[dim], values="records", color="records", color_continuous_scale="Tealgrn")
                else:
                    fig = px.bar(counts.sort_values("records"), x="records", y=dim, orientation="h", color="records", color_continuous_scale=["#c7c0fb","#6955e8"])
                fig.update_layout(height=430, margin=dict(t=20,b=20,l=10,r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
                event = st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False}, on_select="rerun", selection_mode="points", key="category_composition_chart")
                fields = ["label"] if chart in ["Donut","Treemap"] else ["y"]
                selected_categories = selected_point_values(event, fields)
                if selected_categories:
                    selected_rows = filtered[filtered[dim].astype(str).isin(selected_categories)]
                    st.markdown("### Selected categories · source records")
                    st.caption(f"{len(selected_rows):,} matching source rows")
                    st.dataframe(selected_rows.head(500), use_container_width=True, hide_index=True)
                    st.download_button("Download selected category rows", selected_rows.to_csv(index=False).encode("utf-8-sig"), "datapilot_selected_categories.csv", "text/csv", key="download_selected_categories")
                else:
                    st.caption("Select a chart segment to drill into its source records.")
                st.dataframe(counts, use_container_width=True, hide_index=True)
            else:
                st.info("No category or identifier fields are available.")

    # ── Data Explorer ──────────────────────────────────────────────────────────
    elif page == "Data Explorer":
        st.markdown("## Data Explorer")
        st.caption("Inspect source records, search values, understand field roles and trace every filtered result back to rows.")
        a,b,c = st.columns([1.2,1,1])
        with a: search = st.text_input("Search across text fields", placeholder="Type a value, label or identifier…")
        with b: selected_columns = st.multiselect("Visible columns", list(data.columns), default=list(data.columns[:min(12,len(data.columns))]))
        with c: row_limit = st.selectbox("Rows per view", [50,100,250,500,1000,5000], index=2)
        view = filtered.copy()
        if search:
            mask = view.astype("string").apply(lambda s: s.str.contains(re.escape(search), case=False, na=False, regex=True)).any(axis=1)
            view = view[mask]
        if selected_columns:
            view = view[selected_columns]
        st.markdown(f"**{len(view):,} matching rows**")
        st.dataframe(view.head(row_limit), use_container_width=True, hide_index=True, height=510)
        st.download_button("Export current view as CSV", view.to_csv(index=False).encode("utf-8-sig"), "datapilot_explorer_view.csv", "text/csv")
        st.markdown("### Field dictionary")
        dictionary = pd.DataFrame(profile.columns)
        st.dataframe(dictionary, use_container_width=True, hide_index=True)
        st.markdown("### Field spotlight")
        spotlight_field = st.selectbox("Explore a field", list(data.columns), key="explorer_spotlight_field")
        spotlight = data[spotlight_field]
        valid = spotlight.dropna()
        s1, s2, s3 = st.columns(3)
        s1.metric("Non-empty values", f"{len(valid):,}", f"{len(valid) / max(1, len(data)) * 100:.1f}% of rows")
        s2.metric("Unique values", f"{spotlight.nunique(dropna=True):,}")
        s3.metric("Missing values", f"{int(spotlight.isna().sum()):,}")
        if spotlight_field in numeric_cols:
            numeric_values = pd.to_numeric(spotlight, errors="coerce").dropna()
            if not numeric_values.empty:
                spotlight_fig = px.histogram(
                    x=numeric_values, nbins=36,
                    color_discrete_sequence=["#7664e8"],
                    labels={"x": spotlight_field, "count": "Records"},
                )
                spotlight_fig.update_traces(marker_line_width=0, opacity=.88)
                spotlight_fig.update_layout(height=310, margin=dict(t=20,b=24,l=12,r=12), bargap=.08)
                st.plotly_chart(spotlight_fig, use_container_width=True, config={"displaylogo":False})
                st.caption(f"Range {fmt(numeric_values.min())} to {fmt(numeric_values.max())} · median {fmt(numeric_values.median())}")
        elif spotlight_field in date_cols:
            date_values = pd.to_datetime(spotlight, errors="coerce").dropna()
            if not date_values.empty:
                date_counts = date_values.dt.to_period("M").astype(str).value_counts().sort_index().rename_axis("Period").reset_index(name="Records")
                spotlight_fig = px.area(date_counts, x="Period", y="Records", markers=True, color_discrete_sequence=["#36bfc9"])
                spotlight_fig.update_layout(height=310, margin=dict(t=20,b=24,l=12,r=12))
                st.plotly_chart(spotlight_fig, use_container_width=True, config={"displaylogo":False})
        else:
            counts = spotlight.astype("string").fillna("(Missing)").value_counts().head(14).rename_axis("Value").reset_index(name="Records")
            if not counts.empty:
                spotlight_fig = px.bar(counts.sort_values("Records"), x="Records", y="Value", orientation="h", color="Records", color_continuous_scale=["#c7c0fb","#7664e8","#36bfc9"])
                spotlight_fig.update_layout(height=max(280, len(counts)*27), margin=dict(t=20,b=20,l=12,r=12), coloraxis_showscale=False)
                st.plotly_chart(spotlight_fig, use_container_width=True, config={"displaylogo":False})
        with st.expander("Inspect source rows for this field"):
            if spotlight_field in numeric_cols:
                source_sample = data[data[spotlight_field].isna()]
                st.caption("Rows with missing values in this field." if not source_sample.empty else "No missing values in this field.")
            else:
                source_sample = data[data[spotlight_field].isna()]
                st.caption("Source rows where this field is missing.")
            if not source_sample.empty:
                st.dataframe(source_sample.head(200), use_container_width=True, hide_index=True)
                st.download_button("Download matching source rows", source_sample.to_csv(index=False).encode("utf-8-sig"), "datapilot_field_source_rows.csv", "text/csv", key="download_spotlight_missing_rows")
            else:
                st.success("No missing source rows to inspect for this field.")

        st.markdown("### Missingness map")
        missing = data.isna().mean().mul(100).sort_values(ascending=False)
        missing = missing[missing > 0]
        if len(missing):
            mdf = missing.rename("Missing %").reset_index().rename(columns={"index":"Field"})
            fig = px.bar(mdf, x="Missing %", y="Field", orientation="h", color="Missing %", color_continuous_scale=["#36bfc9","#7664e8","#e5ae52"])
            fig.update_layout(height=max(260,len(mdf)*34), margin=dict(t=10,b=10,l=10,r=10), coloraxis_showscale=False)
            event = st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False}, on_select="rerun", selection_mode="points", key="explorer_missingness_chart")
            selected_fields = selected_point_values(event, ["y"])
            if selected_fields:
                field = selected_fields[0]
                missing_rows = data[data[field].isna()]
                st.markdown(f"**{escape(str(field))}** · {len(missing_rows):,} source rows have missing values")
                if not missing_rows.empty:
                    st.dataframe(missing_rows.head(200), use_container_width=True, hide_index=True)
                    st.download_button("Download rows with missing values", missing_rows.to_csv(index=False).encode("utf-8-sig"), "datapilot_missing_field_rows.csv", "text/csv", key="download_missing_field_rows")
            else:
                st.caption("Select a bar to inspect the exact source rows missing that field.")
        else:
            st.success("All source fields are complete.")

    # ── Reports ─────────────────────────────────────────────────────────────────
    elif page == "Reports":
        st.markdown("## Reports & exports")
        st.caption("Build a portable report from the current data and filter state. Report figures are computed, not generated from invented context.")
        report_title = st.text_input("Report title", value=f"{profile.dataset_kind} analysis")
        report_findings = profile.insights[:12]
        report_data = build_report_data(
            data, filtered, numeric_cols, profile.columns, profile.quality,
            report_findings, next_questions, st.session_state.active_filters,
            title=report_title, dataset=upload.name, domain=profile.dataset_kind,
            workspace=st.session_state.workspace_name,
            precision=st.session_state.get("precision", 2),
        )
        html = render_html_report(report_data, include_method_notes=st.session_state.get("show_method_notes", True))
        x1,x2,x3 = st.columns(3)
        with x1:
            st.download_button("Download executive report (HTML)", html.encode("utf-8"), "datapilot_executive_report.html", "text/html", use_container_width=True, type="primary")
        with x2:
            st.download_button("Download workbook (XLSX)", excel_export(data, profile, filtered, report_data), "datapilot_executive_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with x3:
            st.download_button("Download analysis profile (JSON)", json.dumps(report_data, ensure_ascii=False, indent=2, default=str).encode("utf-8"), "datapilot_executive_report.json", "application/json", use_container_width=True)
        st.markdown("### Executive report preview")
        preview_left, preview_right = st.columns(2)
        with preview_left:
            st.metric("Rows in current view", f"{report_data['filtered_rows']:,}", f"of {report_data['source_rows']:,} source rows")
            st.metric("Missing cells", f"{report_data['quality']['missing_cells']:,}", f"{report_data['quality']['missing_pct']:.1f}% of source cells")
        with preview_right:
            st.metric("Priority findings", f"{len(report_data['findings']):,}")
            st.metric("Follow-up questions", f"{len(report_data['next_questions']):,}")
        st.markdown("#### Key measures")
        if report_data["metrics"]:
            st.dataframe(pd.DataFrame(report_data["metrics"]), use_container_width=True, hide_index=True)
        else:
            st.info("No numeric measures are available for a metric summary.")
        st.markdown("#### Priority findings")
        for item in report_data["findings"][:5]:
            st.markdown(f'<div class="insight"><div class="kind">{item.get("evidence_level", item.get("kind", "Observation"))} · {item.get("priority_score", "—")}/100</div><strong>{item.get("title", "Observation")}</strong><p>{item.get("detail", "")}</p><div class="next">NEXT STEP → {item.get("next_step", item.get("action", ""))}</div></div>', unsafe_allow_html=True)
        st.markdown("#### Workbook contents")
        st.caption("Analyzed data · Filtered data · Executive summary · Key measures · Priority findings · Data quality · Field dictionary · Next questions · Applied filters")
        st.info("HTML is print-friendly and can be saved as PDF from your browser. A native PDF export, scheduled delivery and saved report history are not included yet.")

    # ── Settings ────────────────────────────────────────────────────────────────
    elif page == "Settings":
        st.markdown("## Workspace settings")
        st.caption("Control the current workspace presentation and analysis defaults. These settings are session-local.")
        left,right = st.columns(2, gap="large")
        with left:
            st.markdown("### Identity")
            st.text_input("Workspace name", key="workspace_name", max_chars=48)
            st.text_input("Workspace subtitle", value="ADAPTIVE DATA INTELLIGENCE", key="workspace_subtitle")
            st.markdown("### Appearance")
            st.text_input("Brand mark / initials", key="workspace_mark", max_chars=3)
            if st.session_state.get("workspace_logo_upload") is not None:
                if st.button("Remove workspace logo"):
                    st.session_state.pop("workspace_logo_upload", None)
                    st.rerun()
            st.file_uploader("Workspace logo (PNG/JPG/WebP)", type=["png","jpg","jpeg","webp"], key="workspace_logo_upload")
            st.selectbox("Accent palette", ["Violet","Ocean","Emerald","Amber"], key="accent_palette")
            st.selectbox("Theme", ["Light","Dark"], key="theme_mode")
            st.selectbox("Density", ["Comfortable","Compact"], key="density")
        with right:
            st.markdown("### Analysis defaults")
            st.selectbox("Default analysis view", ["Recommended","Compare groups","Time trend","Distribution","Relationship","Category composition"], key="chart_type", on_change=apply_analysis_defaults)
            st.selectbox("Number precision", [0,1,2,3,4], index=2, key="precision")
            st.selectbox("Default Top N", [5,10,12,20,30,50], index=2, key="default_top_n", on_change=apply_analysis_defaults)
            st.markdown("### Privacy & data handling")
            st.info("Uploads are analyzed in the active app session. This build does not provide account login, persistent cloud projects, shared workspaces or external AI processing.")
            st.checkbox("Show methodology notes in reports", value=True, key="show_method_notes")
        st.markdown("---")
        st.button("Reset workspace preferences", on_click=reset_workspace_preferences)
        st.caption("Persistent identity, custom logo uploads and cross-device settings require an authenticated storage layer; this page does not pretend those backend capabilities exist.")

    st.markdown('<div class="sectionline"></div><div class="subtle">DataPilot AI · Adaptive analysis, transparent calculations and evidence-led exploration. No fabricated causes, forecasts or business assumptions.</div>', unsafe_allow_html=True)
