from __future__ import annotations

import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_time_figure(trend: pd.DataFrame) -> go.Figure:
    """Build a filled, interactive time-series chart from a time_summary result."""
    required = {"period", "value"}
    if not isinstance(trend, pd.DataFrame) or not required.issubset(trend.columns):
        raise ValueError("Time chart data must contain period and value columns.")

    clean = trend.loc[:, ["period", "value"]].copy()
    clean["period"] = pd.to_datetime(clean["period"], errors="coerce")
    clean["value"] = pd.to_numeric(clean["value"], errors="coerce")
    clean = clean.dropna(subset=["period", "value"])
    clean = clean.loc[clean["value"].map(lambda value: math.isfinite(float(value)))]
    clean = clean.sort_values("period")

    if clean.empty:
        raise ValueError("There are no valid observations to chart.")

    fig = px.line(
        clean,
        x="period",
        y="value",
        markers=True,
        color_discrete_sequence=["#7558F5"],
        labels={"period": "Period", "value": "Value"},
    )
    fig.update_traces(
        line={"width": 3, "shape": "spline"},
        fill="tozeroy",
        fillcolor="rgba(117,88,245,0.12)",
        marker={"size": 8, "line": {"width": 2, "color": "white"}},
        hovertemplate="%{x|%d %b %Y}<br><b>%{y:,.2f}</b><extra></extra>",
    )
    fig.update_layout(
        hovermode="x unified",
        height=410,
        margin={"t": 24, "b": 28, "l": 12, "r": 12},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "DM Sans, sans-serif", "color": "#39445C"},
        xaxis={"showgrid": False, "zeroline": False},
        yaxis={"gridcolor": "rgba(120,130,155,0.15)", "zeroline": False},
    )
    return fig
