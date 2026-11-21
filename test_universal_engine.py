import pandas as pd
import pytest

from universal_engine import profile_dataset, grouped_summary, time_summary


def test_profiles_mixed_dataset_and_detects_roles():
    frame = pd.DataFrame({
        "order_date": ["2026-01-01", "2026-02-01", "2026-03-01"],
        "region": ["North", "South", "North"],
        "revenue": ["1,200.50", "850.00", "950.00"],
        "units": [10, 7, 8],
    })
    profile = profile_dataset(frame)
    assert profile.dataset_kind == "Sales / commerce"
    assert "order_date" in profile.date_columns
    assert "revenue" in profile.numeric_columns
    assert "units" in profile.numeric_columns
    assert "region" in profile.categorical_columns
    assert profile.quality["rows"] == 3


def test_numeric_locale_conversion_is_conservative():
    frame = pd.DataFrame({"amount": ["1.234,50", "2.000,00", "850,25"], "label": ["a", "b", "c"]})
    profile = profile_dataset(frame)
    assert "amount" in profile.numeric_columns
    assert profile.data["amount"].tolist() == pytest.approx([1234.5, 2000.0, 850.25])


def test_grouped_summary_uses_selected_aggregation():
    frame = pd.DataFrame({"region": ["N", "N", "S"], "sales": [10, 15, 20]})
    result = grouped_summary(frame, "region", "sales", "sum")
    assert result.iloc[0]["region"] == "N" or result.iloc[0]["region"] == "S"
    values = dict(zip(result["region"], result["value"]))
    assert values == {"N": 25, "S": 20}


def test_time_summary_resamples_to_months():
    frame = pd.DataFrame({
        "when": pd.to_datetime(["2026-01-01", "2026-01-20", "2026-02-03"]),
        "value": [5, 7, 10],
    })
    result = time_summary(frame, "when", "value", "Month", "sum")
    assert len(result) == 2
    assert result["value"].tolist() == [12, 10]


def test_empty_dataset_is_rejected():
    with pytest.raises(ValueError, match="no rows"):
        profile_dataset(pd.DataFrame())
