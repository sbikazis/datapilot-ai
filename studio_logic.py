from __future__ import annotations

import csv
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



def build_evidence_findings(
    frame: pd.DataFrame,
    numeric_columns: Iterable[str],
    categorical_columns: Iterable[str],
    date_columns: Iterable[str],
    limit: int = 12,
) -> list[dict[str, str]]:
    """Create concise, evidence-bearing observations from the current role map."""
    if limit < 1:
        raise ValueError("limit must be positive.")
    numeric = [c for c in numeric_columns if c in frame]
    categorical = [c for c in categorical_columns if c in frame]
    dates = [c for c in date_columns if c in frame]
    findings: list[tuple[int, dict[str, str]]] = []

    total_cells = int(frame.size)
    missing_cells = int(frame.isna().sum().sum())
    if missing_cells:
        pct = missing_cells / max(1, total_cells) * 100
        findings.append((100, {
            "kind": "data quality",
            "title": f"{missing_cells:,} missing cells ({pct:.1f}%)",
            "detail": f"{missing_cells:,} of {total_cells:,} source cells are empty. Check whether missingness is concentrated in specific fields or groups.",
            "action": "Inspect missingness by field and segment",
        }))

    duplicates = int(frame.duplicated().sum())
    if duplicates:
        findings.append((95, {
            "kind": "data quality",
            "title": f"{duplicates:,} exact duplicate rows",
            "detail": f"{duplicates:,} of {len(frame):,} rows exactly match another row across all fields. Repeated rows may be valid repeated events; inspect before removing.",
            "action": "Review duplicate records and their business meaning",
        }))

    for col in numeric:
        stats = numeric_summary(frame[col])
        n = int(stats["count"])
        if not n:
            continue
        findings.append((65, {
            "kind": "measure",
            "title": f"{col}: {float(stats['sum']):,.3f} total",
            "detail": f"{n:,} valid observations; mean {float(stats['mean']):,.3f}, median {float(stats['median']):,.3f}, range {float(stats['min']):,.3f} to {float(stats['max']):,.3f}. Statistics use the currently filtered rows.",
            "action": f"Inspect the distribution and compare {col} across relevant groups",
        }))
        if int(stats["iqr_outliers"]):
            findings.append((75, {
                "kind": "distribution",
                "title": f"{int(stats['iqr_outliers']):,} potential extreme values in {col}",
                "detail": f"{int(stats['iqr_outliers']):,} of {n:,} valid observations fall outside the 1.5×IQR fences. This is a review flag, not proof of an error.",
                "action": f"Inspect extreme {col} values and their source records",
            }))

    for col in categorical:
        counts = frame[col].dropna().astype(str).value_counts()
        denominator = int(frame[col].notna().sum())
        if len(counts) > 1 and denominator >= 5:
            share = float(counts.iloc[0] / denominator * 100)
            if share >= 50:
                findings.append((55, {
                    "kind": "concentration",
                    "title": f"{counts.index[0]} represents {share:.1f}% of {col}",
                    "detail": f"The leading category appears in {int(counts.iloc[0]):,} of {denominator:,} non-empty records. A concentrated distribution can affect comparisons.",
                    "action": f"Compare the remaining groups in {col}",
                }))

    for col in dates:
        parsed = pd.to_datetime(frame[col], errors="coerce").dropna()
        if len(parsed) >= 2:
            findings.append((60, {
                "kind": "time coverage",
                "title": f"{col} spans {parsed.min().date()} to {parsed.max().date()}",
                "detail": f"{len(parsed):,} valid timestamps are available across {(parsed.max()-parsed.min()).days:,} calendar days. Coverage alone does not imply a trend.",
                "action": f"Choose a measure and inspect movement over {col}",
            }))

    for i, x in enumerate(numeric):
        for y in numeric[i + 1:]:
            corr, n = safe_correlation(frame, x, y)
            if corr is not None and abs(corr) >= .7:
                findings.append((70, {
                    "kind": "relationship",
                    "title": f"{x} and {y} have a strong linear association ({corr:+.2f})",
                    "detail": f"Pearson correlation is {corr:+.2f} across {n:,} paired observations. This describes linear association and does not establish causality.",
                    "action": f"Inspect the scatter plot for clusters, outliers and subgroup differences",
                }))

    findings.sort(key=lambda item: item[0], reverse=True)
    return [item for _, item in findings[:limit]]



def detect_delimiter(sample: str) -> str:
    """Detect common tabular delimiters conservatively, defaulting to comma."""
    if not sample.strip():
        return ","
    try:
        dialect = csv.Sniffer().sniff(sample[:8192], delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","
