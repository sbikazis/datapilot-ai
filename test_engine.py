import pandas as pd
import pytest
from engine import analyze_sales, map_columns, build_html_report, load_sales_file


def sample():
    return pd.DataFrame({
        "Order ID": ["A1", "A1", "A2", "A3"],
        "Date": ["2026-01-02", "2026-01-02", "2026-01-03", "not-a-date"],
        "Product Name": ["Tea", "Cake", "Tea", "Bad row"],
        "Category": ["Drinks", "Food", "Drinks", "Other"],
        "Qty": [2, 1, 3, 1],
        "Selling Price": [10, 20, 10, 5],
        "Cost Price": [4, 8, 4, 1],
    })


def test_metrics_and_rejections_are_correct():
    result = analyze_sales(sample())
    assert result.summary["valid_rows"] == 3
    assert result.summary["rejected_rows"] == 1
    assert result.summary["total_revenue"] == 70
    assert result.summary["total_cost"] == 28
    assert result.summary["gross_profit"] == 42
    assert result.summary["gross_margin_pct"] == pytest.approx(60)
    assert result.summary["average_order_value"] == pytest.approx(35)
    assert "order_date is missing or invalid" in result.rejected.iloc[0]["rejection_reason"]


def test_alias_mapping():
    mapped, mapping = map_columns(pd.DataFrame(columns=["Order ID", "Date", "Qty"]))
    assert list(mapped.columns) == ["order_id", "order_date", "quantity"]
    assert mapping["Order ID"] == "order_id"


def test_duplicate_alias_is_rejected():
    with pytest.raises(ValueError, match="map to 'quantity'"):
        map_columns(pd.DataFrame(columns=["qty", "quantity"]))


def test_empty_valid_dataset_is_not_silently_accepted():
    frame = sample()
    frame["Date"] = "invalid"
    with pytest.raises(ValueError, match="No valid sales rows"):
        analyze_sales(frame)


def test_html_report_contains_metrics_and_all_breakdowns():
    html = build_html_report(analyze_sales(sample()))
    assert "Gross profit" in html
    assert "Category performance" in html
    assert "Average order value" in html
    assert "not certified accounting advice" in html


def test_infinite_numeric_values_are_rejected():
    frame = sample()
    frame["Selling Price"] = frame["Selling Price"].astype(float)
    frame.loc[0, "Selling Price"] = float("inf")
    result = analyze_sales(frame)
    assert result.summary["valid_rows"] == 2
    assert "unit_price must be a finite number" in result.rejected.iloc[0]["rejection_reason"]


def test_text_fields_are_trimmed_before_grouping():
    frame = sample().iloc[:3].copy()
    frame.loc[0, "Product Name"] = " Tea "
    result = analyze_sales(frame)
    assert set(result.clean["product"]) == {"Tea", "Cake"}


def test_csv_upload_loads_and_maps_headers():
    from io import BytesIO
    csv_data = b"Order ID,Date,Product Name,Category,Qty,Selling Price,Cost Price\nA1,2026-01-02,Tea,Drinks,2,10,4\n"
    loaded = load_sales_file(BytesIO(csv_data), "sample.csv")
    assert "order_id" in loaded.columns
    assert loaded.iloc[0]["product"] == "Tea"


def test_missing_required_columns_are_reported():
    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_sales(pd.DataFrame({"order_id": ["A1"]}))
