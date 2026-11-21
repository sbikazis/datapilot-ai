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
from visualizations import build_time_figure
from studio_logic import recommend_visualization, numeric_summary, safe_correlation, category_summary, build_evidence_findings, detect_delimiter

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
    "accent_palette": "Violet",
    "nav_page": "Overview",
    "active_filters": {},
    "role_overrides": {},
    "chart_type": "Recommended",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

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
.stProgress>div>div>div{background:linear-gradient(90deg,#6955e8,#21b8b2)}
@media(max-width:900px){.block-container{padding:1rem 1rem 3rem}.hero{padding:22px}.hero h1{font-size:1.6rem!important}}
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
    .card,.insight,[data-testid="stMetric"],[data-testid="stPlotlyChart"],[data-testid="stExpander"],[data-testid="stDataFrame"]{background:#192238!important;border-color:#2c3854!important;color:#e8ecf8}
    .card-title,.insight strong{color:#edf0ff!important}
    .card-copy,.insight p,.subtle{color:#aab5ce!important}
    .stTextInput input,.stSelectbox div[data-baseweb="select"],.stMultiSelect div[data-baseweb="select"]{background:#192238;color:#edf0ff}
    [data-testid="stMetricValue"]{color:#edf0ff}
    [data-testid="stMetricLabel"]{color:#aab5ce!important}
    </style>
    """, unsafe_allow_html=True)
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

def fmt(value, decimals=2):
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

def to_html_report(title, filename, profile, frame, filtered, findings, workspace):
    metrics = []
    for col in profile.numeric_columns[:8]:
        s = pd.to_numeric(filtered[col], errors="coerce").dropna()
        if len(s):
            metrics.append(f"<tr><td>{escape(col)}</td><td>{len(s):,}</td><td>{s.sum():,.3f}</td><td>{s.mean():,.3f}</td><td>{s.median():,.3f}</td></tr>")
    insight_html = "".join(
        f"<article><small>{escape(x['kind'])}</small><h3>{escape(x['title'])}</h3><p>{escape(x['detail'])}</p><p class='muted'>Next: {escape(x['action'])}</p></article>"
        for x in findings
    )
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>{escape(title)}</title>
<style>
body{{font:15px/1.6 Arial,sans-serif;background:#f4f6fb;color:#1d2942;margin:0;padding:36px}}
main{{max-width:1050px;margin:auto;background:white;border:1px solid #e4e8f1;border-radius:20px;padding:38px}}
header{{background:linear-gradient(110deg,#111a30,#514995);color:white;padding:26px;border-radius:15px}}
h1{{margin:0}}header p{{color:#dce2f7}}h2{{margin-top:32px}}article{{border-left:4px solid #7561e6;background:#fafaff;padding:12px 17px;margin:12px 0;border-radius:9px}}
small{{color:#705cdb;text-transform:uppercase;font-weight:bold;letter-spacing:1px}}.muted{{color:#75819a;font-size:13px}}
table{{border-collapse:collapse;width:100%;margin-top:12px}}td,th{{border-bottom:1px solid #e6eaf2;text-align:left;padding:10px}}th{{background:#f6f7fb}}
</style></head><body><main><header><h1>{escape(title)}</h1><p>{escape(workspace)} · {escape(filename)}</p><p>Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · {len(filtered):,} filtered of {len(frame):,} source rows</p></header>
<h2>Executive snapshot</h2><p>{profile.dataset_kind} · {len(frame):,} rows · {len(frame.columns):,} fields · {profile.quality['missing_cells']:,} missing cells · {profile.quality['duplicate_rows']:,} exact duplicate rows</p>
<h2>Key measures</h2><table><tr><th>Measure</th><th>Valid</th><th>Total</th><th>Average</th><th>Median</th></tr>{''.join(metrics)}</table>
<h2>Evidence-led findings</h2>{insight_html}
<h2>Method and limitations</h2><p>Findings are calculated from the selected data. They describe observed patterns and statistical associations; they do not establish causes, forecasts, or missing business facts. Review detected field roles and data quality before making decisions.</p>
<p class='muted'>DataPilot AI · Adaptive Data Intelligence</p></main></body></html>"""

def excel_export(frame, profile, filtered):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name="Analyzed data", index=False)
        filtered.to_excel(writer, sheet_name="Filtered data", index=False)
        pd.DataFrame(profile.columns).to_excel(writer, sheet_name="Field profile", index=False)
        pd.DataFrame(profile.insights).to_excel(writer, sheet_name="Findings", index=False)
    return output.getvalue()

# ── Sidebar shell ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div class="brand"><div class="brandmark">{escape(st.session_state.workspace_mark[:3])}</div><div><div class="brandname">DataPilot AI</div><div class="brandtag">INTELLIGENCE STUDIO</div></div></div>', unsafe_allow_html=True)
    st.caption(escape(st.session_state.get("workspace_subtitle", "YOUR DATA. UNDERSTOOD.")))
    st.markdown("---")
    page = st.radio(
        "WORKSPACE",
        ["Overview", "Analysis Studio", "Data Explorer", "Reports", "Settings"],
        key="nav_page",
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**DATA SOURCE**")
    upload = st.file_uploader("Upload a dataset", type=["csv", "tsv", "xlsx", "xls", "json"], help="CSV, TSV, Excel or JSON")
    st.caption("Files stay in this app session. Do not upload sensitive personal data.")
    if upload is not None:
        st.success(f"Loaded · {upload.name}")
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

# Recalculate findings against the active global filter so explanations match the visible records.
profile.insights = build_evidence_findings(filtered, numeric_cols, category_cols, date_cols)

# Common source context header
st.markdown(f'<div class="pagehead"><div><div class="kicker">{profile.dataset_kind} · DATASET PROFILE</div><h2 style="margin:3px 0">{upload.name}</h2><div class="subtle">{len(data):,} rows · {len(data.columns):,} fields · recommended starting point: {recommendation}</div></div><span class="pill">LIVE SESSION</span></div>', unsafe_allow_html=True)

# ── Overview ───────────────────────────────────────────────────────────────
if page == "Overview":
    k = st.columns(5)
    k[0].metric("Rows in view", f"{len(filtered):,}", f"{len(data)-len(filtered):,} filtered out")
    k[1].metric("Fields", f"{len(data.columns):,}")
    k[2].metric("Measures", f"{len(numeric_cols):,}")
    k[3].metric("Date fields", f"{len(date_cols):,}")
    k[4].metric("Missing cells", f"{int(data.isna().sum().sum()):,}", f"{profile.quality['missing_pct']}% of source cells")
    st.markdown("## Intelligence brief")
    st.caption("Evidence-led observations from the current dataset. These are patterns to investigate, not claims about causes.")
    for item in profile.insights[:8]:
        st.markdown(f'<div class="insight"><div class="kind">{item["kind"]}</div><strong>{item["title"]}</strong><p>{item["detail"]}</p><div class="next">NEXT INVESTIGATION → {item["action"]}</div></div>', unsafe_allow_html=True)
    if not profile.insights:
        st.markdown('<div class="empty">No reliable automatic findings yet. Open Analysis Studio to choose a measure and investigate the dataset.</div>', unsafe_allow_html=True)
    st.markdown("## Recommended first analysis")
    c1, c2 = st.columns([1.1, .9], gap="large")
    with c1:
        st.markdown(f'<div class="card"><div class="card-label">RECOMMENDED VIEW</div><div class="card-title">{recommendation}</div><div class="card-copy">{recommendation_reason}</div></div>', unsafe_allow_html=True)
        if numeric_cols:
            metric = st.selectbox("Preview a measure", numeric_cols, key="overview_metric")
            series = pd.to_numeric(filtered[metric], errors="coerce").dropna()
            if len(series):
                st.metric(f"{metric} · total", fmt(series.sum()), f"Average {fmt(series.mean())} · median {fmt(series.median())}")
                fig = px.histogram(filtered, x=metric, marginal="box", nbins=32, color_discrete_sequence=["#7563e8"])
                fig.update_layout(height=330, margin=dict(t=15,b=20,l=10,r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False})
    with c2:
        st.markdown("### Data health")
        q = profile.quality
        st.metric("Exact duplicate rows", f"{q['duplicate_rows']:,}")
        st.metric("Constant fields", f"{len(q['constant_columns']):,}")
        missing = data.isna().sum().sort_values(ascending=False)
        missing = missing[missing > 0].head(8)
        if len(missing):
            st.markdown("**Fields with most missing values**")
            st.dataframe(missing.rename("Missing").reset_index().rename(columns={"index":"Field"}), use_container_width=True, hide_index=True)
        else:
            st.success("No missing cells detected in the source data.")
    st.caption("The automatic findings are statistical/rule-based. No external generative AI model is connected in this release.")

# ── Analysis Studio ────────────────────────────────────────────────────────
elif page == "Analysis Studio":
    st.markdown("## Analysis Studio")
    st.caption("Choose the question, dimensions, measures and method. All views use the active global filters.")
    if not numeric_cols and not category_cols and not date_cols:
        st.warning("No analyzable fields were detected. Review field roles in the sidebar.")
    mode_options = ["Compare groups", "Time trend", "Distribution", "Relationship", "Category composition"]
    default_mode = {"Ranked comparison":"Compare groups","Time trend":"Time trend","Distribution":"Distribution","Relationship scatter":"Relationship","Category frequency":"Category composition"}.get(recommendation, "Compare groups")
    mode = st.segmented_control("Analysis type", mode_options, default=default_mode, key="studio_mode")
    mode = mode or default_mode
    if mode == "Compare groups":
        if numeric_cols and category_cols:
            a,b,c = st.columns([1.15,1.15,.9])
            with a: dimension = st.selectbox("Dimension", category_cols, key="cmp_dimension")
            with b: measure = st.selectbox("Measure", numeric_cols, key="cmp_measure")
            with c: agg = st.selectbox("Aggregation", ["sum","mean","median","min","max","count"], key="cmp_agg")
            limit = st.slider("Show groups", 3, 40, 12, key="cmp_limit")
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
                st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False,"scrollZoom":True})
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
            st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False,"scrollZoom":True})
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
            st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False})
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
    st.markdown("### Missingness map")
    missing = data.isna().mean().mul(100).sort_values(ascending=False)
    missing = missing[missing > 0]
    if len(missing):
        mdf = missing.rename("Missing %").reset_index().rename(columns={"index":"Field"})
        fig = px.bar(mdf, x="Missing %", y="Field", orientation="h", color="Missing %", color_continuous_scale=["#21b8b2","#6955e8"])
        fig.update_layout(height=max(260,len(mdf)*34), margin=dict(t=10,b=10,l=10,r=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("All source fields are complete.")

# ── Reports ─────────────────────────────────────────────────────────────────
elif page == "Reports":
    st.markdown("## Reports & exports")
    st.caption("Build a portable report from the current data and filter state. Report figures are computed, not generated from invented context.")
    report_title = st.text_input("Report title", value=f"{profile.dataset_kind} analysis")
    report_findings = profile.insights[:12]
    html = to_html_report(report_title, upload.name, profile, data, filtered, report_findings, st.session_state.workspace_name)
    x1,x2,x3 = st.columns(3)
    with x1:
        st.download_button("Download executive report (HTML)", html.encode("utf-8"), "datapilot_executive_report.html", "text/html", use_container_width=True, type="primary")
    with x2:
        st.download_button("Download workbook (XLSX)", excel_export(data, profile, filtered), "datapilot_analysis.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with x3:
        payload = {"dataset":upload.name,"kind":profile.dataset_kind,"rows":len(data),"filtered_rows":len(filtered),"quality":profile.quality,"field_profile":profile.columns,"findings":profile.insights,"filters":st.session_state.active_filters}
        st.download_button("Download analysis profile (JSON)", json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8"), "datapilot_profile.json", "application/json", use_container_width=True)
    st.markdown("### Report preview")
    st.markdown(f'<div class="card"><div class="card-label">EXECUTIVE REPORT</div><div class="card-title">{report_title}</div><div class="card-copy">{profile.dataset_kind} · {len(filtered):,} filtered rows · {len(profile.insights):,} evidence-led findings · includes field profile, key measures, quality checks and method caveats.</div></div>', unsafe_allow_html=True)
    for item in report_findings[:5]:
        st.markdown(f'<div class="insight"><div class="kind">{item["kind"]}</div><strong>{item["title"]}</strong><p>{item["detail"]}</p></div>', unsafe_allow_html=True)
    st.info("PDF export, scheduled delivery and saved report history are not included yet. HTML and Excel exports are available now.")

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
        st.selectbox("Accent palette", ["Violet","Ocean","Emerald","Amber"], key="accent_palette")
        st.selectbox("Theme", ["Light","Dark"], key="theme_mode")
        st.selectbox("Density", ["Comfortable","Compact"], key="density")
    with right:
        st.markdown("### Analysis defaults")
        st.selectbox("Default chart preference", ["Recommended","Bars","Line","Scatter","Table"], key="chart_type")
        st.selectbox("Number precision", [0,1,2,3,4], index=2, key="precision")
        st.selectbox("Default Top N", [5,10,12,20,30,50], index=2, key="default_top_n")
        st.markdown("### Privacy & data handling")
        st.info("Uploads are analyzed in the active app session. This build does not provide account login, persistent cloud projects, shared workspaces or external AI processing.")
        st.checkbox("Show methodology notes in reports", value=True, key="show_method_notes")
    st.markdown("---")
    if st.button("Reset workspace preferences"):
        for key, value in defaults.items():
            st.session_state[key] = value
        st.rerun()
    st.caption("Persistent identity, custom logo uploads and cross-device settings require an authenticated storage layer; this page does not pretend those backend capabilities exist.")

st.markdown('<div class="sectionline"></div><div class="subtle">DataPilot AI · Adaptive analysis, transparent calculations and evidence-led exploration. No fabricated causes, forecasts or business assumptions.</div>', unsafe_allow_html=True)
