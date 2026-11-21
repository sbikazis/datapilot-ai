"""Integration coverage for the customer-facing first-run journey."""
from io import BytesIO

import pandas as pd

from domain_intelligence import assess_domain
from guided_analysis import available_guided_paths, build_guided_result
from insight_actions import action_plan_frame, build_action_plan
from recommendation_engine import build_next_questions, rank_findings
from report_intelligence import build_report_data, render_html_report, report_workbook_sheets
from sample_workspace import SAMPLE_DATASET_NOTICE, build_sample_dataset
from studio_logic import build_evidence_findings
from universal_engine import profile_dataset
from upload_intelligence import read_dataset_upload


def _sample_journey():
    source = build_sample_dataset()
    profile = profile_dataset(source)
    domain = assess_domain(
        profile.data,
        profile.columns,
        profile.numeric_columns,
        profile.categorical_columns,
        profile.date_columns,
    )
    findings = build_evidence_findings(
        profile.data,
        profile.numeric_columns,
        profile.categorical_columns,
        profile.date_columns,
    )
    ranked = rank_findings(findings, row_count=len(profile.data), limit=20)
    questions = build_next_questions(
        domain["domain"],
        profile.numeric_columns,
        profile.categorical_columns,
        profile.date_columns,
    )
    return source, profile, domain, ranked, questions


def test_sample_dataset_completes_first_run_analysis_and_decision_journey():
    source, profile, domain, ranked, questions = _sample_journey()

    assert len(source) == 120
    assert domain["domain"] == "Sales & commerce"
    assert "revenue" in profile.numeric_columns
    assert "order_date" in profile.date_columns
    assert {"region", "product_category"}.issubset(profile.categorical_columns)
    assert {path["id"] for path in available_guided_paths(
        profile.numeric_columns, profile.categorical_columns, profile.date_columns
    )} >= {"quality_review", "measure_profile", "compare_groups", "time_movement"}
    assert ranked
    assert questions
    assert all("not a probability" in item["priority_reason"] for item in ranked)

    comparison = build_guided_result(
        profile.data, "compare_groups", measure="revenue", dimension="region", min_group_size=3
    )
    movement = build_guided_result(
        profile.data, "time_movement", measure="revenue", date="order_date"
    )
    assert comparison["status"] == "ready"
    assert set(comparison["table"]["group"]) == set(profile.data["region"].unique())
    assert comparison["source_indices"]
    assert movement["status"] == "ready"
    assert movement["summary"]["periods"] >= 2
    assert "not forecast" in movement["message"]


def test_sample_journey_produces_traceable_decisions_and_customer_report():
    source, profile, domain, ranked, questions = _sample_journey()
    plan = build_action_plan(ranked, profile.data.columns.tolist(), len(profile.data))

    assert plan
    assert all(item["view_rows"] == len(source) for item in plan)
    assert all("not proof" in item["decision_guardrail"] for item in plan)
    action_export = action_plan_frame(plan)
    assert len(action_export) == len(plan)
    assert "decision_guardrail" in action_export.columns

    report = build_report_data(
        source,
        profile.data,
        profile.numeric_columns,
        profile.columns,
        profile.quality,
        ranked,
        questions,
        title="First-run sample report",
        dataset="DataPilot sample · synthetic orders",
        domain=domain["domain"],
        workspace="Demo workspace",
        generated_at="2026-11-21T12:00+00:00",
    )
    html = render_html_report(report)
    sheets = report_workbook_sheets(report)

    assert report["source_rows"] == 120
    assert report["filtered_rows"] == 120
    assert report["dataset"].startswith("DataPilot sample")
    assert "First-run sample report" in html
    assert "Method and limitations" in html
    assert "not a probability" in html
    assert set(sheets) == {
        "Executive summary", "Key measures", "Priority findings", "Data quality",
        "Field dictionary", "Next questions", "Applied filters",
    }
    assert "revenue" in set(sheets["Key measures"]["field"])


def test_sample_report_workbook_round_trips_with_all_expected_sheets():
    source, profile, domain, ranked, questions = _sample_journey()
    report = build_report_data(
        source, source, profile.numeric_columns, profile.columns, profile.quality,
        ranked, questions, dataset="DataPilot sample · synthetic orders",
        domain=domain["domain"], generated_at="2026-11-21T12:00+00:00",
    )
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        source.to_excel(writer, sheet_name="Analyzed data", index=False)
        source.to_excel(writer, sheet_name="Filtered data", index=False)
        for name, table in report_workbook_sheets(report).items():
            table.to_excel(writer, sheet_name=name[:31], index=False)

    workbook = pd.ExcelFile(BytesIO(output.getvalue()))
    assert len(workbook.sheet_names) == 9
    assert "Executive summary" in workbook.sheet_names
    assert "Priority findings" in workbook.sheet_names
    assert "Applied filters" in workbook.sheet_names


