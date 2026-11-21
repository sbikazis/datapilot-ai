from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import math
import re

import pandas as pd


DATE_HINTS = ("date", "time", "timestamp", "created", "updated", "month", "year", "day")
ID_HINTS = ("id", "code", "sku", "zip", "postal", "phone", "account", "number")
MEASURE_HINTS = ("amount", "revenue", "sales", "price", "cost", "profit", "total", "quantity", "qty", "count", "score", "value", "age", "duration")


@dataclass
class DatasetProfile:
    data: pd.DataFrame
    columns: list[dict[str, Any]]
    numeric_columns: list[str]
    categorical_columns: list[str]
    date_columns: list[str]
    insights: list[dict[str, str]]
    quality: dict[str, Any]
    correlations: pd.DataFrame
    dataset_kind: str


def _name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _date_candidate(series: pd.Series, column: str) -> pd.Series | None:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")
    name_hint = any(h in _name(column) for h in DATE_HINTS)
    text = series.astype("string").str.strip()
    iso = text.str.match(r"^\d{4}-\d{1,2}-\d{1,2}(?:[T\s].*)?$", na=False)
    if not name_hint and (not len(text) or iso.mean() < 0.85):
        return None
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    if iso.any():
        parsed.loc[iso] = pd.to_datetime(text.loc[iso], errors="coerce", format="mixed")
    rest = ~iso
    if name_hint and rest.any():
        parsed.loc[rest] = pd.to_datetime(text.loc[rest], errors="coerce", dayfirst=True, format="mixed")
    ratio = parsed.notna().mean() if len(parsed) else 0
    return parsed if ratio >= (0.65 if name_hint else 0.85) else None


