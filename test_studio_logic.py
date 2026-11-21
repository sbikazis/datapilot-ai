import pandas as pd
import pytest

from studio_logic import (
    category_summary,
    numeric_summary,
    recommend_visualization,
    safe_correlation,
)


def test_recommendation_adapts_to_detected_field_roles():
    assert recommend_visualization(["sales"], ["region"], ["date"])[0] == "Time trend"
    assert recommend_visualization(["sales"], ["region"], [])[0] == "Ranked comparison"
    assert recommend_visualization(["x", "y"], [], [])[0] == "Relationship scatter"
    assert recommend_visualization([], ["segment"], [])[0] == "Category frequency"


def test_numeric_summary_reports_distribution_and_iqr_outliers():
    result = numeric_summary(pd.Series([1, 2, 3, 4, 5, 100, None, float("inf")]))
    assert result["count"] == 6
    assert result["median"] == 3.5
    assert result["max"] == 100
    assert result["iqr_outliers"] == 1


def test_numeric_summary_handles_empty_values():
    result = numeric_summary(pd.Series([None, "bad", float("inf")]))
    assert result["count"] == 0
    assert result["mean"] is None


def test_safe_correlation_requires_sufficient_variation_and_pairs():
    frame = pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, 4, 6, 8]})
    corr, count = safe_correlation(frame, "x", "y")
    assert corr == pytest.approx(1.0)
    assert count == 4
    corr, count = safe_correlation(pd.DataFrame({"x": [1, 1, 1], "y": [2, 3, 4]}), "x", "y")
    assert corr is None
    assert count == 3


def test_category_summary_includes_denominator_and_missing_bucket():
    result = category_summary(pd.Series(["A", "A", "B", None]), top_n=5)
    assert result["records"].sum() == 4
    assert result.loc[result["category"] == "A", "share_pct"].iloc[0] == 50
    assert "(Missing)" in result["category"].tolist()


def test_category_summary_rejects_invalid_top_n():
    with pytest.raises(ValueError):
        category_summary(pd.Series(["A"]), top_n=0)



def test_evidence_findings_include_denominators_and_caveats():
    from studio_logic import build_evidence_findings

    frame = pd.DataFrame({
        "segment": ["A"] * 8 + ["B"] * 2,
        "revenue": [10, 11, 12, 13, 14, 15, 16, 100, 9, 8],
        "cost": [5, 5.5, 6, 6.5, 7, 7.5, 8, 50, 4.5, 4],
        "date": pd.date_range("2026-01-01", periods=10),
    })
    findings = build_evidence_findings(frame, ["revenue", "cost"], ["segment"], ["date"])
    assert findings
    assert any("observations" in item["detail"] for item in findings)
    assert any("causality" in item["detail"] for item in findings if item["kind"] == "relationship")


def test_evidence_findings_are_empty_for_empty_roles_and_validate_limit():
    from studio_logic import build_evidence_findings

    frame = pd.DataFrame({"label": ["a", "b"]})
    assert build_evidence_findings(frame, [], [], []) == []
    with pytest.raises(ValueError):
        build_evidence_findings(frame, [], [], [], limit=0)
