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
from guided_analysis import available_guided_paths, build_guided_result
from insight_actions import build_action_plan, action_plan_summary, action_plan_frame
from visualizations import build_time_figure
from studio_logic import recommend_visualization, numeric_summary, safe_correlation, category_summary, build_evidence_findings, detect_delimiter, selected_point_values, selected_point_indices
from semantic_engine import infer_semantic_fields
from sample_workspace import build_sample_dataset, SAMPLE_DATASET_NOTICE
from visual_identity import THEME_OPTIONS, THEMES, resolve_theme, build_theme_css, theme_chart_colors, theme_gallery_html
from navigation_state import activate_sample_workspace

st.set_page_config(
    page_title="DataPilot AI — Intelligence Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ──────────────────────────────────────────────────────────
defaults = {
    "workspace_name": "My workspace",
    "theme_mode": "Dark",
    "density": "Comfortable",
    "workspace_mark": "◈",
    "workspace_subtitle": "ADAPTIVE DATA INTELLIGENCE",
    "workspace_logo_upload": None,
    "accent_palette": "Violet",
    "visual_theme": "Automatic · domain aware",
    "precision": 2,
    "default_top_n": 12,
    "show_method_notes": True,
    "nav_page": "Overview",
    "active_filters": {},
    "role_overrides": {},
    "chart_type": "Recommended",
    "use_sample_dataset": False,
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


def start_sample_dataset():
    """Set navigation and sample state before Streamlit rebuilds keyed widgets."""
    activate_sample_workspace(st.session_state)



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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{--ink:#172435;--muted:#697789;--line:#e4e9ef;--surface:#fff;--canvas:#f6f8fa;--accent:#167d83;--accent-soft:#e8f4f3;--navy:#142333}
.stApp{background:var(--canvas);color:var(--ink);font-family:'DM Sans',sans-serif}
.block-container{max-width:1480px;padding:1.65rem 2.5rem 4rem}
h1,h2,h3,h4{font-family:'Manrope',sans-serif!important;letter-spacing:-.025em;color:var(--ink)!important}
h1{font-weight:700!important;font-size:1.9rem!important}h2{font-weight:700!important;font-size:1.35rem!important}h3{font-weight:700!important;font-size:1.05rem!important}
p,li{line-height:1.58}
[data-testid="stSidebar"]{background:#142333;border-right:1px solid #26394a}
[data-testid="stSidebar"] *{color:#e8eef3}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#aab8c5}
[data-testid="stSidebar"] hr{border-color:#304252}
[data-testid="stSidebar"] [role="radiogroup"]{gap:4px}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:8px 10px;border-radius:8px}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:#263d4c;border:1px solid #3b5965}
[data-testid="stSidebar"] [data-testid="stFileUploader"]{background:#1c3040;border:1px dashed #526879;border-radius:10px}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 16px;box-shadow:none;min-height:98px}
[data-testid="stMetricLabel"]{font-size:.76rem;font-weight:600;color:var(--muted)!important}
[data-testid="stMetricValue"]{font-family:'Manrope',sans-serif;font-size:1.55rem;font-weight:700;color:var(--ink)}
.stButton>button,.stDownloadButton>button{border:1px solid #d9e1e8;border-radius:8px;background:#fff;color:#243647;font-weight:600;min-height:2.4rem;transition:background .14s,border-color .14s}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:#8ab9b9;color:#126d73;background:#f4faf9}
button[kind="primary"]{background:#167d83!important;color:#fff!important;border:1px solid #167d83!important}
button[kind="primary"]:hover{background:#116b71!important}
[data-testid="stTabs"] button{font-weight:600}
[data-testid="stTabs"] button[aria-selected="true"]{color:#167d83;border-bottom-color:#167d83}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:9px;overflow:hidden}
[data-testid="stPlotlyChart"]{background:#fff;border:1px solid var(--line);border-radius:10px;padding:5px 5px 0;box-shadow:none}
[data-testid="stExpander"]{background:#fff;border:1px solid var(--line);border-radius:9px}
[data-testid="stAlert"]{border-radius:9px}
[data-testid="stSelectbox"],[data-testid="stMultiSelect"],[data-testid="stTextInput"]{border-radius:8px}
.brand{display:flex;align-items:center;gap:10px;margin:5px 0 16px}
.brandmark{width:36px;height:36px;border-radius:9px;background:#1b8a8d;display:grid;place-items:center;color:#fff;font-size:20px;font-weight:800}
.brandname{font-family:Manrope,sans-serif;font-weight:800;font-size:1.05rem;letter-spacing:-.035em}
.brandtag{font-size:.58rem;letter-spacing:.13em;color:#9fb1bf;font-weight:700}
.hero{position:relative;overflow:hidden;border-radius:13px;padding:24px 27px;background:#172b3b;color:#fff;margin-bottom:20px}
.hero:before{content:none}
.hero .eyebrow{font-size:.67rem;letter-spacing:.13em;color:#9fc9c8;font-weight:700}
.hero h1{color:#fff!important;font-size:1.8rem!important;margin:9px 0 7px}
.hero p{max-width:780px;color:#c3d0d9;font-size:.94rem;margin:0}
.hero-meta{margin-top:16px;color:#9db5c1;font-size:.66rem;font-weight:700;letter-spacing:.12em}
.pagehead{padding:17px 19px;border:1px solid var(--line);border-radius:10px;background:#fff;margin-bottom:18px}
.pagehead h2{margin:0 0 4px}
.dataset-summary{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin:-5px 0 19px;padding:0 2px;color:#718191;font-size:.76rem}
.dataset-summary>span{display:inline-flex;align-items:center;min-height:25px;padding:3px 8px;border:1px solid #e2e9ed;border-radius:5px;background:#fff}
.dataset-summary .dataset-kind{color:#176f73;background:#edf6f5;border-color:#d8e9e7;font-weight:700}
.dataset-summary .dataset-recommendation{border-color:transparent;background:transparent;padding-left:0}
@media(max-width:700px){.workspace-topbar{align-items:flex-start;padding:13px}.workspace-session{display:none}.workspace-filename{font-size:1rem}.dataset-summary{gap:6px}.dataset-summary .dataset-recommendation{flex-basis:100%}}

.kicker,.card-label{font-size:.66rem;letter-spacing:.11em;text-transform:uppercase;color:#718191;font-weight:700}
.subtle,.card-copy{color:#697789;font-size:.88rem}
.card,.insight,.signal-card,.health-card,.domain-card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px 18px;box-shadow:none}
.card-title{font-weight:700;color:#1b2a3a}
.card-copy{margin:6px 0 0;line-height:1.55}
.insight{margin-bottom:10px}
.insight strong{color:#1b2a3a}
.insight p{color:#697789;margin:.35rem 0}
.signal-card{margin:9px 0;padding:16px}
.signal-top{display:flex;justify-content:space-between;gap:12px;align-items:center}
.signal-index,.signal-kind,.pill{display:inline-block;border-radius:5px;padding:3px 7px;background:#edf2f5;color:#536675;font-size:.68rem;font-weight:700}
.signal-title{font-weight:700;color:#1c2c3c;margin:9px 0 5px}
.signal-next{color:#506475;font-size:.88rem}
.signal-meta{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}
.signal-meta span{background:#f0f4f6;color:#637584;border-radius:5px;padding:3px 7px;font-size:.68rem}
.health-card,.domain-card{padding:17px}
.health-heading{display:flex;justify-content:space-between;gap:10px}
.health-heading strong,.health-row strong,.health-row b{color:#213242}
.health-track{height:7px;border-radius:8px;background:#eaf0f2;overflow:hidden}
.health-track>span{display:block;height:100%;background:#23898b;border-radius:8px}
.health-foot,.health-row span{color:#72818e;font-size:.78rem}
.health-row{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-bottom:1px solid #edf1f4}
.next-step{background:#f1f6f6;border:1px solid #dcebea;border-radius:9px;padding:12px 14px}
.next-step strong{color:#1d4d50}
.sectionline{height:1px;background:#e5ebef;margin:13px 0}
.upload-panel{background:#fff;border:1px solid var(--line);border-radius:12px;padding:19px 21px 10px}
.upload-panel h2{margin:5px 0 7px}
.upload-guidance{background:#fff;border:1px solid var(--line);border-radius:12px;padding:20px;height:100%}
.format-list{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.format-list span{background:#f0f4f6;border:1px solid #e2e9ed;color:#4c6271;border-radius:5px;padding:4px 8px;font-size:.7rem;font-weight:700}
.loaded-dataset{display:flex;align-items:center;gap:11px;background:#edf7f5;border:1px solid #cfe6df;border-radius:9px;padding:11px 14px;margin:10px 0 18px}
.workspace-topbar{min-height:88px;display:flex;align-items:center;justify-content:space-between;gap:18px;background:#fff;border:1px solid var(--line);border-radius:11px;padding:15px 19px;margin:0 0 18px}
.workspace-filename{font-family:Manrope,sans-serif;font-size:1.12rem;font-weight:750;letter-spacing:-.025em;color:var(--ink);margin-top:3px;overflow-wrap:anywhere}
.workspace-detail{display:flex;align-items:center;gap:7px;color:var(--muted);font-size:.78rem;margin-top:4px}
.status-dot{width:7px;height:7px;border-radius:50%;background:#258b72;display:inline-block}
.workspace-session{font-size:.65rem;font-weight:700;letter-spacing:.1em;color:#637584;background:#f1f5f7;border:1px solid #e2e9ed;border-radius:6px;padding:6px 9px;white-space:nowrap}
.replace-label{font-size:.66rem;font-weight:700;letter-spacing:.1em;color:#718191;margin:2px 0 6px}

.loaded-dot{width:8px;height:8px;border-radius:50%;background:#258b72}
.overview-intro{color:#617282}
.overview-live{display:inline-block;background:#eaf5f2;color:#24745f;border:1px solid #d3e9e1;border-radius:5px;padding:4px 8px;font-size:.68rem;font-weight:700}
.empty{border:1px dashed #cbd6dd;border-radius:10px;padding:24px;text-align:center;color:#738391}
:focus-visible{outline:3px solid rgba(22,125,131,.45)!important;outline-offset:2px!important}
@media(max-width:900px){.block-container{padding-left:1rem;padding-right:1rem}.hero{padding:20px}.hero h1{font-size:1.5rem!important}.pagehead{padding:14px}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{transition:none!important;animation:none!important;scroll-behavior:auto!important}}
</style>
""", unsafe_allow_html=True)


accent_colors = {
    "Violet": ("#167d83", "#32999a"),
    "Ocean": ("#276b8a", "#4f91a7"),
    "Emerald": ("#267d69", "#5b9b85"),
    "Amber": ("#9a6b2e", "#c08b4e"),
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
    .workspace-topbar{background:#192238!important;border-color:#2c3854!important}
    .workspace-filename{color:#edf0ff!important}
    .workspace-detail,.replace-label{color:#aab5ce!important}
    .workspace-session{background:#29354f!important;border-color:#3b4866!important;color:#c0c9df!important}

    .overview-live{background:#17352f!important;border-color:#285c50!important;color:#a5e4cf!important}
    .signal-meta span{background:#29354f!important;color:#c0c9df!important}
    .pagehead,.upload-panel,.upload-guidance,.signal-card{background:#192238!important;border-color:#2c3854!important}
    .dataset-summary>span{background:#192238!important;border-color:#2c3854!important;color:#aab5ce!important}
    .dataset-summary .dataset-kind{background:#17352f!important;border-color:#285c50!important;color:#a5e4cf!important}
    .dataset-summary .dataset-recommendation{background:transparent!important;border-color:transparent!important}

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
px.defaults.color_discrete_sequence = ["#167d83", "#4f7894", "#8b9b78", "#c08b4e", "#7184a0", "#8c9a9e"]
px.defaults.color_continuous_scale = ["#e5f1f0", "#83b7b4", "#167d83", "#164d60"]
px.defaults.template = go.layout.Template(layout=go.Layout(
    font=dict(family="DM Sans, sans-serif", color=plot_text),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=True, gridcolor=plot_grid, zerolinecolor=plot_grid, linecolor=plot_grid),
    yaxis=dict(showgrid=True, gridcolor=plot_grid, zerolinecolor=plot_grid, linecolor=plot_grid),
    colorway=["#167d83", "#4f7894", "#8b9b78", "#c08b4e", "#7184a0", "#8c9a9e"],
))

if st.session_state.density == "Compact":
    st.markdown("<style>.block-container{padding-top:.8rem;padding-bottom:2rem}[data-testid='stMetric']{min-height:84px;padding:10px 13px}.card,.insight{padding:12px 14px;margin-bottom:7px}</style>", unsafe_allow_html=True)

# Apply a complete, accessible visual system before rendering the workspace.
_initial_visual_theme = resolve_theme(st.session_state.visual_theme, "General / mixed data")
st.markdown(
    build_theme_css(_initial_visual_theme, st.session_state.theme_mode, st.session_state.density),
    unsafe_allow_html=True,
)

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
        ["Overview", "Guided Analysis", "Decisions", "Analysis Studio", "Data Explorer", "Reports", "Settings"],
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

# ── Workspace entry / active dataset shell ───────────────────────────────────
# Keep a single uploader widget so Streamlit retains the selected file across reruns.
existing_upload = st.session_state.get("workspace_dataset_upload")
has_active_dataset = existing_upload is not None or st.session_state.get("use_sample_dataset", False)

if not has_active_dataset:
    st.markdown(f"""
    <div class="hero">
      <div class="eyebrow">DATA INTELLIGENCE WORKSPACE · {escape(st.session_state.workspace_name.upper())}</div>
      <h1>Clarity starts with your data.</h1>
      <p>Bring a dataset into a focused workspace to inspect its structure, find meaningful signals, and turn evidence into your next decision.</p>
      <div class="hero-meta">PROFILE &nbsp;·&nbsp; INVESTIGATE &nbsp;·&nbsp; EXPLAIN &nbsp;·&nbsp; EXPORT</div>
    </div>
    """, unsafe_allow_html=True)
    upload_left, upload_right = st.columns([1.35, .65], gap="large")
    with upload_left:
        st.markdown("""
        <div class="upload-panel">
          <div class="kicker">NEW ANALYSIS</div>
          <h2>Choose a dataset</h2>
          <p class="subtle" style="margin:0">Start with a file from your device. Your original values remain the source of truth.</p>
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
          <div class="card-label">DATA HANDLING</div>
          <p class="card-copy">Files are processed in this active app session. Avoid uploading sensitive personal or confidential data.</p>
          <p class="card-copy">No account, cloud project or external AI processing is implied.</p>
        </div>
        """, unsafe_allow_html=True)
else:
    active_name = existing_upload.name if existing_upload is not None else "DataPilot sample · synthetic orders"
    active_detail = "Uploaded file · active session" if existing_upload is not None else "Synthetic sample · fictional records"
    top_left, top_right = st.columns([1.6, .8], gap="medium")
    with top_left:
        st.markdown(f"""
        <div class="workspace-topbar">
          <div class="workspace-context">
            <div class="kicker">ACTIVE DATASET</div>
            <div class="workspace-filename">{escape(active_name)}</div>
            <div class="workspace-detail"><span class="status-dot"></span>{active_detail}</div>
          </div>
          <div class="workspace-session">SESSION WORKSPACE</div>
        </div>
        """, unsafe_allow_html=True)
    with top_right:
        st.markdown('<div class="replace-label">CHANGE DATASET</div>', unsafe_allow_html=True)
        upload = st.file_uploader(
            "Replace dataset",
            type=["csv", "tsv", "xlsx", "xls", "json"],
            help="Choose another CSV, TSV, Excel or JSON file",
            key="workspace_dataset_upload",
            label_visibility="collapsed",
        )

if upload is not None:
    st.session_state["use_sample_dataset"] = False
    dataset_name = upload.name
elif st.session_state.get("use_sample_dataset"):
    dataset_name = "DataPilot sample · synthetic orders"
else:
    dataset_name = None

if dataset_name is None:
    if page == "Settings":
        st.markdown("## Workspace settings")
        st.caption("These controls customize this active browser session. They do not create an account or persist across sessions.")
        st.text_input("Workspace name", key="workspace_name", max_chars=48)
        st.selectbox("Appearance", ["Light", "Dark"], key="theme_mode")
        st.selectbox("Visual direction", THEME_OPTIONS, key="visual_theme", help="Automatic selects a visual theme from the detected dataset domain.")
        st.markdown(theme_gallery_html(st.session_state.visual_theme), unsafe_allow_html=True)
        st.selectbox("Interface density", ["Comfortable", "Compact"], key="density")
        st.info("Workspace branding and interface preferences are session-local in this release. Persistent user accounts and cloud-saved settings are not implemented.")
    else:
        left, right = st.columns([1.15, .85], gap="large")
        with left:
            st.markdown("## Start with a real analysis, even before you have a file")
            st.write("Explore a fictional order dataset to see how profiling, guided analysis, evidence-ranked decisions and reports work end to end.")
            st.button(
                "Explore the sample dataset",
                type="primary",
                use_container_width=True,
                on_click=start_sample_dataset,
                key="start_sample_dataset",
            )
            st.caption("No upload required · generated locally · no external AI processing")
            st.markdown("## Or bring your own data")
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

if dataset_name is not None:
    # ── Load and profile ───────────────────────────────────────────────────────
    try:
        sheet_names = []
        chosen_sheet = None
        if upload is not None and upload.name.lower().endswith((".xlsx", ".xls")):
            book = pd.ExcelFile(BytesIO(upload.getvalue()))
            sheet_names = book.sheet_names
            if "selected_sheet" not in st.session_state or st.session_state.selected_sheet not in sheet_names:
                st.session_state.selected_sheet = sheet_names[0]
            chosen_sheet = st.session_state.selected_sheet
        raw = build_sample_dataset() if upload is None else read_upload(upload, chosen_sheet)[0]
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

    if upload is None:
        st.info(SAMPLE_DATASET_NOTICE)
        st.caption("Try: compare revenue by region, inspect monthly movement, or review order status and data quality.")

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
    # Resolve the visual language from the selected domain, unless the user chose a fixed theme.
    active_visual_theme = resolve_theme(st.session_state.visual_theme, domain_assessment["domain"])
    st.markdown(
        build_theme_css(active_visual_theme, st.session_state.theme_mode, st.session_state.density),
        unsafe_allow_html=True,
    )
    chart_colors = theme_chart_colors(active_visual_theme, st.session_state.theme_mode)
    plot_text = active_visual_theme["dark" if st.session_state.theme_mode == "Dark" else "light"]["text"]
    plot_grid = active_visual_theme["dark" if st.session_state.theme_mode == "Dark" else "light"]["line"]
    px.defaults.color_discrete_sequence = chart_colors
    px.defaults.color_continuous_scale = [
        active_visual_theme["light"]["accent_soft"],
        active_visual_theme["light"]["accent_2"],
        active_visual_theme["light"]["accent"],
        active_visual_theme["light"]["sidebar"],
    ]
    px.defaults.template = go.layout.Template(layout=go.Layout(
        font=dict(family="Inter, Segoe UI, sans-serif", color=plot_text),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor=plot_grid, zerolinecolor=plot_grid, linecolor=plot_grid),
        yaxis=dict(showgrid=True, gridcolor=plot_grid, zerolinecolor=plot_grid, linecolor=plot_grid),
        colorway=chart_colors,
    ))


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

    # Dataset context: compact metadata without repeating the filename in the top bar.
    st.markdown(
        f'<div class="dataset-summary"><span class="dataset-kind">{escape(str(profile.dataset_kind))}</span>'
        f'<span>{len(data):,} rows</span><span>{len(data.columns):,} fields</span>'
        f'<span class="dataset-recommendation">Suggested starting point: {escape(str(recommendation))}</span></div>',
        unsafe_allow_html=True,
    )

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
                    fig = px.bar(category_data.sort_values("records"), x="records", y=category_field, orientation="h", color="records", color_continuous_scale=["#c9c2fb", "#167d83"])
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
                        fig = px.histogram(measure_frame, x=measure_field, nbins=24, color_discrete_sequence=["#4f7894"])
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

    # ── Guided Analysis ────────────────────────────────────────────────────────
    elif page == "Guided Analysis":
        st.markdown("## Guided Analysis")
        st.caption("Start with a question. DataPilot checks which analyses your detected fields can support, then walks you through the relevant choices.")
        paths = available_guided_paths(numeric_cols, category_cols, date_cols)
        path_labels = {item["id"]: item["label"] for item in paths}
        selected_objective = st.selectbox(
            "1 · What would you like to understand?",
            list(path_labels),
            format_func=lambda value: path_labels[value],
            key="guided_objective",
        )
        st.markdown("### 2 · Configure the evidence")
        measure = dimension = date_field = x_measure = y_measure = None
        if selected_objective in ("measure_profile", "compare_groups", "time_movement"):
            measure = st.selectbox("Numeric measure", numeric_cols, key="guided_measure")
        if selected_objective == "compare_groups":
            dimension = st.selectbox("Group / dimension", category_cols, key="guided_dimension")
            min_group_size = st.slider("Minimum valid records per group", 1, 20, 3, key="guided_min_group")
        if selected_objective == "time_movement":
            date_field = st.selectbox("Date / time field", date_cols, key="guided_date")
            st.caption("The guided time view groups observations by calendar month.")
        if selected_objective == "relationship":
            x_measure, y_measure = st.columns(2)
            with x_measure:
                guided_x = st.selectbox("X measure", numeric_cols, key="guided_x")
            with y_measure:
                guided_y = st.selectbox("Y measure", [field for field in numeric_cols if field != guided_x], key="guided_y")
        if selected_objective == "quality_review":
            st.caption("Review completeness, distinct values and exact duplicate rows across the current filtered dataset.")
        if st.button("Run guided analysis", type="primary", key="run_guided_analysis"):
            try:
                result = build_guided_result(
                    filtered,
                    selected_objective,
                    measure=measure,
                    dimension=dimension,
                    date=date_field,
                    x_measure=guided_x if selected_objective == "relationship" else None,
                    y_measure=guided_y if selected_objective == "relationship" else None,
                    min_group_size=min_group_size if selected_objective == "compare_groups" else 3,
                )
                st.session_state["guided_result"] = result
                st.session_state["guided_result_objective"] = selected_objective
            except ValueError as exc:
                st.error(str(exc))
        result = st.session_state.get("guided_result")
        if result and st.session_state.get("guided_result_objective") == selected_objective:
            st.markdown('<div class="sectionline"></div>', unsafe_allow_html=True)
            st.markdown("### 3 · Your findings")
            if result["status"] == "empty":
                st.info(result["message"])
            else:
                st.caption(result["message"])
                for label, value in result["summary"].items():
                    if value is not None and isinstance(value, (int, float)):
                        st.metric(label.replace("_", " ").title(), fmt(value) if isinstance(value, float) else f"{value:,}")
                table = result["table"]
                if not table.empty:
                    if selected_objective == "compare_groups":
                        fig = px.bar(table, x="group", y="median", color="median", color_continuous_scale=["#c9dfdc", "#167d83", "#4f7894"], labels={"median": "Median", "group": dimension})
                        fig.update_layout(height=360, margin=dict(t=20, b=20, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
                        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
                    elif selected_objective == "time_movement":
                        fig = px.line(table, x="period", y="mean", markers=True, labels={"period": "Month", "mean": "Average"})
                        fig.update_layout(height=360, margin=dict(t=20, b=20, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
                    st.dataframe(table, use_container_width=True, hide_index=True)
                    st.download_button("Download guided result (CSV)", table.to_csv(index=False).encode("utf-8-sig"), "datapilot_guided_result.csv", "text/csv", key="download_guided_result")
                if result["source_indices"]:
                    source_rows = filtered.loc[filtered.index.intersection(result["source_indices"])]
                    with st.expander(f"Inspect supporting source records · {len(source_rows):,} rows"):
                        st.dataframe(source_rows.head(500), use_container_width=True, hide_index=True)
                        st.download_button("Download supporting records", source_rows.to_csv(index=False).encode("utf-8-sig"), "datapilot_guided_source_rows.csv", "text/csv", key="download_guided_source_rows")
            st.caption("Guided results are descriptive and traceable to the current filtered rows. They do not establish causality or predict future outcomes.")
        else:
            st.info("Choose an objective and its fields, then run the analysis. Only supported objectives are shown for this dataset.")

    # ── Decisions ──────────────────────────────────────────────────────────────
    elif page == "Decisions":
        st.markdown("## Insight-to-Action")
        st.caption("Turn ranked findings into concrete validation steps. Each action keeps its source evidence, sample context and decision guardrail.")
        action_plan = build_action_plan(profile.insights, filtered.columns.tolist(), len(filtered), limit=20)
        summary = action_plan_summary(action_plan)
        if not action_plan:
            st.markdown('<div class="empty"><strong>No evidence-backed actions are available yet.</strong><p>Review data quality or choose a guided analysis to generate a finding supported by the current dataset.</p></div>', unsafe_allow_html=True)
            st.button("Open Guided Analysis", type="primary", key="decisions_open_guided", on_click=go_to_page, args=("Guided Analysis",))
        else:
            st.markdown("### Action overview")
            cards = st.columns(4)
            cards[0].metric("Actions to review", summary["actions"])
            cards[1].metric("Risks to validate", summary.get("Risk to validate", 0) + summary.get("Data risk to validate", 0))
            cards[2].metric("Opportunities to investigate", summary.get("Opportunity to investigate", 0))
            cards[3].metric("Changes / coverage", summary.get("Change to investigate", 0) + summary.get("Coverage limitation", 0))
            st.info("These are investigation priorities, not promises of revenue, savings, performance improvement or causal impact. Validate each item before making a business decision.")
            action_options = {f'{item["action_id"]} · {item["action_type"]} — {item["finding_title"]}': item for item in action_plan}
            selected_action_label = st.selectbox("Choose an action to inspect", list(action_options), key="selected_decision_action")
            selected_action = action_options[selected_action_label]
            st.markdown('<div class="sectionline"></div>', unsafe_allow_html=True)
            st.markdown(f'### {selected_action["action_type"]}')
            st.markdown(f'**{selected_action["finding_title"]}**')
            st.write(selected_action["recommended_check"])
            evidence_left, evidence_right = st.columns(2)
            with evidence_left:
                st.markdown("**Source evidence**")
                st.write(selected_action["evidence"] or "No detailed evidence text was supplied by the finding.")
                st.caption(f'Finding type: {selected_action["finding_kind"]} · Evidence: {selected_action["evidence_level"]}')
            with evidence_right:
                st.markdown("**Evidence context**")
                st.metric("Priority score", f'{selected_action["priority_score"]}/100' if selected_action["priority_score"] is not None else "Not scored")
                st.metric("Sample support", str(selected_action["sample"]))
                st.metric("Rows in current view", f'{selected_action["view_rows"]:,}')
                st.caption("Priority scores are a review-order heuristic, not statistical significance or probability.")
            st.markdown("**Fields referenced by this finding**")
            if selected_action["fields"]:
                st.write(" · ".join(selected_action["fields"]))
            else:
                st.caption("No source column could be matched safely from the finding text.")
            st.markdown("**Suggested validation step**")
            st.write(selected_action["next_step"])
            st.markdown("**Decision guardrail**")
            st.caption(selected_action["decision_guardrail"])
            source_index = selected_action["source_index"]
            original_finding = profile.insights[source_index] if source_index < len(profile.insights) else {}
            with st.expander("Inspect original finding and full priority rationale"):
                st.json(original_finding)
            export_frame = action_plan_frame(action_plan)
            st.download_button("Export action plan (CSV)", export_frame.to_csv(index=False).encode("utf-8-sig"), "datapilot_action_plan.csv", "text/csv", key="export_action_plan")
            st.download_button("Export action plan (JSON)", json.dumps(action_plan, ensure_ascii=False, indent=2, default=str).encode("utf-8"), "datapilot_action_plan.json", "application/json", key="export_action_plan_json")
            st.markdown("### Full action register")
            st.dataframe(export_frame, use_container_width=True, hide_index=True)
            st.caption("The register is rebuilt from the current filtered dataset on each run. Actions are session-local and are not saved to an account or external service.")

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
                        fig = px.bar(summary.sort_values("value"), x="value", y=dimension, orientation="h", color="value", color_continuous_scale=["#c9dfdc","#167d83","#4f7894"])
                    elif chart == "Vertical bars":
                        fig = px.bar(summary, x=dimension, y="value", color="value", color_continuous_scale=["#c9dfdc","#167d83","#4f7894"])
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
                    event = st.plotly_chart(
                        fig, use_container_width=True,
                        config={"displaylogo":False,"scrollZoom":True},
                        on_select="rerun", selection_mode="points",
                        key="time_trend_chart",
                    )
                    selected_periods = selected_point_values(event, ["x"])
                    if selected_periods:
                        period_frequency = {"Day":"D","Week":"W","Month":"M","Quarter":"Q","Year":"Y"}[grain]
                        source_dates = pd.to_datetime(filtered[date_col], errors="coerce")
                        source_periods = source_dates.dt.to_period(period_frequency).dt.start_time
                        selected_keys = {
                            stamp.strftime("%Y-%m-%d")
                            for stamp in pd.to_datetime(selected_periods, errors="coerce")
                            if pd.notna(stamp)
                        }
                        source_rows = filtered.loc[source_periods.dt.strftime("%Y-%m-%d").isin(selected_keys)]
                        st.markdown("### Selected periods · source records")
                        st.caption(f"{len(source_rows):,} source rows contribute to the selected time period(s).")
                        if not source_rows.empty:
                            st.dataframe(source_rows.head(500), use_container_width=True, hide_index=True)
                            st.download_button(
                                "Download selected period rows",
                                source_rows.to_csv(index=False).encode("utf-8-sig"),
                                "datapilot_selected_period_rows.csv",
                                "text/csv",
                                key="download_selected_period_rows",
                            )
                    else:
                        st.caption("Select one or more points on the timeline to inspect the exact source records behind those periods.")

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
                    fig = px.histogram(filtered, x=measure, marginal="box", nbins=40, color_discrete_sequence=["#167d83"])
                elif chart == "Violin":
                    fig = px.violin(filtered, y=measure, box=True, points="outliers", color_discrete_sequence=["#4f7894"])
                else:
                    fig = px.ecdf(filtered, x=measure, color_discrete_sequence=["#167d83"])
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
                    fig = px.scatter(plot_data, x=x, y=y, opacity=.75, color_discrete_sequence=["#167d83"])
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
                    fig = px.bar(counts.sort_values("records"), x="records", y=dim, orientation="h", color="records", color_continuous_scale=["#c9dfdc","#167d83"])
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
                    color_discrete_sequence=["#167d83"],
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
                spotlight_fig = px.area(date_counts, x="Period", y="Records", markers=True, color_discrete_sequence=["#4f7894"])
                spotlight_fig.update_layout(height=310, margin=dict(t=20,b=24,l=12,r=12))
                st.plotly_chart(spotlight_fig, use_container_width=True, config={"displaylogo":False})
        else:
            counts = spotlight.astype("string").fillna("(Missing)").value_counts().head(14).rename_axis("Value").reset_index(name="Records")
            if not counts.empty:
                spotlight_fig = px.bar(counts.sort_values("Records"), x="Records", y="Value", orientation="h", color="Records", color_continuous_scale=["#c9dfdc","#167d83","#4f7894"])
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
            fig = px.bar(mdf, x="Missing %", y="Field", orientation="h", color="Missing %", color_continuous_scale=["#4f7894","#167d83","#e5ae52"])
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
            title=report_title, dataset=dataset_name, domain=profile.dataset_kind,
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
            st.selectbox("Visual direction", THEME_OPTIONS, key="visual_theme", help="Automatic selects a visual theme from the detected dataset domain. You can lock a theme here.")
            st.markdown(theme_gallery_html(st.session_state.visual_theme, domain_assessment["domain"]), unsafe_allow_html=True)
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
