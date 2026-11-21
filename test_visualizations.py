import pandas as pd
import pytest

from visualizations import build_time_figure


def test_time_figure_builds_filled_interactive_line_without_unsupported_arguments():
    trend = pd.DataFrame({
        "period": pd.to_datetime(["2026-10-01", "2026-10-02", "2026-10-03"]),
        "value": [12.0, 18.0, 15.0],
    })
    figure = build_time_figure(trend)
    assert len(figure.data) == 1
    assert figure.data[0].type == "scatter"
    assert figure.data[0].fill == "tozeroy"
    assert figure.data[0].mode == "lines+markers"


def test_time_figure_rejects_empty_or_missing_required_columns():
    with pytest.raises(ValueError, match="no valid observations"):
        build_time_figure(pd.DataFrame({"period": [], "value": []}))
    with pytest.raises(ValueError, match="period and value"):
        build_time_figure(pd.DataFrame({"date": [], "amount": []}))


def test_time_figure_discards_invalid_dates_nulls_and_non_finite_values():
    trend = pd.DataFrame({
        "period": ["2026-10-02", "not-a-date", "2026-10-01", "2026-10-03"],
        "value": ["18", "22", None, float("inf")],
    })
    figure = build_time_figure(trend)
    assert len(figure.data[0].x) == 1
    assert list(figure.data[0].y) == [18]


def test_time_figure_supports_a_single_valid_observation():
    trend = pd.DataFrame({"period": ["2026-10-01"], "value": ["42.5"]})
    figure = build_time_figure(trend)
    assert list(figure.data[0].y) == [42.5]
