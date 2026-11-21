from __future__ import annotations

import re
from typing import Any, Iterable

import pandas as pd


_ACTIONS = {
    "data quality": ("Risk to validate", "Review the affected records and confirm whether the gaps or repeats are expected before using this field in a decision."),
    "change anomaly": ("Change to investigate", "Compare the affected period with adjacent periods and inspect the underlying records before treating the movement as operationally meaningful."),
    "trend shift": ("Change to investigate", "Validate the time window, sample coverage and contributing records; compare against an appropriate earlier baseline."),
    "segment difference": ("Opportunity to investigate", "Compare the segment with the overall baseline, inspect its distribution and verify whether the difference persists across a suitable time window."),
    "relationship": ("Relationship to investigate", "Inspect the scatter plot, outliers and possible subgroup effects. Association alone does not establish a cause or intervention."),
    "distribution": ("Data risk to validate", "Inspect the flagged values in context and confirm whether they are valid extremes, data-entry issues or a different population."),
    "concentration": ("Concentration to review", "Check whether the dominant category is expected and whether the smaller categories have enough records for a fair comparison."),
    "time coverage": ("Coverage limitation", "Check missing periods, timestamp quality and the observation window before interpreting a trend."),
    "measure": ("Baseline to understand", "Review the distribution and compare the measure across relevant groups or time periods before setting a target."),
    "coverage": ("Coverage to review", "Check which records or fields are included and whether the available sample represents the question being asked."),
}


def _matched_fields(finding: dict[str, Any], columns: list[str]) -> list[str]:
    text = " ".join(str(finding.get(key, "")) for key in ("title", "detail", "action")).casefold()
    matches = []
    for column in columns:
        name = str(column)
        if name and re.search(r"(?<![\w])" + re.escape(name.casefold()) + r"(?![\w])", text):
            matches.append(name)
    return matches


def build_action_plan(
    findings: Iterable[dict[str, Any]],
    columns: Iterable[str],
    row_count: int,
    limit: int = 12,
) -> list[dict[str, Any]]:
    """Turn ranked observations into traceable validation steps, not business claims."""
    if row_count < 0:
        raise ValueError("row_count cannot be negative.")
    if limit < 1:
        raise ValueError("limit must be positive.")
    available = [str(column) for column in columns]
    plan = []
    for index, source in enumerate(findings):
        finding = dict(source)
        kind = str(finding.get("kind", "observation")).casefold()
        label, recommendation = _ACTIONS.get(
            kind, ("Finding to validate", "Inspect the supporting records and confirm the observation before acting.")
        )
        fields = _matched_fields(finding, available)
        sample = finding.get("sample_size")
        if sample is None:
            sample = finding.get("sample_label")
        plan.append({
            "action_id": f"A{index + 1:02d}",
            "action_type": label,
            "priority_score": finding.get("priority_score"),
            "evidence_level": finding.get("evidence_level", "Exploratory"),
            "finding_kind": finding.get("kind", "observation"),
            "finding_title": finding.get("title", "Untitled finding"),
            "evidence": finding.get("detail", ""),
            "recommended_check": recommendation,
            "next_step": finding.get("next_step", finding.get("action", "Inspect supporting records.")),
            "fields": fields,
            "sample": sample if sample is not None else "Not stated",
            "view_rows": row_count,
            "source_index": index,
            "decision_guardrail": "Validate this observation in context. It is not proof of causality, financial impact or a guaranteed outcome.",
        })
    return plan[:limit]


def action_plan_summary(plan: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in plan:
        label = str(item.get("action_type", "Other"))
        counts[label] = counts.get(label, 0) + 1
    return {"actions": len(plan), **counts}


def action_plan_frame(plan: list[dict[str, Any]]) -> pd.DataFrame:
    """Flatten the action plan into a portable, auditable export."""
    columns = [
        "action_id", "action_type", "priority_score", "evidence_level",
        "finding_kind", "finding_title", "evidence", "recommended_check",
        "next_step", "fields", "sample", "view_rows", "decision_guardrail",
    ]
    rows = []
    for item in plan:
        row = {key: item.get(key) for key in columns}
        row["fields"] = ", ".join(item.get("fields", []))
        rows.append(row)
    return pd.DataFrame(rows, columns=columns)