def _parse_number(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    text = str(value).strip().replace("\u00a0", "").replace(" ", "")
    if not text:
        return None
    text = re.sub(r"[^0-9, .+-]", "", text).replace(" ", "")
    if not text or not re.search(r"\d", text):
        return None
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        parts = text.split(",")
        if len(parts) == 2 and len(parts[1]) == 3 and parts[0].lstrip("+-").isdigit():
            text = "".join(parts)
        elif len(parts) > 2 and all(len(part) == 3 for part in parts[1:]):
            text = "".join(parts)
        else:
            text = text.replace(",", ".")
    if text.count(".") > 1:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _numeric_candidate(series: pd.Series, column: str) -> pd.Series | None:
    if pd.api.types.is_numeric_dtype(series):
        values = pd.to_numeric(series, errors="coerce")
        finite = values.map(lambda x: math.isfinite(float(x)) if pd.notna(x) else False)
        values = values.where(finite)
    else:
        # pandas 3.x may infer plain text columns as dtype "str", not "object".
        # Use pandas' dtype predicate so locale-formatted numeric strings are profiled
        # consistently across pandas versions.
        if not pd.api.types.is_string_dtype(series.dtype) and series.dtype != "object":
            return None
        values = series.map(_parse_number).astype("Float64")
    ratio = values.notna().mean() if len(values) else 0
    hint = any(h in _name(column) for h in MEASURE_HINTS)
    threshold = 0.65 if hint else 0.9
    return values if ratio >= threshold else None

def _safe_top(series: pd.Series) -> tuple[str, int] | None:
    counts = series.dropna().astype(str).value_counts()
    if counts.empty:
        return None
    return str(counts.index[0]), int(counts.iloc[0])


def profile_dataset(frame: pd.DataFrame) -> DatasetProfile:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError("The uploaded file has no rows to analyze.")
    if len(frame.columns) == 0:
        raise ValueError("The uploaded file has no columns.")
    data = frame.copy()
    data.columns = [str(c).strip() or f"unnamed_{i+1}" for i, c in enumerate(data.columns)]
    if data.columns.duplicated().any():
        duplicates = data.columns[data.columns.duplicated()].tolist()
        raise ValueError(f"Duplicate column names found: {duplicates}. Rename them and upload again.")

    numeric: list[str] = []
    categorical: list[str] = []
    dates: list[str] = []
    metadata: list[dict[str, Any]] = []
    for col in data.columns:
        original = data[col]
        parsed_date = _date_candidate(original, col)
        parsed_num = None if parsed_date is not None else _numeric_candidate(original, col)
        missing = int(original.isna().sum())
        unique = int(original.nunique(dropna=True))
        if parsed_date is not None:
            data[col] = parsed_date
            dates.append(col)
            role = "Date / time"
        elif parsed_num is not None and not any(h in _name(col) for h in ID_HINTS):
            data[col] = parsed_num
            numeric.append(col)
            role = "Numeric measure"
        else:
            categorical.append(col)
            role = "Identifier / category" if any(h in _name(col) for h in ID_HINTS) else "Category / text"
        metadata.append({
            "column": col, "detected_type": str(data[col].dtype), "role": role,
            "non_empty": int(original.notna().sum()), "missing": missing,
            "missing_pct": round(missing / len(data) * 100, 1),
            "unique_values": unique, "unique_pct": round(unique / max(1, original.notna().sum()) * 100, 1),
        })

    insights: list[dict[str, str]] = []
    quality = {
        "rows": int(len(data)), "columns": int(len(data.columns)),
        "duplicate_rows": int(data.duplicated().sum()),
        "missing_cells": int(data.isna().sum().sum()),
        "missing_pct": round(data.isna().sum().sum() / max(1, data.size) * 100, 1),
        "constant_columns": [c for c in data.columns if data[c].nunique(dropna=True) <= 1],
    }
    if quality["duplicate_rows"]:
        insights.append({"kind": "quality", "title": "Duplicate records detected", "detail": f"{quality['duplicate_rows']:,} exact duplicate rows were found. Check whether they represent repeated events before removing them.", "action": "Review duplicate rows"})
    if quality["missing_cells"]:
        insights.append({"kind": "quality", "title": "Missing values need attention", "detail": f"{quality['missing_cells']:,} cells ({quality['missing_pct']}% of the dataset) are empty. Missingness may affect comparisons and totals.", "action": "Inspect missing-value patterns"})
    if quality["constant_columns"]:
        insights.append({"kind": "quality", "title": "Columns with no variation", "detail": "These columns contain one value or no usable values: " + ", ".join(quality["constant_columns"][:8]), "action": "Consider excluding them from comparisons"})

    for col in numeric:
        values = data[col].dropna()
        if values.empty:
            continue
        total = float(values.sum())
        mean = float(values.mean())
        median = float(values.median())
        std = float(values.std()) if len(values) > 1 else 0.0
        if math.isfinite(total) and any(h in _name(col) for h in ("revenue", "sales", "amount", "total", "profit", "cost")):
            insights.append({"kind": "metric", "title": f"{col}: {total:,.2f} total", "detail": f"{len(values):,} valid values; average {mean:,.2f}, median {median:,.2f}. The mean/median gap can reveal skew or unusually large records.", "action": f"Compare the distribution of {col}"})
        if std > 0:
            z = (values - mean).abs() / std
            outliers = int((z > 3).sum())
            if outliers:
                insights.append({"kind": "anomaly", "title": f"Unusual values in {col}", "detail": f"{outliers:,} value(s) are more than three standard deviations from the mean. These may be genuine extremes or data-entry issues.", "action": f"Inspect extreme {col} records"})

    for col in categorical:
        if col not in data:
            continue
        top = _safe_top(data[col])
        if top and top[1] / max(1, data[col].notna().sum()) >= 0.5 and data[col].nunique(dropna=True) > 1:
            insights.append({"kind": "pattern", "title": f"{top[0]} dominates {col}", "detail": f"This value appears in {top[1]:,} rows ({top[1] / max(1, data[col].notna().sum()) * 100:.1f}% of non-empty records). The dataset may be imbalanced across groups.", "action": f"Compare groups in {col}"})

    for col in dates:
        valid = data[col].dropna()
        if len(valid) >= 2:
            insights.append({"kind": "trend", "title": f"Time coverage: {col}", "detail": f"Records span {valid.min().date()} to {valid.max().date()}. Use a time aggregation to explore movement and seasonality.", "action": f"Explore trends over {col}"})

    corr = data[numeric].corr(numeric_only=True) if len(numeric) >= 2 else pd.DataFrame()
    if not corr.empty:
        pairs = []
        for i, a in enumerate(numeric):
            for b in numeric[i+1:]:
                value = corr.loc[a, b]
                if pd.notna(value) and abs(float(value)) >= 0.7:
                    pairs.append((a, b, float(value)))
        for a, b, value in sorted(pairs, key=lambda x: abs(x[2]), reverse=True)[:4]:
            insights.append({"kind": "relationship", "title": f"{a} and {b} move together", "detail": f"Correlation is {value:.2f}. This is an association, not proof that one variable causes the other.", "action": "Investigate the relationship"})

    if not insights:
        insights.append({"kind": "neutral", "title": "No strong automatic signal found yet", "detail": "The dataset is profiled, but the current columns do not support a reliable standout pattern. Try selecting a measure and grouping column.", "action": "Explore the data interactively"})

    names = " ".join(_name(c) for c in data.columns)
    if any(word in names for word in ("order", "invoice", "sales", "revenue", "product", "quantity")):
        kind = "Sales / commerce"
    elif any(word in names for word in ("customer", "client", "user", "segment")):
        kind = "Customer / audience"
    elif any(word in names for word in ("employee", "salary", "department", "staff")):
        kind = "People / workforce"
    elif dates and numeric:
        kind = "Time-series / operational"
    elif numeric:
        kind = "Numeric / performance"
    else:
        kind = "General / mixed data"

    return DatasetProfile(data, metadata, numeric, categorical, dates, insights, quality, corr, kind)


def grouped_summary(data: pd.DataFrame, group_by: str, measure: str, aggregation: str = "sum") -> pd.DataFrame:
    if group_by not in data or measure not in data:
        raise ValueError("Choose valid columns for the comparison.")
    if aggregation not in {"sum", "mean", "median", "min", "max", "count"}:
        raise ValueError("Unsupported aggregation.")
    if aggregation == "count":
        result = data.groupby(group_by, dropna=False)[measure].count().rename("value")
    else:
        result = data.groupby(group_by, dropna=False)[measure].agg(aggregation).rename("value")
    return result.reset_index().sort_values("value", ascending=False)


def time_summary(data: pd.DataFrame, date_col: str, measure: str, frequency: str = "Month", aggregation: str = "sum") -> pd.DataFrame:
    if date_col not in data or measure not in data:
        raise ValueError("Choose valid date and measure columns.")
    freq = {"Day": "D", "Week": "W", "Month": "MS", "Quarter": "QS", "Year": "YS"}.get(frequency)
    if not freq:
        raise ValueError("Unsupported time frequency.")
    work = data[[date_col, measure]].dropna().copy()
    work["_period"] = work[date_col].dt.to_period({"D":"D","W":"W","MS":"M","QS":"Q","YS":"Y"}[freq]).dt.start_time
    return work.groupby("_period")[measure].agg(aggregation).reset_index().rename(columns={"_period": "period", measure: "value"}).sort_values("period")
