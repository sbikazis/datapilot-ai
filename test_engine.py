import pandas as pd
import pytest
from engine import analyze_sales, map_columns, build_html_report


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


def test_html_report_contains_disclaimer_and_metrics():
    html = build_html_report(analyze_sales(sample()))
    assert "Gross profit" in html
    assert "not certified accounting advice" in html
