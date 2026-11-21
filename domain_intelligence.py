from __future__ import annotations

import re
from typing import Any

import pandas as pd


DOMAIN_SIGNALS: dict[str, dict[str, tuple[str, ...]]] = {
    "Sales & commerce": {
        "transaction": ("order", "invoice", "sales", "revenue", "transaction", "cart", "checkout"),
        "product": ("product", "sku", "item", "quantity", "qty", "unit_price", "discount"),
        "fulfilment": ("shipping", "shipment", "delivery", "return"),
    },
    "Customer & audience": {
        "identity": ("customer", "client", "subscriber", "user", "member", "audience"),
        "segmentation": ("segment", "cohort", "lifetime_value", "churn", "retention", "loyalty"),
        "engagement": ("session", "visit", "engagement", "signup", "sign_up"),
    },
    "People & workforce": {
        "people": ("employee", "staff", "worker", "personnel", "headcount"),
        "organization": ("department", "job_title", "position", "manager", "team"),
        "employment": ("salary", "wage", "hire_date", "tenure", "performance_review"),
    },
    "Finance & accounting": {
        "accounting": ("ledger", "debit", "credit", "balance", "accounting", "journal"),
        "financial_metric": ("expense", "cost", "profit", "budget", "cashflow", "cash_flow", "margin"),
        "payment": ("payment", "invoice_amount", "tax", "reimbursement", "payout"),
    },
    "Marketing & acquisition": {
        "campaign": ("campaign", "ad_group", "creative", "advert"),
        "traffic": ("impression", "click", "ctr", "cpc", "cpm", "source", "medium", "channel"),
        "conversion": ("conversion", "lead", "signup", "acquisition", "roas", "cpa"),
    },
    "Operations & service": {
        "workflow": ("ticket", "task", "case", "request", "incident", "work_order"),
        "process": ("duration", "latency", "response_time", "resolution_time", "cycle_time", "downtime"),
        "supply": ("inventory", "stock", "warehouse", "production", "machine", "defect", "quality"),
    },
}


DOMAIN_DESCRIPTIONS = {
    "Sales & commerce": "Commercial activity, orders, products and fulfilment.",
    "Customer & audience": "People, customer segments, audience behaviour and retention.",
    "People & workforce": "Employees, roles, departments and workforce measures.",
    "Finance & accounting": "Balances, expenses, budgets, payments and financial measures.",
    "Marketing & acquisition": "Campaigns, channels, traffic and conversion performance.",
    "Operations & service": "Workflows, service delivery, process time and operational quality.",
    "General / mixed data": "A flexible analysis lens because no specialist domain has enough evidence.",
}


