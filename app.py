import io
import streamlit as st
import pandas as pd
import plotly.express as px
from engine import analyze_sales, build_html_report, load_sales_file

st.set_page_config(page_title="DataPilot AI | Sales Intelligence", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#21143f; --muted:#746b8b; --violet:#7652e8; --pink:#ed75b5; --cyan:#54d5d0; --gold:#f5bd62; }
.stApp { background: radial-gradient(ellipse at 8% 0%, rgba(118,82,232,.13), transparent 34%), radial-gradient(ellipse at 95% 12%, rgba(84,213,208,.13), transparent 30%), linear-gradient(135deg,#f8f6ff 0%,#f4f9ff 52%,#fff7fb 100%); color:var(--ink); font-family:'DM Sans',sans-serif; }
[data-testid="stHeader"] { background:rgba(248,246,255,.75); }
.block-container { max-width:1440px; padding-top:2.2rem; padding-bottom:4rem; }
h1,h2,h3 { font-family:'Manrope',sans-serif!important; color:#241643!important; letter-spacing:-.035em; }
h1 { font-size:2.55rem!important; font-weight:800!important; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#241744 0%,#382365 55%,#4a3478 100%); }
[data-testid="stSidebar"] * { color:#f8f4ff!important; }
[data-testid="stSidebar"] [data-testid="stFileUploader"] { background:rgba(255,255,255,.10); border:1px dashed rgba(255,255,255,.4); border-radius:18px; padding:12px; }
[data-testid="stMetric"] { background:rgba(255,255,255,.86); border:1px solid rgba(118,82,232,.14); border-radius:20px; padding:18px 20px; box-shadow:0 10px 30px rgba(49,31,91,.055); min-height:126px; }
[data-testid="stMetricLabel"] { color:#766d8d!important; font-weight:700; }
[data-testid="stMetricValue"] { color:#2b1b50!important; font-family:'Manrope',sans-serif; font-weight:800; }
[data-testid="stTabs"] button { border-radius:12px 12px 0 0; font-weight:700; }
.stButton>button,.stDownloadButton>button { border:0; border-radius:13px; background:linear-gradient(100deg,#7552e8,#9a68ee); color:white; font-weight:700; padding:.65rem 1.1rem; box-shadow:0 8px 18px rgba(118,82,232,.18); }
.stButton>button:hover,.stDownloadButton>button:hover { color:white; border:0; filter:brightness(1.06); transform:translateY(-1px); }
[data-testid="stDataFrame"],[data-testid="stTable"] { border:1px solid #e9e3f5; border-radius:16px; overflow:hidden; }
div[data-testid="stAlert"] { border-radius:14px; }
.hero { background:linear-gradient(112deg,#2d1d50 0%,#6546b4 58%,#a45db5 100%); color:white; padding:28px 32px; border-radius:26px; box-shadow:0 18px 40px rgba(57,36,99,.18); position:relative; overflow:hidden; margin-bottom:24px; }
.hero:after { content:""; position:absolute; width:260px;height:260px;border-radius:50%;right:-65px;top:-125px;background:rgba(84,213,208,.23); }
.hero h1 { color:white!important; margin:0 0 8px 0; font-size:2.15rem!important; }
.hero p { color:#eee7ff; margin:0; max-width:760px; }
.eyebrow { color:#9de9e2; text-transform:uppercase; font-size:.72rem; font-weight:800; letter-spacing:.16em; margin-bottom:10px; }
.section-kicker { color:#8b75bd; font-size:.75rem; font-weight:800; text-transform:uppercase; letter-spacing:.13em; margin:12px 0 4px; }
.insight { background:linear-gradient(110deg,rgba(118,82,232,.10),rgba(84,213,208,.12)); border:1px solid rgba(118,82,232,.13); border-radius:18px; padding:16px 19px; color:#35265a; margin:8px 0 18px; }
.small-note { color:#7a718e; font-size:.84rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">Sales intelligence studio</div>
  <h1>Make every sale tell a story.</h1>
  <p>Turn raw exports into reliable numbers, clear patterns and decisions you can act on — without pretending missing data exists.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ✦ DataPilot AI")
    st.caption("YOUR BUSINESS, IN FOCUS")
    st.markdown("---")
    upload = st.file_uploader("Import your sales data", type=["csv", "xlsx", "xls"], help="CSV, Excel XLSX or XLS. Maximum 200 MB.")
    st.markdown("---")
    st.markdown("**Built for clarity**")
    st.caption("• Transparent validation\n\n• No invented currency\n\n• Row-level rejection reasons\n\n• Downloadable outputs")
    st.markdown("---")
    st.caption("Your file is processed in this app session. Avoid uploading unnecessary customer-identifying information.")

if not upload:
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        st.markdown("### Your next clear business decision starts here.")
        st.write("Upload a sales export and DataPilot will map your columns, validate each row, calculate core profitability metrics and reveal product, category and time trends.")
        st.markdown("""
        <div class="insight"><b>Designed around trustworthy analysis</b><br>Every rejected row includes a reason. Every metric is calculated from accepted source rows. No silent assumptions about currency, taxes or returns.</div>
        """, unsafe_allow_html=True)
    with right:
        st.markdown("### What you’ll unlock")
        for title, detail in [
            ("01 · Performance pulse", "Revenue, cost, gross profit, margin and average order value."),
            ("02 · Product intelligence", "Find the products and categories contributing most."),
            ("03 · Time patterns", "Explore monthly movement and spot changes."),
            ("04 · Clean exports", "Download validated data, rejected rows and a shareable report."),
        ]:
            st.markdown(f"**{title}**")
            st.caption(detail)
    st.stop()

try:
    raw = load_sales_file(upload, upload.name)
    result = analyze_sales(raw)
except Exception as exc:
    st.error(f"Could not analyze this file: {exc}")
    st.info("Check the required columns and review the file format. Your original file is not modified.")
    st.stop()

s = result.summary
st.markdown('<div class="section-kicker">01 / Executive overview</div>', unsafe_allow_html=True)
st.markdown("## Your business at a glance")
valid_rate = (s["valid_rows"] / s["total_rows"] * 100) if s["total_rows"] else 0
if s["rejected_rows"]:
    st.warning(f"Data quality needs attention: {s['valid_rows']} of {s['total_rows']} rows accepted ({valid_rate:.1f}%). Download the rejection log to see the exact source row and reason.")
else:
    st.success(f"All {s['total_rows']} source rows passed validation. No rows were silently discarded.")

metric_cols = st.columns(5)
metrics = [
    ("Revenue", s["total_revenue"], False),
    ("Gross profit", s["gross_profit"], False),
    ("Gross margin", s["gross_margin_pct"], True),
    ("Orders", s["order_count"], False),
    ("Avg. order value", s["average_order_value"], False),
]
for col, (label, value, pct) in zip(metric_cols, metrics):
    shown = "—" if value is None else (f"{value:,.2f}%" if pct else f"{value:,.2f}" if label != "Orders" else f"{value:,}")
    col.metric(label, shown)

with st.expander("How these numbers are calculated", expanded=False):
    st.write("Revenue = quantity × unit price. Cost = quantity × unit cost. Gross profit = revenue − recorded cost. Gross margin = gross profit ÷ revenue. Average order value = revenue ÷ distinct order IDs.")
    st.caption("These are operational analytics, not certified accounting. Taxes, refunds, shipping, payment fees and currency are not inferred.")

st.markdown('<div class="section-kicker">02 / Explore the signals</div>', unsafe_allow_html=True)
tab_overview, tab_products, tab_time, tab_quality, tab_exports = st.tabs(["✦ Overview", "◈ Products & categories", "⌁ Trends", "✓ Data quality", "↓ Exports"])

with tab_overview:
    a, b = st.columns([1.1, .9], gap="large")
    with a:
        st.markdown("### Revenue by category")
        fig = px.pie(result.by_category, names="category", values="revenue", hole=.68, color_discrete_sequence=["#7652e8","#54d5d0","#ed75b5","#f5bd62","#7b9df4","#8bcf9b"])
        fig.update_traces(textposition="inside", textinfo="percent+label", marker=dict(line=dict(color="#f8f6ff", width=3)))
        fig.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=330, font=dict(family="DM Sans",color="#38285b"))
        st.plotly_chart(fig, use_container_width=True)
    with b:
        st.markdown("### Where profit comes from")
        profit_data = result.by_category.sort_values("gross_profit", ascending=True)
        fig = px.bar(profit_data, x="gross_profit", y="category", orientation="h", color="gross_profit", color_continuous_scale=["#ed75b5","#7652e8","#54d5d0"])
        fig.update_layout(coloraxis_showscale=False, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=330, xaxis_title="Gross profit", yaxis_title="", font=dict(family="DM Sans",color="#38285b"))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('<div class="insight"><b>Read the numbers in context.</b> Revenue is not the same as profit. Compare both before deciding which products deserve more attention.</div>', unsafe_allow_html=True)

with tab_products:
    st.markdown("### Product performance")
    product_options = ["All categories"] + sorted(result.by_category["category"].dropna().astype(str).unique().tolist())
    selected_category = st.selectbox("Focus on a category", product_options)
    product_data = result.clean.copy()
    if selected_category != "All categories":
        product_data = product_data[product_data["category"].astype(str) == selected_category]
    product_rollup = product_data.groupby("product", as_index=False).agg(units=("quantity","sum"), revenue=("revenue","sum"), cost=("cost","sum"), gross_profit=("gross_profit","sum")).sort_values("revenue", ascending=False)
    fig = px.bar(product_rollup.head(15).sort_values("revenue"), x="revenue", y="product", orientation="h", color="gross_profit", color_continuous_scale=["#ed75b5","#7652e8","#54d5d0"], hover_data=["units","cost","gross_profit"])
    fig.update_layout(coloraxis_showscale=False, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="Revenue", yaxis_title="", font=dict(family="DM Sans",color="#38285b"))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(product_rollup, use_container_width=True, hide_index=True)

with tab_time:
    st.markdown("### Performance over time")
    monthly = result.by_month.copy()
    if len(monthly):
        fig = px.line(monthly, x="month", y=["revenue","gross_profit"], markers=True, color_discrete_sequence=["#7652e8","#ed75b5"], labels={"value":"Amount","month":"Month","variable":"Metric"})
        fig.update_traces(line=dict(width=3))
        fig.update_layout(hovermode="x unified", margin=dict(t=15,b=15,l=10,r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="DM Sans",color="#38285b"))
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(monthly, use_container_width=True, hide_index=True)

with tab_quality:
    st.markdown("### Validation & trust")
    q1, q2, q3 = st.columns(3)
    q1.metric("Source rows", f"{s['total_rows']:,}")
    q2.metric("Accepted", f"{s['valid_rows']:,}")
    q3.metric("Rejected", f"{s['rejected_rows']:,}")
    st.progress(valid_rate / 100, text=f"{valid_rate:.1f}% accepted")
    st.markdown("#### Detected column mapping")
    mapping_df = pd.DataFrame([{"Source column": source, "DataPilot field": target} for source, target in result.column_mapping.items()])
    st.dataframe(mapping_df, use_container_width=True, hide_index=True)
    if not result.rejected.empty:
        st.markdown("#### Rejected rows — with exact reasons")
        display_rejected = result.rejected.drop(columns=["rejection_reason"], errors="ignore")
        st.dataframe(result.rejected, use_container_width=True, hide_index=True)
    else:
        st.success("No rejected rows. All source records passed the current validation rules.")

with tab_exports:
    st.markdown("### Take your work with you")
    clean_csv = result.clean.drop(columns=["_source_row"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
    rejected_csv = result.rejected.to_csv(index=False).encode("utf-8-sig")
    report_html = build_html_report(result).encode("utf-8")
    d1, d2, d3 = st.columns(3)
    d1.download_button("↓ Clean dataset", clean_csv, "datapilot_cleaned_sales.csv", "text/csv", use_container_width=True)
    d2.download_button("↓ Rejection log", rejected_csv, "datapilot_rejected_rows.csv", "text/csv", use_container_width=True, disabled=result.rejected.empty)
    d3.download_button("↓ Business report", report_html, "datapilot_business_report.html", "text/html", use_container_width=True)
    st.caption("The cleaned file includes calculated revenue, cost, gross profit, margin and month. The rejection log includes the original row values and reasons.")

st.markdown("---")
st.caption("DataPilot AI · Clear numbers. Better decisions. · Session-only processing")
