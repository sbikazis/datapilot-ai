import pandas as pd
import pytest

from guided_analysis import available_guided_paths, build_guided_result


def sample():
    return pd.DataFrame({
        "team": ["A"] * 4 + ["B"] * 4 + ["tiny"],
        "amount": [10, 12, 11, 13, 20, 22, 21, 23, 999],
        "other": [1, 2, 3, 4, 2, 4, 6, 8, 9],
        "date": pd.date_range("2026-01-01", periods=9, freq="D"),
    })


def test_available_paths_are_gated_by_roles():
    ids = [p["id"] for p in available_guided_paths(["amount"], ["team"], ["date"])]
    assert ids == ["quality_review", "measure_profile", "compare_groups", "time_movement"]
    assert "relationship" in [p["id"] for p in available_guided_paths(["a", "b"], [], [])]


def test_measure_profile_ignores_invalid_and_infinite_values():
    frame = pd.DataFrame({"m": [1, 2, float("inf"), None, 5]})
    result = build_guided_result(frame, "measure_profile", measure="m")
    assert result["summary"]["valid_values"] == 3
    assert result["summary"]["median"] == 2


def test_compare_groups_suppresses_tiny_groups_and_is_traceable():
    frame = sample()
    result = build_guided_result(frame, "compare_groups", measure="amount", dimension="team", min_group_size=3)
    assert result["table"]["group"].tolist() == ["B", "A"]
    assert 8 == len(result["source_indices"])
    assert "not causes" in result["message"]


def test_time_movement_does_not_fill_missing_periods():
    frame = pd.DataFrame({"d": ["2026-01-01", "2026-03-01"], "m": [2, 4]})
    result = build_guided_result(frame, "time_movement", measure="m", date="d")
    assert result["table"]["period"].dt.month.tolist() == [1, 3]
    assert result["summary"]["periods"] == 2


def test_relationship_requires_distinct_fields_and_reports_sample_size():
    frame = sample()
    result = build_guided_result(frame, "relationship", x_measure="amount", y_measure="other")
    assert result["summary"]["paired_records"] == 9
    with pytest.raises(ValueError, match="different"):
        build_guided_result(frame, "relationship", x_measure="amount", y_measure="amount")


def test_quality_review_includes_missingness_and_duplicates():
    frame = pd.DataFrame({"a": [1, None, 1], "b": ["x", "x", "x"]})
    result = build_guided_result(frame, "quality_review")
    assert result["summary"]["duplicate_rows"] == 1
    assert result["table"].set_index("field").loc["a", "missing"] == 1


def test_empty_frame_and_invalid_inputs_are_safe():
    empty = build_guided_result(pd.DataFrame(columns=["a"]), "measure_profile", measure="a")
    assert empty["status"] == "empty"
    with pytest.raises(ValueError):
        build_guided_result(sample(), "unsupported")
    with pytest.raises(ValueError):
        build_guided_result(sample(), "compare_groups", measure="missing", dimension="team")