def _tokens(column: Any) -> set[str]:
    return set(re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_").split("_"))


def assess_domain(
    frame: pd.DataFrame,
    field_metadata: list[dict[str, Any]] | None = None,
    numeric_columns: list[str] | None = None,
    categorical_columns: list[str] | None = None,
    date_columns: list[str] | None = None,
    override: str = "Automatic",
) -> dict[str, Any]:
    """Classify a dataset from explicit column-name evidence and expose the evidence."""
    numeric = list(numeric_columns or [])
    categorical = list(categorical_columns or [])
    dates = list(date_columns or [])
    columns = list(frame.columns)
    tokens_by_column = {str(col): _tokens(col) for col in columns}
    scores: dict[str, int] = {}
    evidence: dict[str, list[str]] = {}

    for domain, groups in DOMAIN_SIGNALS.items():
        matched: list[str] = []
        score = 0
        for group, hints in groups.items():
            group_match = []
            for column, tokens in tokens_by_column.items():
                normalized = re.sub(r"[^a-z0-9]+", "_", column.strip().lower()).strip("_")
                if any(hint in tokens or hint == normalized for hint in hints):
                    group_match.append(column)
            if group_match:
                score += min(3, len(group_match)) * (2 if group in {"transaction", "identity", "people", "accounting", "campaign", "workflow"} else 1)
                matched.extend(group_match)
        scores[domain] = score
        evidence[domain] = list(dict.fromkeys(matched))

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_domain, best_score = ordered[0]
    second_score = ordered[1][1] if len(ordered) > 1 else 0
    # Require at least two independent signal points and a meaningful lead over alternatives.
    confident = best_score >= 2 and best_score >= second_score + 1
    automatic = best_domain if confident else "General / mixed data"
    if override != "Automatic" and override not in (*DOMAIN_SIGNALS.keys(), "General / mixed data"):
        raise ValueError("Unsupported domain override.")
    selected = automatic if override == "Automatic" else override

    denominator = max(1, sum(scores.values()))
    confidence = round(best_score / denominator * 100) if confident else 0
    selected_evidence = evidence.get(selected, [])
    if override != "Automatic" and selected == "General / mixed data":
        selected_evidence = []
    templates = _build_templates(selected, numeric, categorical, dates, field_metadata or [])
    if not templates:
        templates = [{
            "title": "Review the data structure",
            "question": "Which fields are reliable measures, dimensions or time fields?",
            "why": "The current schema does not yet support a specialist analysis template.",
            "required_fields": [],
            "available": True,
        }]

    return {
        "domain": selected,
        "automatic_domain": automatic,
        "confidence": confidence if override == "Automatic" else None,
        "is_overridden": override != "Automatic",
        "scores": scores,
        "evidence_columns": selected_evidence,
        "description": DOMAIN_DESCRIPTIONS[selected],
        "templates": templates,
    }


def _build_templates(
    domain: str,
    numeric: list[str],
    categorical: list[str],
    dates: list[str],
    metadata: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    semantic = {item.get("column"): item.get("semantic_type", "") for item in metadata}
    templates: list[dict[str, Any]] = []

    def add(title: str, question: str, why: str, required: list[str], condition: bool) -> None:
        templates.append({
            "title": title,
            "question": question,
            "why": why,
            "required_fields": required,
            "available": bool(condition),
        })

    if domain == "Sales & commerce":
        add("Revenue by product or segment", "Which product or category contributes most to the selected measure?", "A commercial measure and a grouping field support a ranked comparison.", [numeric[0] if numeric else "numeric measure", categorical[0] if categorical else "category"], bool(numeric and categorical))
        add("Sales movement over time", "How does the selected commercial measure change across periods?", "A date field and numeric measure support period aggregation.", [dates[0] if dates else "date", numeric[0] if numeric else "measure"], bool(dates and numeric))
        add("Quantity and value relationship", "Do quantity and amount move together in this dataset?", "This checks association between two numeric fields; it does not imply causation.", numeric[:2], len(numeric) >= 2)
    elif domain == "Customer & audience":
        add("Audience segments", "How do selected measures differ across customer or audience groups?", "A segment and numeric measure enable a sample-aware group comparison.", [categorical[0] if categorical else "segment", numeric[0] if numeric else "measure"], bool(categorical and numeric))
        add("Customer activity over time", "How does the selected activity measure vary over time?", "Date and numeric fields support an activity trend; cohort or retention meaning is not assumed.", [dates[0] if dates else "date", numeric[0] if numeric else "measure"], bool(dates and numeric))
        add("Audience field quality", "Are customer categories complete and sufficiently varied?", "Category completeness and distinct counts help assess whether segmentation is useful.", categorical[:1], bool(categorical))
    elif domain == "People & workforce":
        salary_fields = [c for c in numeric if semantic.get(c) == "Currency-like amount" or "salary" in _tokens(c) or "wage" in _tokens(c)]
        add("Workforce measure by department", "How does a workforce measure vary across departments or roles?", "A numeric measure and category support group comparison.", [numeric[0] if numeric else "measure", categorical[0] if categorical else "department"], bool(numeric and categorical))
        add("Compensation distribution", "What is the spread of the detected salary or wage field?", "Only fields explicitly named or semantically labelled as currency-like compensation are included.", salary_fields[:1], bool(salary_fields))
        add("Workforce timeline", "How does a workforce measure vary across dates?", "Date and numeric fields support descriptive time analysis.", [dates[0] if dates else "date", numeric[0] if numeric else "measure"], bool(dates and numeric))
    elif domain == "Finance & accounting":
        finance_fields = [c for c in numeric if semantic.get(c) == "Currency-like amount" or _tokens(c) & {"amount", "balance", "debit", "credit", "expense", "cost", "profit", "budget"}]
        add("Financial measure distribution", "How are the available financial values distributed?", "The field name or semantic label suggests a financial amount; currency is not inferred.", finance_fields[:1], bool(finance_fields))
        add("Financial movement over time", "How does the selected financial measure change across periods?", "Date and amount fields support descriptive period comparisons.", [dates[0] if dates else "date", finance_fields[0] if finance_fields else "financial measure"], bool(dates and finance_fields))
        add("Financial categories", "How are financial measures distributed across available categories?", "A financial measure and category enable transparent group summaries.", [finance_fields[0] if finance_fields else "financial measure", categorical[0] if categorical else "category"], bool(finance_fields and categorical))
    elif domain == "Marketing & acquisition":
        marketing_metrics = [c for c in numeric if semantic.get(c) in {"Percentage / rate", "Currency-like amount"} or _tokens(c) & {"click", "impression", "conversion", "spend", "cost", "lead", "revenue"}]
        add("Channel or campaign comparison", "Which channel or campaign differs on the selected metric?", "A channel/campaign dimension and metric support evidence-based comparison.", [categorical[0] if categorical else "channel", marketing_metrics[0] if marketing_metrics else "metric"], bool(categorical and marketing_metrics))
        add("Campaign performance over time", "How does a selected campaign metric move over time?", "A date and marketing metric support trend analysis.", [dates[0] if dates else "date", marketing_metrics[0] if marketing_metrics else "metric"], bool(dates and marketing_metrics))
        add("Rate and volume relationship", "How do available rate and volume metrics relate?", "Numeric association can reveal co-movement but cannot establish cause.", marketing_metrics[:2], len(marketing_metrics) >= 2)
    elif domain == "Operations & service":
        duration_fields = [c for c in numeric if semantic.get(c) == "Duration" or _tokens(c) & {"duration", "latency", "downtime", "response_time", "resolution_time"}]
        add("Operational measure by status", "How does an operational measure differ across statuses or process groups?", "A measure and category support a comparison of process outcomes.", [numeric[0] if numeric else "measure", categorical[0] if categorical else "status"], bool(numeric and categorical))
        add("Process-time distribution", "What is the spread of the detected process-duration field?", "Only fields identified as durations by name or semantic inference are included.", duration_fields[:1], bool(duration_fields))
        add("Operational throughput over time", "How does a selected operational measure move across periods?", "Date and numeric fields support descriptive time analysis.", [dates[0] if dates else "date", numeric[0] if numeric else "measure"], bool(dates and numeric))
    else:
        add("Compare categories", "Which groups differ on a selected measure?", "A numeric measure and category support a general group comparison.", [numeric[0] if numeric else "measure", categorical[0] if categorical else "category"], bool(numeric and categorical))
        add("Explore time movement", "How does a numeric measure change over time?", "A date field and numeric measure support a time trend.", [dates[0] if dates else "date", numeric[0] if numeric else "measure"], bool(dates and numeric))
        add("Understand distributions", "What are the spread and unusual values of a numeric field?", "Numeric fields support distribution and robust outlier review.", numeric[:1], bool(numeric))

    return templates
