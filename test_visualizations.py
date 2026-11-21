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


def test_time_figure_rejects_empty_or_invalid_data():
    with pytest.raises(ValueError, match="no valid observations"):
        build_time_figure(pd.DataFrame({"period": [], "value": []}))
    with pytest.raises(ValueError, match="period and value"):
        build_time_figure(pd.DataFrame({"date": [], "amount": []}))
