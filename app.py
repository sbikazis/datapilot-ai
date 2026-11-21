import streamlit as st
from datapilot.engine import analyze_sales, build_html_report, load_sales_file

st.set_page_config(page_title="DataPilot AI", page_icon="📊", layout="wide")
st.title("📊 DataPilot AI")
st.caption("Turn a sales export into a clean dataset and an understandable business report.")
upload = st.file_uploader("Upload a CSV or Excel sales file", type=["csv", "xlsx", "xls"])
if upload:
    try:
        raw = load_sales_file(upload, upload.name)
        result = analyze_sales(raw)
        s = result.summary
        st.success(f"Analysis complete: {s['valid_rows']} valid rows; {s['rejected_rows']} rejected rows.")
        cols = st.columns(4)
        labels = [("Revenue", s["total_revenue"]), ("Gross profit", s["gross_profit"]), ("Gross margin", s["gross_margin_pct"]), ("Orders", s["order_count"])]
        for col, (label, value) in zip(cols, labels):
            shown = "—" if value is None else (f"{value:,.2f}%" if label == "Gross margin" else f"{value:,.2f}" if label != "Orders" else str(value))
            col.metric(label, shown)
        st.subheader("Product performance")
        st.dataframe(result.by_product, use_container_width=True)
        st.subheader("Monthly performance")
        st.dataframe(result.by_month, use_container_width=True)
        st.download_button("Download cleaned CSV", result.clean.to_csv(index=False).encode("utf-8-sig"), "datapilot_cleaned_sales.csv", "text/csv")
        st.download_button("Download rejected rows and reasons", result.rejected.to_csv(index=False).encode("utf-8-sig"), "datapilot_rejected_rows.csv", "text/csv")
        st.download_button("Download HTML report", build_html_report(result).encode("utf-8"), "datapilot_report.html", "text/html")
        with st.expander("Detected column mapping"):
            st.json(result.column_mapping)
    except Exception as exc:
        st.error(str(exc))
else:
    st.info("Upload a sales export to begin. Required fields: order ID, date, product, category, quantity, unit price and unit cost.")
    st.caption("Your file is processed in this app session. Avoid uploading unnecessary customer-identifying information.")
