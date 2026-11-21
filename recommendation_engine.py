from __future__ import annotations

import re
from typing import Any, Iterable


_KIND_WEIGHT = {
    "data quality": 1.00,
    "change anomaly": 0.96,
    "trend shift": 0.90,
    "segment difference": 0.88,
    "relationship": 0.78,
    "distribution": 0.74,
    "concentration": 0.70,
    "time coverage": 0.55,
    "measure": 0.45,
    "coverage": 0.40,
}


def _sample_size(finding: dict[str, Any]) -> int | None:
    text = " ".join(str(finding.get(key, "")) for key in ("detail", "title"))
    # For "24 of 40 valid observations", use the group sample (24), not
    # the overall denominator (40). Otherwise use the stated paired/record count.
    group_match = re.search(r"(\d[\d,]*)\s+of\s+\d[\d,]*\s+valid observations", text, flags=re.I)
    if group_match:
        return int(group_match.group(1).replace(",", ""))
    candidates = re.findall(r"(\d[\d,]*)\s+(?:paired observations|observations|records|rows|timestamps)", text, flags=re.I)
    values = []
    for value in candidates:
        try:
            values.append(int(value.replace(",", "")))
        except ValueError:
            continue
    return max(values) if values else None


def rank_findings(
    findings: Iterable[dict[str, Any]],
    row_count: int,
    limit: int = 12,
) -> list[dict[str, Any]]:
    """Rank deterministic findings by type, available sample support and denominator.

    The score is a prioritization heuristic, not a probability or statistical p-value.
    """
    if row_count < 0:
        raise ValueError("row_count cannot be negative.")
    if limit < 1:
        raise ValueError("limit must be positive.")

    ranked = []
    for original_index, source in enumerate(findings):
        item = dict(source)
        kind = str(item.get("kind", "")).lower()
        base = _KIND_WEIGHT.get(kind, 0.35)
        sample = _sample_size(item)
        if sample is None:
            support = 0.55
            sample_label = "Not stated"
        else:
            support = min(1.0, sample / 30.0)
            sample_label = f"{sample:,}"
        coverage = min(1.0, sample / max(1, row_count)) if sample is not None and row_count else 0.5
        score = round(100 * (0.55 * base + 0.35 * support + 0.10 * coverage))
        if score >= 78 and sample is not None and sample >= 20:
            evidence_level = "Stronger evidence"
        elif score >= 58 and (sample is None or sample >= 8):
            evidence_level = "Useful signal"
        else:
            evidence_level = "Exploratory"
        item["priority_score"] = score
        item["evidence_level"] = evidence_level
        item["sample_size"] = sample
        item["sample_label"] = sample_label
        item["priority_reason"] = (
            f"Prioritized using finding type ({kind or 'unspecified'}), "
            f"available sample support ({sample_label}) and current view size ({row_count:,} rows). "
            "This score is a review order, not a probability or significance test."
        )
        item["next_step"] = str(item.get("action") or "Inspect the supporting records and compare relevant fields.")
        ranked.append((score, original_index, item))

    ranked.sort(key=lambda entry: (-entry[0], entry[1]))
    return [item for _, _, item in ranked[:limit]]


def build_next_questions(
    domain: str,
    numeric_columns: Iterable[str],
    categorical_columns: Iterable[str],
    date_columns: Iterable[str],
    limit: int = 4,
) -> list[dict[str, str]]:
    """Suggest concrete questions only where their required field roles exist."""
    if limit < 1:
        raise ValueError("limit must be positive.")
    numeric = list(numeric_columns)
    categories = list(categorical_columns)
    dates = list(date_columns)
    questions: list[dict[str, str]] = []

    if numeric and categories:
        questions.append({
            "question": f"Which {categories[0]} groups have the highest and lowest median {numeric[0]}?",
            "why": "A numeric measure and categorical dimension are both available.",
            "fields": f"{numeric[0]}, {categories[0]}",
        })
    if dates and numeric:
        questions.append({
            "question": f"How does {numeric[0]} change across the available {dates[0]} periods?",
            "why": "A date field and numeric measure support a time comparison.",
            "fields": f"{dates[0]}, {numeric[0]}",
        })
    if len(numeric) >= 2:
        questions.append({
            "question": f"Do {numeric[0]} and {numeric[1]} move together, and are there visible outliers?",
            "why": "Two numeric measures support a descriptive relationship check.",
            "fields": f"{numeric[0]}, {numeric[1]}",
        })
    if categories:
        questions.append({
            "question": f"Is {categories[0]} dominated by a small number of categories or missing values?",
            "why": "Category counts and completeness can reveal concentration.",
            "fields": categories[0],
        })

    domain_prefix = {
        "Sales & commerce": "For commercial analysis,",
        "Customer & audience": "For audience analysis,",
        "People & workforce": "For workforce analysis,",
        "Finance & accounting": "For financial analysis,",
        "Marketing & acquisition": "For campaign analysis,",
        "Operations & service": "For operations analysis,",
    }.get(domain, "For this dataset,")
    return [
        {**item, "question": f"{domain_prefix} {item['question'][0].lower()}{item['question'][1:]}"}
        for item in questions[:limit]
    ]
