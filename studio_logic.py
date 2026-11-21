from __future__ import annotations

import math
from typing import Iterable

import pandas as pd


def recommend_visualization(
    numeric_columns: Iterable[str],
    categorical_columns: Iterable[str],
    date_columns: Iterable[str],
) -> tuple[str, str]:
    numeric = list(numeric_columns)
    categorical = list(categorical_columns)
    dates = list(date_columns)
    if dates and numeric:
        return "Time trend", "A date field and numeric measure support movement over time."
    if categorical and numeric:
        return "Ranked comparison", "A category and numeric measure support a group comparison."
    if len(numeric) >= 2:
        return "Relationship scatter", "Two numeric measures support a relationship view."
    if numeric:
        return "Distribution", "A numeric measure supports distribution and spread analysis."
    if categorical:
        return "Category frequency", "Categorical fields support frequency and composition analysis."
    return "Data quality review", "No measure or dimension was confidently detected; begin with the field profile."


def numeric_summary(values: pd.Series) -> dict[str, float | int | None]:
    series = pd.to_numeric(values, errors="coerce")
    series = series[series.map(lambda x: math.isfinite(float(x)) if pd.notna(x) else False)].dropna()
    if series.empty:
        return {
            "count": 0, "sum": None, "mean": None, "median": None, "std": None,
            "min": None, "q1": None, "q3": None, "p90": None, "max": None,
            "iqr_outliers": 0,
        }
    q1, q3 = float(series.quantile(.25)), float(series.quantile(.75))
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return {
        "count": int(series.count()),
        "sum": float(series.sum()),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "std": float(series.std()) if len(series) > 1 else 0.0,
        "min": float(series.min()),
        "q1": q1,
        "q3": q3,
        "p90": float(series.quantile(.9)),
        "max": float(series.max()),
        "iqr_outliers": int(((series < lower) | (series > upper)).sum()),
    }


def safe_correlation(frame: pd.DataFrame, x: str, y: str) -> tuple[float | None, int]:
    if x not in frame or y not in frame:
        raise ValueError("Both selected fields must exist in the dataset.")
    pair = frame[[x, y]].apply(pd.to_numeric, errors="coerce").replace([float("inf"), float("-inf")], pd.NA).dropna()
    if len(pair) < 3 or pair[x].nunique() < 2 or pair[y].nunique() < 2:
        return None, int(len(pair))
    value = float(pair[x].corr(pair[y]))
    return (value if math.isfinite(value) else None), int(len(pair))


def category_summary(values: pd.Series, top_n: int = 20) -> pd.DataFrame:
    if top_n < 1:
        raise ValueError("top_n must be positive.")
    series = values.astype("string").fillna("(Missing)")
    counts = series.value_counts(dropna=False).head(top_n)
    total = int(series.shape[0])
    result = counts.rename("records").rename_axis("category").reset_index()
    result["share_pct"] = (result["records"] / max(1, total) * 100).round(2)
    return result
