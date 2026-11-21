from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any, Iterable

import math
import pandas as pd


def build_report_data(
    source: pd.DataFrame,
    filtered: pd.DataFrame,
    numeric_columns: Iterable[str],
    field_profile: Iterable[dict[str, Any]],
    quality: dict[str, Any],
    findings: Iterable[dict[str, Any]],
    next_questions: Iterable[dict[str, Any]],
    filters: dict[str, Any] | None = None,
    *,
    title: str = "DataPilot executive report",
    dataset: str = "Dataset",
    domain: str = "General / mixed data",
    workspace: str = "My workspace",
    prepared_for: str = "",
    prepared_by: str = "",
    analyst_note: str = "",
    generated_at: str | None = None,
    precision: int = 2,
) -> dict[str, Any]:
    """Create a reproducible, source-grounded report snapshot."""
    if precision < 0 or precision > 8:
        raise ValueError("precision must be between 0 and 8.")
    metrics = []
    for column in list(numeric_columns):
        if column not in filtered.columns:
            continue
        values = pd.to_numeric(filtered[column], errors="coerce")
        values = values[values.map(lambda value: math.isfinite(float(value)) if pd.notna(value) else False)]
        if values.empty:
            continue
        metrics.append({
            "field": str(column),
            "valid_count": int(values.count()),
            "total": float(values.sum()),
            "mean": float(values.mean()),
            "median": float(values.median()),
            "minimum": float(values.min()),
            "maximum": float(values.max()),
        })

    missing_by_field = []
    for column in source.columns:
        missing = int(source[column].isna().sum())
        if missing:
            missing_by_field.append({
                "field": str(column),
                "missing_count": missing,
                "missing_pct": round(missing / max(1, len(source)) * 100, 1),
            })
    missing_by_field.sort(key=lambda item: (-item["missing_count"], item["field"]))

    return {
        "title": str(title).strip() or "DataPilot executive report",
        "dataset": str(dataset),
        "domain": str(domain),
        "workspace": str(workspace),
        "prepared_for": str(prepared_for).strip()[:120],
        "prepared_by": str(prepared_by).strip()[:80],
        "analyst_note": str(analyst_note).strip()[:1200],
        "generated_at": generated_at or datetime.now().astimezone().isoformat(timespec="minutes"),
        "source_rows": int(len(source)),
        "filtered_rows": int(len(filtered)),
        "field_count": int(len(source.columns)),
        "quality": {
            "missing_cells": int(quality.get("missing_cells", source.isna().sum().sum())),
            "missing_pct": float(quality.get("missing_pct", source.isna().sum().sum() / max(1, source.size) * 100)),
            "duplicate_rows": int(quality.get("duplicate_rows", source.duplicated().sum())),
            "constant_columns": list(quality.get("constant_columns", [])),
        },
        "metrics": metrics,
        "missing_by_field": missing_by_field,
        "field_profile": [dict(item) for item in field_profile],
        "findings": [dict(item) for item in findings],
        "next_questions": [dict(item) for item in next_questions],
        "filters": {str(key): list(value) if isinstance(value, (list, tuple, set)) else value for key, value in (filters or {}).items()},
        "method": (
            "Descriptive statistics and deterministic rules computed from the uploaded dataset. "
            "Findings are observational and do not establish causality, forecasts or business context."
        ),
        "precision": precision,
    }


