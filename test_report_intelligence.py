import pandas as pd
import pytest

from report_intelligence import build_report_data, render_html_report, report_workbook_sheets


@pytest.fixture
def report():
    source = pd.DataFrame({
        "revenue": [10.0, 20.0, None, 40.0],
        "region": ["N", "S", "N", "S"],
        "emptyish": ["x", None, None, "x"],
    })
    filtered = source.dropna(subset=["revenue"])
    quality = {"missing_cells": 3, "missing_pct": 25.0, "duplicate_rows": 0, "constant_columns": []}
    return build_report_data(
        source, filtered, ["revenue"], [{"column": "revenue", "role": "Numeric measure"}],
        quality, [{"kind": "segment difference", "title": "Region gap", "detail": "Observed difference",
                   "priority_score": 81, "evidence_level": "Stronger evidence",
                   "next_step": "Compare source records", "priority_reason": "Heuristic only"}],
        [{"question": "Compare regions?", "why": "Fields support it", "fields": "region, revenue"}],
        {"region": ["N"]}, title="Quarterly review", dataset="orders.csv",
        domain="Sales & commerce", workspace="Ops", generated_at="2026-11-21T12:00+00:00",
    )


def test_report_snapshot_contains_metrics_quality_and_provenance(report):
    assert report["source_rows"] == 4
    assert report["filtered_rows"] == 3
    assert report["metrics"][0]["total"] == 70
    assert report["metrics"][0]["valid_count"] == 3
    assert report["missing_by_field"][0]["field"] == "emptyish"
    assert report["filters"] == {"region": ["N"]}
    assert report["generated_at"].startswith("2026-11-21")


def test_html_report_escapes_untrusted_content_and_includes_sections(report):
    report["title"] = "<script>alert(1)</script>"
    html = render_html_report(report)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    for section in ("Executive summary", "Key measures", "Priority findings", "Data quality", "Recommended follow-up questions", "Applied filters"):
        assert section in html
    assert "Priority 81/100" in html


def test_html_report_handles_empty_findings_and_questions():
    data = pd.DataFrame({"label": ["a", "b"]})
    report = build_report_data(data, data, [], [], {}, [], [], generated_at="fixed")
    html = render_html_report(report)
    assert "No evidence-led findings" in html
    assert "No next questions" in html
    assert "No usable numeric measures" in html


def test_workbook_sheets_are_complete_and_named(report):
    sheets = report_workbook_sheets(report)
    assert "Executive summary" in sheets
    assert "Key measures" in sheets
    assert "Priority findings" in sheets
    assert "Data quality" in sheets
    assert "Field dictionary" in sheets
    assert "Next questions" in sheets
    assert "Applied filters" in sheets
    assert sheets["Key measures"].iloc[0]["total"] == 70


@pytest.mark.parametrize("precision", [-1, 9])
def test_invalid_precision_is_rejected(precision):
    frame = pd.DataFrame({"x": [1]})
    with pytest.raises(ValueError):
        build_report_data(frame, frame, ["x"], [], {}, [], [], precision=precision)
