from __future__ import annotations

from io import BytesIO
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from universal_engine import profile_dataset, grouped_summary, time_summary
from engine import analyze_sales, load_sales_file, build_html_report

st.set_page_config(page_title="DataPilot AI · Intelligent data studio", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;600;700;800&display=swap');
:root{--navy:#111827;--muted:#8b98ad;--violet:#7558f5;--cyan:#39c6c3;--pink:#ed75ad;--gold:#f4bd61}
.stApp{background:radial-gradient(ellipse at 5% 0%,rgba(117,88,245,.16),transparent 31%),radial-gradient(ellipse at 95% 8%,rgba(57,198,195,.12),transparent 28%),#f5f7fc;color:#172033;font-family:'DM Sans',sans-serif}
.block-container{max-width:1500px;padding-top:1.4rem;padding-bottom:4rem}
h1,h2,h3{font-family:'Manrope',sans-serif!important;letter-spacing:-.035em;color:#172033!important}
h1{font-weight:800!important}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#121a2c,#20284a 68%,#322b61)}
[data-testid="stSidebar"] *{color:#f4f5ff!important}
[data-testid="stMetric"]{background:rgba(255,255,255,.92);border:1px solid #e8ebf4;border-radius:18px;padding:16px 18px;box-shadow:0 8px 24px rgba(26,37,67,.045);min-height:112px}
[data-testid="stMetricLabel"]{color:#77839a!important;font-weight:700}
[data-testid="stMetricValue"]{font-family:'Manrope',sans-serif;color:#1c2740;font-weight:800}
.stButton>button,.stDownloadButton>button{border:0;border-radius:12px;background:linear-gradient(100deg,#7055ee,#8d6df6);color:white;font-weight:700;padding:.62rem 1rem}
.stButton>button:hover,.stDownloadButton>button:hover{color:white;border:0;filter:brightness(1.08)}
[data-testid="stTabs"] button{font-weight:700}
[data-testid="stDataFrame"]{border:1px solid #e6eaf2;border-radius:14px;overflow:hidden}
div[data-testid="stAlert"]{border-radius:13px}
.hero{background:linear-gradient(112deg,#121b30 0%,#34366d 60%,#6551ae 100%);color:white;border-radius:24px;padding:27px 31px;margin-bottom:20px;position:relative;overflow:hidden;box-shadow:0 16px 38px rgba(27,31,67,.15)}
.hero:after{content:"";position:absolute;width:280px;height:280px;right:-80px;top:-140px;border-radius:50%;background:rgba(57,198,195,.2)}
.hero h1{color:#fff!important;font-size:2.25rem!important;margin:0 0 8px}
.hero p{color:#dce3ff;margin:0;max-width:850px}
.eyebrow{font-size:.7rem;letter-spacing:.17em;text-transform:uppercase;font-weight:800;color:#8de4dd;margin-bottom:8px}
.panel{background:rgba(255,255,255,.86);border:1px solid #e8ebf4;border-radius:18px;padding:17px 19px;margin-bottom:12px}
.panel-title{font-weight:800;color:#25304a;margin-bottom:5px}
.muted{color:#7e8aa0;font-size:.86rem}
.insight{background:white;border:1px solid #e8ebf4;border-left:4px solid #7558f5;border-radius:15px;padding:15px 17px;margin:8px 0;box-shadow:0 5px 18px rgba(30,42,75,.035)}
.insight small{color:#8b78d9;font-weight:800;text-transform:uppercase;letter-spacing:.08em}
.insight strong{display:block;color:#202b45;margin:4px 0}
[data-testid="stFileUploader"]{background:rgba(255,255,255,.08);border:1px dashed rgba(255,255,255,.35);border-radius:15px;padding:10px}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
 <div class="eyebrow">DATA INTELLIGENCE · NOT JUST A DASHBOARD</div>
 <h1>Understand your data. Find your next move.</h1>
 <p>DataPilot examines the structure, quality, patterns and relationships in each file, then adapts the analysis to the data it actually contains.</p>
</div>
""", unsafe_allow_html=True)

def load_any(upload):
    name = upload.name.lower()
    if name.endswith(".xlsx"):
        return pd.read_excel(upload, engine="openpyxl")
    if name.endswith(".xls"):
        return pd.read_excel(upload, engine="xlrd")
    if name.endswith(".json"):
        return pd.read_json(upload)
    if name.endswith(".tsv"):
        return pd.read_csv(upload, sep="\t")
    try:
        return pd.read_csv(upload)
    except UnicodeDecodeError:
        upload.seek(0)
        return pd.read_csv(upload, encoding="latin-1")

with st.sidebar:
    st.markdown("## ◈ DataPilot AI")
    st.caption("ADAPTIVE DATA INTELLIGENCE")
    st.markdown("---")
    upload = st.file_uploader("Drop a dataset", type=["csv","tsv","xlsx","xls","json"], help="CSV, TSV, Excel or JSON")
    st.markdown("---")
    st.markdown("**Analysis principles**")
    st.caption("• Detect structure automatically\n\n• Keep source values traceable\n\n• Explain findings in plain language\n\n• Never invent missing business facts")
    st.markdown("---")
    st.caption("Files are processed in the current app session. Avoid uploading sensitive personal data.")

if upload is None:
    a,b=st.columns([1.15,.85],gap="large")
    with a:
        st.markdown("## One file. A tailored analysis.")
        st.write("Upload a spreadsheet or data export. DataPilot identifies dates, measures, categories and identifiers, checks data quality, and builds the right views from the columns it finds.")
        st.markdown('<div class="panel"><div class="panel-title">The difference</div><div class="muted">A fixed dashboard asks your file to fit its template. DataPilot first studies your file, then builds the analysis around it.</div></div>',unsafe_allow_html=True)
        st.markdown("### Built to adapt")
        st.write("Sales and commerce · customer data · operations · time series · workforce data · general tabular datasets")
    with b:
        st.markdown("### What happens after upload")
        for n,t,d in [("01","Understand","Detect column types, likely roles and dataset domain."),("02","Validate","Measure missingness, duplicates, constants and unusual values."),("03","Discover","Surface distributions, group patterns, time movement and relationships."),("04","Explain","Turn the strongest signals into readable findings and next steps.")]:
            st.markdown(f'<div class="panel"><div class="panel-title">{n} · {t}</div><div class="muted">{d}</div></div>',unsafe_allow_html=True)

if upload is not None:
    try:
        raw=load_any(upload)
        profile=profile_dataset(raw)
    except Exception as exc:
        st.error(f"DataPilot could not profile this file: {exc}")
        st.info("Check that the file contains a readable table with column headers.")
        st.stop()

    data=profile.data.copy()
    st.markdown(f"### {upload.name}")
    st.caption(f"{profile.dataset_kind} · {len(data):,} rows · {len(data.columns):,} columns · analysis adapted to detected fields")
    k1,k2,k3,k4,k5=st.columns(5)
    k1.metric("Records",f"{len(data):,}")
    k2.metric("Fields",f"{len(data.columns):,}")
    k3.metric("Numeric measures",f"{len(profile.numeric_columns):,}")
    k4.metric("Date fields",f"{len(profile.date_columns):,}")
    k5.metric("Missing cells",f"{profile.quality['missing_cells']:,}",f"{profile.quality['missing_pct']}% of all cells")

    tabs=st.tabs(["✦ Intelligence brief","⌁ Explore & compare","◷ Time analysis","◎ Relationships","✓ Data quality","↓ Export"])
    with tabs[0]:
        st.markdown("## What stands out")
        st.caption("Findings are calculated from the uploaded data. They describe patterns; they do not claim causes.")
        for item in profile.insights:
            st.markdown(f'<div class="insight"><small>{item["kind"]}</small><strong>{item["title"]}</strong><div>{item["detail"]}</div><div class="muted">Suggested next step: {item["action"]}</div></div>',unsafe_allow_html=True)
        if profile.numeric_columns:
            st.markdown("### Distribution snapshot")
            selected=st.selectbox("Choose a measure to inspect",profile.numeric_columns,key="dist_measure")
            fig=px.histogram(data,x=selected,marginal="box",nbins=35,color_discrete_sequence=["#7558f5"])
            fig.update_layout(height=390,margin=dict(t=20,b=15,l=10,r=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#39445c"))
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.info("No numeric measures were confidently detected. Use the data preview and column profile to inspect the fields.")

    with tabs[1]:
        st.markdown("## Ask the dataset a question")
        if profile.numeric_columns and profile.categorical_columns:
            c1,c2,c3=st.columns([1.2,1.2,1])
            with c1: group=st.selectbox("Break down by",profile.categorical_columns)
            with c2: measure=st.selectbox("Measure",profile.numeric_columns)
            with c3: agg=st.selectbox("Calculate",["sum","mean","median","count","min","max"])
            limit=st.slider("Number of groups to show",5,50,15)
            summary=grouped_summary(data,group,measure,agg).head(limit)
            fig=px.bar(summary.sort_values("value"),x="value",y=group,orientation="h",color="value",color_continuous_scale=["#ed75ad","#7558f5","#39c6c3"],hover_data={group:True,"value":":,.3f"})
            fig.update_layout(height=max(350,min(760,summary.shape[0]*32+100)),coloraxis_showscale=False,margin=dict(t=20,b=20,l=10,r=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig,use_container_width=True)
            st.dataframe(summary,use_container_width=True,hide_index=True)
            top=summary.iloc[0]
            st.success(f"Highest {agg} of {measure}: {top[group]} ({top['value']:,.3f}).")
        else:
            st.info("This view becomes available when the file contains at least one numeric measure and one category/identifier field.")
        st.markdown("### Interactive data filters")
        filter_col=st.selectbox("Filter records by field",["None"]+profile.categorical_columns,key="filter_col")
        filtered=data.copy()
        if filter_col!="None":
            options=sorted(data[filter_col].dropna().astype(str).unique().tolist())
            chosen=st.multiselect(f"Keep values in {filter_col}",options,default=options[:min(10,len(options))])
            filtered=filtered[filtered[filter_col].astype(str).isin(chosen)]
        st.caption(f"Showing {len(filtered):,} of {len(data):,} rows after filters.")
        st.dataframe(filtered.head(1000),use_container_width=True,hide_index=True)

    with tabs[2]:
        st.markdown("## Time intelligence")
        if profile.date_columns and profile.numeric_columns:
            dcol=st.selectbox("Date field",profile.date_columns)
            mcol=st.selectbox("Measure",profile.numeric_columns,key="time_measure")
            freq=st.segmented_control("Time grain",["Day","Week","Month","Quarter","Year"],default="Month")
            tagg=st.selectbox("Aggregation",["sum","mean","median","count"],key="time_agg")
            trend=time_summary(data,dcol,mcol,freq or "Month",tagg)
            fig=px.line(trend,x="period",y="value",markers=True,area=True,color_discrete_sequence=["#7558f5"])
            fig.update_traces(line=dict(width=3),fillcolor="rgba(117,88,245,.10)")
            fig.update_layout(hovermode="x unified",height=410,margin=dict(t=20,b=20,l=10,r=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig,use_container_width=True)
            st.dataframe(trend,use_container_width=True,hide_index=True)
            if len(trend)>=2:
                first=float(trend.iloc[0]["value"]); last=float(trend.iloc[-1]["value"])
                if first!=0:
                    st.info(f"First to last period change: {(last-first)/abs(first)*100:+.1f}% ({first:,.2f} → {last:,.2f}). This compares endpoints, not a forecast.")
        else:
            st.info("A reliable time analysis needs at least one detected date field and one numeric measure.")

    with tabs[3]:
        st.markdown("## Relationships between measures")
        if len(profile.numeric_columns)>=2:
            corr=profile.correlations
            fig=px.imshow(corr,text_auto=".2f",color_continuous_scale="RdBu",zmin=-1,zmax=1,aspect="auto")
            fig.update_layout(height=max(380,len(corr.columns)*48),margin=dict(t=25,b=20,l=20,r=20))
            st.plotly_chart(fig,use_container_width=True)
            st.caption("Correlation measures linear association between numeric columns. It does not establish causation.")
            xcol,ycol=st.columns(2)
            with xcol: x=st.selectbox("X axis",profile.numeric_columns,key="scatter_x")
            with ycol: y=st.selectbox("Y axis",[c for c in profile.numeric_columns if c!=x],key="scatter_y")
            color_options=["None"]+profile.categorical_columns
            color=st.selectbox("Color points by (optional)",color_options)
            fig=px.scatter(data,x=x,y=y,color=None if color=="None" else color,trendline="ols",opacity=.72)
            fig.update_layout(height=430,margin=dict(t=20,b=20,l=10,r=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.info("At least two numeric measures are needed to examine correlations and scatter relationships.")

    with tabs[4]:
        st.markdown("## Data quality & column intelligence")
        q=profile.quality
        q1,q2,q3,q4=st.columns(4)
        q1.metric("Exact duplicate rows",f"{q['duplicate_rows']:,}")
        q2.metric("Missing cells",f"{q['missing_cells']:,}")
        q3.metric("Columns with one value",f"{len(q['constant_columns']):,}")
        q4.metric("Complete cells",f"{data.notna().sum().sum():,}")
        st.markdown("### Detected field roles")
        st.dataframe(pd.DataFrame(profile.columns),use_container_width=True,hide_index=True)
        st.markdown("### Missing values by column")
        missing=data.isna().sum().sort_values(ascending=False)
        missing=missing[missing>0]
        if len(missing):
            mdf=missing.rename("missing_rows").reset_index().rename(columns={"index":"column"})
            fig=px.bar(mdf,x="missing_rows",y="column",orientation="h",color="missing_rows",color_continuous_scale=["#39c6c3","#7558f5"])
            fig.update_layout(height=max(260,len(mdf)*34),coloraxis_showscale=False,margin=dict(t=10,b=10,l=10,r=10))
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.success("No missing values were detected.")
        with st.expander("View duplicate records"):
            duplicates=data[data.duplicated(keep=False)]
            st.dataframe(duplicates,use_container_width=True,hide_index=True)
        with st.expander("View all source rows"):
            st.dataframe(data,use_container_width=True,hide_index=True)

    with tabs[5]:
        st.markdown("## Export your analysis")
        csv=data.to_csv(index=False).encode("utf-8-sig")
        profile_json=json.dumps({"dataset_kind":profile.dataset_kind,"quality":profile.quality,"columns":profile.columns,"insights":profile.insights},ensure_ascii=False,indent=2,default=str).encode("utf-8")
        e1,e2=st.columns(2)
        e1.download_button("↓ Analyzed dataset (CSV)",csv,"datapilot_analyzed_data.csv","text/csv",use_container_width=True)
        e2.download_button("↓ Profile & findings (JSON)",profile_json,"datapilot_data_profile.json","application/json",use_container_width=True)
        st.caption("Exports preserve the detected and converted data types where supported. Original source values are not overwritten in your uploaded file.")

    # Specialized sales module remains available when the uploaded file has the full sales schema.
    try:
        sales_frame=load_sales_file(BytesIO(upload.getvalue()),upload.name)
        sales=analyze_sales(sales_frame)
        with st.expander("Open specialized sales analysis"):
            ss=sales.summary
            c=st.columns(5)
            for col,label,val in zip(c,["Revenue","Gross profit","Gross margin","Orders","Average order value"],[ss["total_revenue"],ss["gross_profit"],ss["gross_margin_pct"],ss["order_count"],ss["average_order_value"]]):
                col.metric(label,"—" if val is None else (f"{val:,.2f}%" if label=="Gross margin" else f"{val:,.2f}" if label!="Orders" else f"{val:,}"))
            st.dataframe(sales.by_product,use_container_width=True,hide_index=True)
            st.download_button("Download detailed sales report",build_html_report(sales).encode("utf-8"),"datapilot_sales_report.html","text/html")
    except (ValueError, KeyError, TypeError):
        pass

    st.markdown("---")
    st.caption("DataPilot AI · Adaptive analysis from your data · No fabricated causes, forecasts or currency assumptions")
