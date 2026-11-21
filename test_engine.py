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
    assert "not certified accounting software" in html


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


def test_iso_dates_are_not_misread_as_day_first():
    frame = pd.DataFrame({
        "order_id": [f"ISO-{day:02d}" for day in range(1, 21)],
        "order_date": [f"2026-10-{day:02d}" for day in range(1, 21)],
        "product": ["Widget"] * 20,
        "category": ["Test"] * 20,
        "quantity": [1] * 20,
        "unit_price": [10] * 20,
        "unit_cost": [4] * 20,
    })
    result = analyze_sales(frame)
    assert result.summary["valid_rows"] == 20
    assert result.summary["rejected_rows"] == 0
    assert result.clean["order_date"].dt.month.eq(10).all()
    assert result.clean["order_date"].dt.day.tolist() == list(range(1, 21))


def test_decimal_comma_and_thousands_separators():
    frame = sample().iloc[:1].copy()
    frame["Selling Price"] = ["1.234,50"]
    frame["Cost Price"] = ["1.000,25"]
    result = analyze_sales(frame)
    assert result.clean.iloc[0]["unit_price"] == pytest.approx(1234.50)
    assert result.clean.iloc[0]["unit_cost"] == pytest.approx(1000.25)


def test_duplicate_order_ids_are_counted_once():
    result = analyze_sales(sample())
    # A3 is rejected for its invalid date; the two valid A1 rows count as one order.
    assert result.summary["order_count"] == 2


def test_full_twenty_row_demo_file_is_fully_accepted_with_expected_totals():
    frame = pd.DataFrame({
        "order_id": [f"ORD-{1001+i}" for i in range(20)],
        "order_date": [f"2026-10-{day:02d}" for day in range(1, 21)],
        "product": [
            "Wireless Mouse", "Notebook A5", "USB-C Cable", "Coffee Mug", "Desk Lamp",
            "Wireless Mouse", "Notebook A5", "Phone Stand", "USB-C Cable", "Water Bottle",
            "Coffee Mug", "Desk Lamp", "Notebook A5", "Phone Stand", "Wireless Mouse",
            "Water Bottle", "USB-C Cable", "Coffee Mug", "Desk Lamp", "Notebook A5",
        ],
        "category": [
            "Electronics", "Stationery", "Electronics", "Home", "Home",
            "Electronics", "Stationery", "Accessories", "Electronics", "Accessories",
            "Home", "Home", "Stationery", "Accessories", "Electronics",
            "Accessories", "Electronics", "Home", "Home", "Stationery",
        ],
        "quantity": [2,5,3,4,1,1,8,2,6,3,2,2,4,5,3,2,4,3,1,6],
        "unit_price": [18.5,3.2,7.9,6.5,32,18.5,3.2,11,7.9,14,6.5,32,3.2,11,18.5,14,7.9,6.5,32,3.2],
        "unit_cost": [9,1.1,3.25,2.4,18,9,1.1,4.5,3.25,6.75,2.4,18,1.1,4.5,9,6.75,3.25,2.4,18,1.1],
    })
    result = analyze_sales(frame)
    assert result.summary["valid_rows"] == 20
    assert result.summary["rejected_rows"] == 0
    assert result.summary["total_revenue"] == pytest.approx(620.80)
    assert result.summary["total_cost"] == pytest.approx(280.40)
    assert result.summary["gross_profit"] == pytest.approx(340.40)
    assert result.summary["gross_margin_pct"] == pytest.approx(54.8324742268)
    assert result.summary["order_count"] == 20
    assert result.summary["average_order_value"] == pytest.approx(31.04)


def test_malformed_numeric_value_is_rejected_with_row_reason():
    frame = sample().iloc[:2].copy()
    frame["Selling Price"] = frame["Selling Price"].astype("string")
    frame.loc[0, "Selling Price"] = "12-3"
    result = analyze_sales(frame)
    assert result.summary["valid_rows"] == 1
    assert result.summary["rejected_rows"] == 1
    assert "unit_price is missing or not numeric" in result.rejected.iloc[0]["rejection_reason"]