def test_small_sample_stays_safe_when_group_comparison_has_no_supported_groups():
    frame = build_sample_dataset(rows=1)
    profile = profile_dataset(frame)
    result = build_guided_result(
        profile.data, "compare_groups", measure="revenue", dimension="region", min_group_size=3
    )

    assert result["status"] == "limited"
    assert result["table"].empty
    assert result["source_indices"] == []
    assert "smaller than 3" in result["message"]


def test_synthetic_notice_is_explicit_and_sample_is_reproducible():
    assert "fictional" in SAMPLE_DATASET_NOTICE.lower()
    assert "not be treated as real" in SAMPLE_DATASET_NOTICE.lower()
    pd.testing.assert_frame_equal(build_sample_dataset(), build_sample_dataset())



def _serialize_customer_dataset(source: pd.DataFrame, file_format: str) -> bytes:
    if file_format == "csv":
        return source.to_csv(index=False).encode("utf-8")
    if file_format == "xlsx":
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            source.to_excel(writer, sheet_name="Orders", index=False)
        return output.getvalue()
    if file_format == "json":
        return source.to_json(orient="records", date_format="iso").encode("utf-8")
    raise AssertionError(f"Unsupported test format: {file_format}")


def _run_uploaded_customer_journey(file_format: str):
    original = build_sample_dataset()
    filename = f"customer-orders.{file_format}"
    uploaded, intake = read_dataset_upload(
        filename, _serialize_customer_dataset(original, file_format),
        sheet_name="Orders" if file_format == "xlsx" else None,
    )
    profile = profile_dataset(uploaded)
    domain = assess_domain(
        profile.data, profile.columns, profile.numeric_columns,
        profile.categorical_columns, profile.date_columns,
    )
    findings = build_evidence_findings(
        profile.data, profile.numeric_columns,
        profile.categorical_columns, profile.date_columns,
    )
    ranked = rank_findings(findings, row_count=len(profile.data), limit=20)
    questions = build_next_questions(
        domain["domain"], profile.numeric_columns,
        profile.categorical_columns, profile.date_columns,
    )
    plan = build_action_plan(ranked, profile.data.columns.tolist(), len(profile.data))
    report = build_report_data(
        uploaded, profile.data, profile.numeric_columns, profile.columns,
        profile.quality, ranked, questions,
        title="Uploaded customer orders review",
        dataset=filename, domain=domain["domain"],
        workspace="Customer demo", prepared_for="Demo client",
        prepared_by="DataPilot analyst",
        generated_at="2026-11-21T12:00+00:00",
    )
    html = render_html_report(report)
    sheets = report_workbook_sheets(report)
    return original, uploaded, intake, profile, domain, ranked, questions, plan, report, html, sheets


import pytest


@pytest.mark.parametrize("file_format", ["csv", "xlsx", "json"])
def test_uploaded_file_completes_customer_journey_to_client_report(file_format):
    (
        original, uploaded, intake, profile, domain, ranked, questions,
        plan, report, html, sheets,
    ) = _run_uploaded_customer_journey(file_format)

    # Intake: source file is read with its full record and field shape.
    assert intake["filename"] == f"customer-orders.{file_format}"
    assert intake["rows"] == len(original) == 120
    assert intake["columns"] == len(original.columns)
    assert uploaded.shape == original.shape
    assert intake["selected_sheet"] == ("Orders" if file_format == "xlsx" else None)

    # Understanding: date, numeric and categorical roles survive real serialization.
    assert domain["domain"] == "Sales & commerce"
    assert "revenue" in profile.numeric_columns
    assert "order_date" in profile.date_columns
    assert "product_category" in profile.categorical_columns
    assert len(profile.data) == 120

    # Investigation and decisions: evidence is ranked and the action register is traceable.
    assert ranked
    assert questions
    assert plan
    assert all(item["view_rows"] == 120 for item in plan)
    comparison = build_guided_result(
        profile.data, "compare_groups", measure="revenue",
        dimension="region", min_group_size=3,
    )
    assert comparison["status"] == "ready"
    assert comparison["source_indices"]

    # Delivery: the client report carries the same row scope and real measure totals.
    revenue = float(pd.to_numeric(uploaded["revenue"]).sum())
    assert report["source_rows"] == 120
    assert report["filtered_rows"] == 120
    assert report["metrics"]
    revenue_metric = next(item for item in report["metrics"] if item["field"] == "revenue")
    assert revenue_metric["valid_count"] == 120
    assert revenue_metric["total"] == pytest.approx(revenue)
    assert "Uploaded customer orders review" in html
    assert "Prepared for Demo client" in html
    assert "Method and limitations" in html
    assert "Key measures" in sheets
    assert "revenue" in set(sheets["Key measures"]["field"])


def test_uploaded_excel_workbook_requires_and_reports_the_selected_sheet():
    source = build_sample_dataset(rows=12)
    payload = _serialize_customer_dataset(source, "xlsx")
    frame, metadata = read_dataset_upload("orders.xlsx", payload, sheet_name="Orders")

    assert metadata["sheets"] == ["Orders"]
    assert metadata["selected_sheet"] == "Orders"
    assert len(frame) == 12
