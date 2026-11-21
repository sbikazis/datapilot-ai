import pandas as pd
import pytest

from time_intelligence import analyze_time_series


def test_detects_missing_months_without_filling_them_as_zero():
    frame = pd.DataFrame({
        "period": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-04-01", "2025-05-01"]),
        "value": [10, 12, 11, 13],
    })
    result = analyze_time_series(frame)
    assert result["missing_periods"] == 1
    finding = next(x for x in result["findings"] if x["kind"] == "coverage")
    assert "not treated as zero" in finding["detail"]


def test_suppresses_comparison_for_small_samples():
    frame = pd.DataFrame({"period": pd.date_range("2025-01-01", periods=3, freq="MS"), "value": [1, 2, 20]})
    result = analyze_time_series(frame)
    assert not result["eligible_for_comparison"]
    assert any("More periods" in x["title"] for x in result["findings"])
    assert not any(x["kind"] == "change anomaly" for x in result["findings"])


def test_detects_material_shift_between_halves():
    frame = pd.DataFrame({
        "period": pd.date_range("2025-01-01", periods=8, freq="MS"),
        "value": [10, 11, 9, 10, 20, 21, 19, 22],
    })
    result = analyze_time_series(frame)
    assert result["eligible_for_comparison"]
    assert any(x["kind"] == "trend shift" for x in result["findings"])


def test_detects_large_change_using_robust_baseline():
    frame = pd.DataFrame({
        "period": pd.date_range("2025-01-01", periods=9, freq="MS"),
        "value": [10, 10, 11, 10, 10, 50, 51, 50, 52],
    })
    result = analyze_time_series(frame)
    assert any(x["kind"] == "change anomaly" for x in result["findings"])


def test_ignores_null_and_infinite_values_and_sorts_periods():
    frame = pd.DataFrame({
        "period": pd.to_datetime(["2025-03-01", "2025-01-01", "2025-02-01", "2025-04-01"]),
        "value": [3, 1, float("inf"), None],
    })
    result = analyze_time_series(frame)
    assert result["valid_periods"] == 2
    assert result["series"]["period"].is_monotonic_increasing


def test_empty_series_returns_safe_result():
    result = analyze_time_series(pd.DataFrame({"period": [None], "value": [None]}))
    assert result["valid_periods"] == 0
    assert result["findings"] == []


@pytest.mark.parametrize("kwargs", [{"min_periods": 3}, {"change_threshold": 0}])
def test_rejects_invalid_thresholds(kwargs):
    with pytest.raises(ValueError):
        analyze_time_series(pd.DataFrame({"period": [], "value": []}), **kwargs)