def render_html_report(report: dict[str, Any], include_method_notes: bool = True) -> str:
    """Render a self-contained HTML report with a print-friendly layout."""
    esc = lambda value: escape(str(value))
    precision = int(report.get("precision", 2))
    metric_rows = "".join(
        "<tr>" + "".join((
            f"<td>{esc(item['field'])}</td>",
            f"<td>{int(item['valid_count']):,}</td>",
            f"<td>{item['total']:,.{precision}f}</td>",
            f"<td>{item['mean']:,.{precision}f}</td>",
            f"<td>{item['median']:,.{precision}f}</td>",
            f"<td>{item['minimum']:,.{precision}f} – {item['maximum']:,.{precision}f}</td>",
        )) + "</tr>"
        for item in report["metrics"]
    ) or "<tr><td colspan='6'>No usable numeric measures were identified.</td></tr>"

    finding_cards = []
    for item in report["findings"]:
        label = item.get("evidence_level", item.get("kind", "Observation"))
        score = item.get("priority_score")
        score_text = f" · Priority {int(score)}/100" if isinstance(score, (int, float)) else ""
        finding_cards.append(
            f"<article><div class='eyebrow'>{esc(label)}{esc(score_text)}</div>"
            f"<h3>{esc(item.get('title', 'Observation'))}</h3>"
            f"<p>{esc(item.get('detail', ''))}</p>"
            f"<p class='action'><b>Next step:</b> {esc(item.get('next_step', item.get('action', 'Review supporting records.')))}</p>"
            f"<p class='muted'>{esc(item.get('priority_reason', ''))}</p></article>"
        )
    findings_html = "".join(finding_cards) or "<p>No evidence-led findings were produced for this view.</p>"

    missing_rows = "".join(
        f"<tr><td>{esc(item['field'])}</td><td>{int(item['missing_count']):,}</td><td>{float(item['missing_pct']):.1f}%</td></tr>"
        for item in report["missing_by_field"][:15]
    ) or "<tr><td colspan='3'>No missing values detected.</td></tr>"

    question_items = "".join(
        f"<li><b>{esc(item.get('question', ''))}</b><br><span class='muted'>{esc(item.get('why', ''))} Fields: {esc(item.get('fields', 'Not specified'))}</span></li>"
        for item in report["next_questions"]
    ) or "<li>No next questions could be generated from the detected field roles.</li>"

    filter_items = "".join(
        f"<li><b>{esc(key)}:</b> {esc(', '.join(map(str, value)) if isinstance(value, list) else value)}</li>"
        for key, value in report["filters"].items() if value not in (None, "", [], ())
    ) or "<li>No active global filters.</li>"

    method = f"<section><h2>Method and limitations</h2><p>{esc(report['method'])}</p><p>Priority scores are review-order heuristics, not probabilities or statistical significance tests. Validate data definitions and sample coverage before acting.</p></section>" if include_method_notes else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(report['title'])}</title>
