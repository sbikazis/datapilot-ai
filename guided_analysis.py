from __future__ import annotations

import math
from typing import Any

import pandas as pd


OBJECTIVES = {
    "measure_profile": "Understand a measure",
    "compare_groups": "Compare groups",
    "time_movement": "Explore change over time",
    "relationship": "Check a relationship",
    "quality_review": "Review data quality",
}


def available_guided_paths(
    numeric_columns: list[str],
    category_columns: list[str],
    date_columns: list[str],
) -> list[dict[str, Any]]:
    """Return only guided objectives supported by the detected field roles."""
    paths = [{"id": "quality_review", "label": OBJECTIVES["quality_review"], "required": []}]
    if numeric_columns:
        paths.append({"id": "measure_profile", "label": OBJECTIVES["measure_profile"], "required": ["measure"]})
    if numeric_columns and category_columns:
        paths.append({"id": "compare_groups", "label": OBJECTIVES["compare_groups"], "required": ["measure", "dimension"]})
    if numeric_columns and date_columns:
        paths.append({"id": "time_movement", "label": OBJECTIVES["time_movement"], "required": ["measure", "date"]})
    if len(numeric_columns) >= 2:
        paths.append({"id": "relationship", "label": OBJECTIVES["relationship"], "required": ["x_measure", "y_measure"]})
    return paths


def _numeric(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    return values.replace([float("inf"), float("-inf")], pd.NA).dropna()


def build_guided_result(
    frame: pd.DataFrame,
    objective: str,
    *,
    measure: str | None = None,
    dimension: str | None = None,
    date: str | None = None,
    x_measure: str | None = None,
    y_measure: str | None = None,
    min_group_size: int = 3,
) -> dict[str, Any]:
    """Build a deterministic, traceable result for one guided analysis objective."""
    if objective not in OBJECTIVES:
        raise ValueError("Unsupported guided analysis objective.")
    if min_group_size < 1:
        raise ValueError("min_group_size must be at least 1.")
    if frame.empty:
        return {"objective": objective, "status": "empty", "message": "No rows remain in the current view.", "summary": {}, "table": pd.DataFrame(), "source_indices": []}

    def require(field: str | None, label: str) -> str:
        if not field or field not in frame.columns:
            raise ValueError(f"Choose a valid {label} field from this dataset.")
        return field

    if objective == "quality_review":
        table = pd.DataFrame({
            "field": list(frame.columns),
            "missing": [int(frame[c].isna().sum()) for c in frame.columns],
            "missing_pct": [float(frame[c].isna().mean() * 100) for c in frame.columns],
            "distinct": [int(frame[c].nunique(dropna=True)) for c in frame.columns],
        }).sort_values(["missing_pct", "missing"], ascending=False).reset_index(drop=True)
        return {"objective": objective, "status": "ready", "message": "Field-level completeness and distinct-value profile.", "summary": {"rows": len(frame), "fields": len(frame.columns), "duplicate_rows": int(frame.duplicated().sum())}, "table": table, "source_indices": frame.index.tolist()}

    if objective == "measure_profile":
        field = require(measure, "measure")
        values = _numeric(frame[field])
        if values.empty:
            return {"objective": objective, "status": "limited", "message": "No valid numeric observations remain for this measure.", "summary": {"valid_values": 0}, "table": pd.DataFrame(), "source_indices": []}
        quantiles = values.quantile([.25, .5, .75, .9])
        summary = {"valid_values": int(values.size), "missing_or_invalid": int(len(frame) - values.size), "mean": float(values.mean()), "median": float(values.median()), "minimum": float(values.min()), "maximum": float(values.max()), "p25": float(quantiles.loc[.25]), "p75": float(quantiles.loc[.75]), "p90": float(quantiles.loc[.9])}
        valid_index = values.index.tolist()
        return {"objective": objective, "status": "ready", "message": f"Descriptive profile of {field}; no causal or predictive claim is made.", "summary": summary, "table": pd.DataFrame([{"measure": field, **summary}]), "source_indices": valid_index}

    if objective == "compare_groups":
        measure_field = require(measure, "measure")
        dimension_field = require(dimension, "dimension")
        work = pd.DataFrame({"group": frame[dimension_field], "value": _numeric(frame[measure_field])})
        work = work.dropna(subset=["group", "value"])
        grouped = work.groupby("group", dropna=False)["value"].agg(records="count", mean="mean", median="median").reset_index()
        grouped = grouped[grouped["records"] >= min_group_size].sort_values("median", ascending=False).reset_index(drop=True)
        eligible = set(grouped["group"].tolist())
        indices = frame.index[frame[dimension_field].isin(eligible) & _numeric(frame[measure_field]).reindex(frame.index).notna()].tolist()
        status = "ready" if not grouped.empty else "limited"
        return {"objective": objective, "status": status, "message": f"Groups smaller than {min_group_size} valid records are suppressed. Values describe differences, not causes.", "summary": {"eligible_groups": len(grouped), "valid_records": len(work)}, "table": grouped, "source_indices": indices}

    if objective == "time_movement":
        measure_field = require(measure, "measure")
        date_field = require(date, "date")
        work = pd.DataFrame({"date": pd.to_datetime(frame[date_field], errors="coerce", format="mixed"), "value": pd.to_numeric(frame[measure_field], errors="coerce")}, index=frame.index)
        work["value"] = work["value"].replace([float("inf"), float("-inf")], pd.NA)
        work = work.dropna()
        if work.empty:
            return {"objective": objective, "status": "limited", "message": "No valid date-and-measure pairs remain.", "summary": {"valid_records": 0}, "table": pd.DataFrame(), "source_indices": []}
        work["period"] = work["date"].dt.to_period("M").dt.to_timestamp()
        table = work.groupby("period")["value"].agg(records="count", mean="mean", median="median").reset_index()
        return {"objective": objective, "status": "ready", "message": "Monthly descriptive movement. Missing periods are not filled with zero; this view does not forecast.", "summary": {"valid_records": len(work), "periods": len(table)}, "table": table, "source_indices": work.index.tolist()}

    x_field = require(x_measure, "X measure")
    y_field = require(y_measure, "Y measure")
    if x_field == y_field:
        raise ValueError("Choose two different numeric measures.")
    pairs = pd.DataFrame({"x": _numeric(frame[x_field]), "y": _numeric(frame[y_field])}).dropna()
    corr = None
    if len(pairs) >= 3 and pairs["x"].nunique() > 1 and pairs["y"].nunique() > 1:
        corr = float(pairs["x"].corr(pairs["y"]))
    table = pd.DataFrame([{"x_measure": x_field, "y_measure": y_field, "paired_records": len(pairs), "pearson_correlation": corr}])
    return {"objective": objective, "status": "ready" if corr is not None else "limited", "message": "Correlation describes linear association only; it does not establish causation.", "summary": {"paired_records": len(pairs), "pearson_correlation": corr}, "table": table, "source_indices": pairs.index.tolist()}
