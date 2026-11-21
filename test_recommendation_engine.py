import pytest

from recommendation_engine import build_next_questions, rank_findings


def test_ranks_supported_findings_ahead_of_weak_generic_findings():
    findings = [
        {"kind": "measure", "title": "Metric summary", "detail": "Mean is 12."},
        {"kind": "segment difference", "title": "Segment differs", "detail": "Group has 24 of 40 valid observations."},
        {"kind": "data quality", "title": "Missing values", "detail": "10 missing cells."},
    ]
    ranked = rank_findings(findings, row_count=40)
    assert ranked[0]["kind"] == "segment difference"
    assert ranked[0]["sample_size"] == 24
    assert ranked[0]["priority_score"] >= ranked[-1]["priority_score"]


def test_rank_output_explains_heuristic_and_is_not_probability():
    ranked = rank_findings([{"kind": "relationship", "detail": "Correlation across 12 paired observations."}], 20)
    assert ranked[0]["evidence_level"] in {"Stronger evidence", "Useful signal", "Exploratory"}
    assert "not a probability" in ranked[0]["priority_reason"]


def test_preserves_original_fields_and_limits_results():
    items = [{"kind": "measure", "title": str(i), "action": "Inspect"} for i in range(5)]
    ranked = rank_findings(items, 10, limit=2)
    assert len(ranked) == 2
    assert all(item["next_step"] == "Inspect" for item in ranked)


def test_ties_preserve_original_order():
    items = [{"kind": "measure", "title": "first"}, {"kind": "measure", "title": "second"}]
    ranked = rank_findings(items, 10)
    assert [item["title"] for item in ranked] == ["first", "second"]


def test_next_questions_require_actual_field_roles():
    questions = build_next_questions("Sales & commerce", ["revenue", "cost"], ["region"], ["order_date"])
    assert len(questions) == 4
    assert all(item["fields"] for item in questions)
    assert "Sales analysis" not in questions[0]["question"]


def test_next_questions_are_empty_without_usable_roles():
    assert build_next_questions("General / mixed data", [], [], []) == []


@pytest.mark.parametrize("kwargs", [{"row_count": -1}, {"row_count": 1, "limit": 0}])
def test_rank_rejects_invalid_arguments(kwargs):
    with pytest.raises(ValueError):
        rank_findings([], **kwargs)