<style>
:root{{--ink:#182239;--muted:#71809b;--line:#e5e9f1;--violet:#6955e8;--canvas:#f4f6fb}}
*{{box-sizing:border-box}}body{{margin:0;padding:30px;background:var(--canvas);color:var(--ink);font:15px/1.6 Inter,Arial,sans-serif}}
main{{max-width:1120px;margin:auto;background:#fff;border:1px solid var(--line);border-radius:22px;padding:34px;box-shadow:0 14px 40px #1723420d}}
header{{background:linear-gradient(115deg,#111a30,#514995);color:#fff;padding:30px;border-radius:17px}}
header .eyebrow{{color:#9ce7e0;letter-spacing:.16em;font-size:11px;font-weight:800}}h1{{font-size:30px;line-height:1.2;margin:8px 0}}header p{{color:#dce2f7;margin:5px 0}}
.kpis{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:20px 0}}
.kpi{{border:1px solid var(--line);border-radius:13px;padding:15px;background:#fbfcff}}.kpi small{{display:block;color:var(--muted);font-weight:700}}.kpi strong{{font-size:23px}}
h2{{font-size:20px;margin:30px 0 10px}}h3{{font-size:17px;margin:5px 0}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border-bottom:1px solid var(--line);padding:10px;text-align:left}}th{{background:#f6f7fb}}
article{{border:1px solid var(--line);border-left:4px solid var(--violet);border-radius:12px;padding:15px 18px;margin:11px 0;background:#fcfbff}}
.eyebrow{{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--violet);font-weight:800}}.action{{margin-bottom:4px}}.muted{{font-size:12px;color:var(--muted)}}li{{margin:9px 0}}.foot{{border-top:1px solid var(--line);margin-top:30px;padding-top:15px;color:var(--muted);font-size:12px}}
@media(max-width:700px){{body{{padding:8px}}main{{padding:16px}}.kpis{{grid-template-columns:repeat(2,minmax(0,1fr))}}header{{padding:20px}}h1{{font-size:24px}}}}
@media print{{body{{background:#fff;padding:0}}main{{border:0;box-shadow:none;padding:0;max-width:none}}header{{print-color-adjust:exact;-webkit-print-color-adjust:exact}}article,.kpi{{break-inside:avoid}}}}
</style></head><body><main>
<header><div class="eyebrow">DATAPILOT AI · EXECUTIVE INTELLIGENCE</div><h1>{esc(report['title'])}</h1>
<p>{esc(report['workspace'])} · {esc(report['dataset'])} · {esc(report['domain'])}</p>
<p>{'Prepared for ' + esc(report.get('prepared_for')) + ' · ' if report.get('prepared_for') else ''}{'Prepared by ' + esc(report.get('prepared_by')) + ' · ' if report.get('prepared_by') else ''}Generated {esc(report['generated_at'])} · {report['filtered_rows']:,} of {report['source_rows']:,} source rows in view</p></header>
<div class="kpis">
<div class="kpi"><small>Rows in view</small><strong>{report['filtered_rows']:,}</strong></div>
<div class="kpi"><small>Fields</small><strong>{report['field_count']:,}</strong></div>
<div class="kpi"><small>Missing cells</small><strong>{report['quality']['missing_cells']:,}</strong></div>
<div class="kpi"><small>Duplicate rows</small><strong>{report['quality']['duplicate_rows']:,}</strong></div>
</div>
<section><h2>Executive summary</h2><p>The current view contains <b>{report['filtered_rows']:,}</b> rows across <b>{report['field_count']:,}</b> fields. The dataset is classified under <b>{esc(report['domain'])}</b>. {len(report['findings'])} evidence-led findings and {len(report['next_questions'])} follow-up questions are included below.</p></section>
{'<section><h2>Analyst note</h2><p>' + esc(report.get('analyst_note')) + '</p><p class="muted">Provided by the report author; not inferred from the dataset.</p></section>' if report.get('analyst_note') else ''}
<section><h2>Key measures</h2><table><thead><tr><th>Measure</th><th>Valid</th><th>Total</th><th>Average</th><th>Median</th><th>Range</th></tr></thead><tbody>{metric_rows}</tbody></table></section>
<section><h2>Priority findings</h2>{findings_html}</section>
<section><h2>Data quality</h2><p>{report['quality']['missing_pct']:.1f}% of source cells are missing. Constant fields: {esc(', '.join(report['quality']['constant_columns']) or 'None detected')}.</p><table><thead><tr><th>Field</th><th>Missing</th><th>Missing %</th></tr></thead><tbody>{missing_rows}</tbody></table></section>
<section><h2>Recommended follow-up questions</h2><ol>{question_items}</ol></section>
<section><h2>Applied filters</h2><ul>{filter_items}</ul></section>
{method}<div class="foot">DataPilot AI · Adaptive Data Intelligence · Report snapshot generated from the current app session.</div>
</main></body></html>"""


def report_workbook_sheets(report: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Return normalized tables for a multi-sheet XLSX report."""
    return {
        "Executive summary": pd.DataFrame([{
            "title": report["title"], "dataset": report["dataset"], "domain": report["domain"],
            "generated_at": report["generated_at"], "prepared_for": report.get("prepared_for", ""),
            "prepared_by": report.get("prepared_by", ""), "analyst_note": report.get("analyst_note", ""), "source_rows": report["source_rows"],
            "filtered_rows": report["filtered_rows"], "field_count": report["field_count"],
            **{**report["quality"], "constant_columns": ", ".join(report["quality"]["constant_columns"])},
        }]),
        "Key measures": pd.DataFrame(report["metrics"]),
        "Priority findings": pd.DataFrame(report["findings"]),
        "Data quality": pd.DataFrame(report["missing_by_field"]),
        "Field dictionary": pd.DataFrame(report["field_profile"]),
        "Next questions": pd.DataFrame(report["next_questions"]),
        "Applied filters": pd.DataFrame([{"field": key, "selected_values": ", ".join(map(str, value)) if isinstance(value, list) else str(value)} for key, value in report["filters"].items()]),
    }
