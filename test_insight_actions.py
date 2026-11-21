import pandas as pd
import pytest

from insight_actions import action_plan_frame, action_plan_summary, build_action_plan


def findings():
    return [
        {"kind": "data quality", "title": "12 missing cells in email", "detail": "12 of 100 source cells are empty in email.", "priority_score": 92, "evidence_level": "Useful signal", "sample_size": 12},
        {"kind": "segment difference", "title": "revenue differs in region", "detail": "Median revenue for North is 20, compared with 10 overall. The group has 24 of 40 valid observations.", "priority_score": 81, "evidence_level": "Stronger evidence", "sample_size": 24},
        {"kind": "relationship", "title": "price and quantity association", "detail": "Correlation across 30 paired observations; no causal inference.", "priority_score": 70},
    ]


def test_action_plan_maps_findings_to_validation_not_unverified_outcomes():
    plan = build_action_plan(findings(), ["email", "revenue", "region", "price", "quantity"], row_count=100)
    assert plan[0]["action_type"] == "Risk to validate"
    assert plan[0]["fields"] == ["email"]
    assert "not proof" in plan[0]["decision_guardrail"]
    assert "financial impact" in plan[0]["decision_guardrail"]


def test_segment_recommendation_keeps_evidence_and_source_fields():
    plan = build_action_plan(findings(), ["revenue", "region"], 40)
    segment = plan[1]
    assert segment["action_type"] == "Opportunity to investigate"
    assert segment["fields"] == ["revenue", "region"]
    assert segment["sample"] == 24
    assert segment["priority_score"] == 81
    assert "overall baseline" in segment["recommended_check"]


def test_summary_and_export_are_stable_and_auditable():
    plan = build_action_plan(findings(), ["email", "revenue", "region", "price", "quantity"], 100)
    summary = action_plan_summary(plan)
    assert summary["actions"] == 3
    assert summary["Risk to validate"] == 1
    frame = action_plan_frame(plan)
    assert len(frame) == 3
    assert "decision_guardrail" in frame.columns
    assert frame.iloc[1]["fields"] == "revenue, region"


def test_unknown_finding_kind_gets_safe_generic_validation():
    plan = build_action_plan([{"kind": "unknown", "title": "Custom signal"}], [], 5)
    assert plan[0]["action_type"] == "Finding to validate"
    assert "confirm the observation" in plan[0]["recommended_check"]


@pytest.mark.parametrize("kwargs", [{"row_count": -1}, {"row_count": 1, "limit": 0}])
def test_invalid_arguments_are_rejected(kwargs):
    with pytest.raises(ValueError):
        build_action_plan([], [], **kwargs)


def test_empty_findings_produce_empty_export():
    assert build_action_plan([], ["x"], 0) == []
    assert action_plan_frame([]).empty
