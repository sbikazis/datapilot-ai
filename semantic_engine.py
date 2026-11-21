from __future__ import annotations

import re
from typing import Any

import pandas as pd


CURRENCY_HINTS = ("amount", "revenue", "sales", "price", "cost", "profit", "budget", "spend", "salary", "wage", "balance", "subtotal", "total")
PERCENT_HINTS = ("percent", "percentage", "pct", "margin", "rate", "ratio", "share", "conversion")
DURATION_HINTS = ("duration", "elapsed", "latency", "runtime", "time_spent", "seconds", "minutes", "hours", "days_to")
ID_HINTS = ("id", "uuid", "sku", "code", "account", "phone", "postal", "zip")


def infer_semantic_fields(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Infer cautious semantic labels without assuming currency, units or business meaning."""
    result: list[dict[str, Any]] = []
    for column in frame.columns:
        series = frame[column]
        name = re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_")
        values = series.dropna()
        text_values = values.astype(str).str.strip().str.lower()
        unique = set(text_values.unique().tolist())
        tokens = set(name.split("_"))
        currency_symbols = bool(len(text_values) and text_values.str.contains(r"[$€£¥]", regex=True).mean() >= 0.5)
        semantic = "Text / category"
        confidence = "medium"
        reason = "No stronger semantic signal was detected."
        unit_hint = "Not inferred"

        if pd.api.types.is_datetime64_any_dtype(series) or any(token in name for token in ("date", "timestamp", "datetime", "created_at", "updated_at")):
            semantic, confidence = "Date / time", "high"
            reason = "The field name or stored dtype indicates a temporal value."
        elif any(token in tokens for token in ("latitude", "lat", "longitude", "lon", "lng")):
            semantic, confidence = ("Latitude" if any(t in tokens for t in ("latitude", "lat")) else "Longitude"), "high"
            reason = "The field name explicitly identifies a geographic coordinate."
            unit_hint = "Decimal degrees (verify coordinate reference)"
        elif any(token in name for token in ("email", "e_mail")):
            semantic, confidence = "Email identifier", "high"
            reason = "The field name indicates an email address; treat values as personal data."
        elif any(token in name for token in ("url", "website", "web_link")):
            semantic, confidence = "URL / link", "high"
            reason = "The field name indicates a web address."
        elif pd.api.types.is_bool_dtype(series) or (unique and unique.issubset({"true", "false", "yes", "no", "y", "n"})):
            semantic, confidence = "Boolean / flag", "high"
            reason = "Values are boolean-like."
        elif any(token in name for token in PERCENT_HINTS):
            semantic, confidence = "Percentage / rate", "high"
            reason = "The field name indicates a rate, share or percentage."
            unit_hint = "Scale not assumed; verify whether values use 0–1 or 0–100"
        elif any(token in name for token in DURATION_HINTS):
            semantic, confidence = "Duration", "high"
            reason = "The field name indicates elapsed time or duration."
            unit_hint = "Unit inferred only from the column name; verify"
        elif any(token in tokens for token in CURRENCY_HINTS) or currency_symbols:
            semantic, confidence = "Currency-like amount", "medium"
            reason = "The field name or values suggest an amount, but the currency is unknown."
            unit_hint = "Currency not identified"
        elif any(token in name for token in ("phone", "mobile", "telephone")):
            semantic, confidence = "Phone identifier", "high"
            reason = "The field name indicates a phone/contact identifier; treat values as personal data."
        elif any(token in name for token in ("postal", "postcode", "zip")):
            semantic, confidence = "Postal code", "high"
            reason = "The field name indicates a postal identifier; preserve leading zeros."
        elif any(token in name for token in ID_HINTS):
            semantic, confidence = "Identifier / code", "high"
            reason = "The field name suggests an identifier rather than a measure."
        elif pd.api.types.is_numeric_dtype(series):
            semantic, confidence = "Numeric measure", "medium"
            reason = "The stored values are numeric; their business meaning is not assumed."
        elif len(values) and values.nunique() / max(1, len(values)) > 0.9:
            semantic, confidence = "High-cardinality text", "medium"
            reason = "Most non-empty values are unique; this may be an identifier or free text."

        result.append({
            "column": str(column),
            "semantic_type": semantic,
            "semantic_confidence": confidence,
            "semantic_reason": reason,
            "unit_hint": unit_hint,
        })
    return result
