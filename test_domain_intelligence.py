import pandas as pd
import pytest

from domain_intelligence import assess_domain


def _assess(columns, numeric=None, categorical=None, dates=None, override="Automatic"):
    frame = pd.DataFrame({column: [1, 2, 3] for column in columns})
    metadata = [{"column": column, "semantic_type": "Currency-like amount" if "amount" in column else "Numeric measure"} for column in columns]
    return assess_domain(frame, metadata, numeric or [], categorical or [], dates or [], override)


@pytest.mark.parametrize(
    "columns,expected",
    [
        (["order_id", "product_name", "revenue", "order_date"], "Sales & commerce"),
        (["customer_id", "customer_segment", "lifetime_value"], "Customer & audience"),
        (["employee_id", "department", "salary"], "People & workforce"),
        (["ledger_account", "debit", "credit", "balance"], "Finance & accounting"),
        (["campaign_id", "channel", "impressions", "clicks"], "Marketing & acquisition"),
        (["ticket_id", "resolution_time", "status"], "Operations & service"),
    ],
)
def test_classifies_common_domains_from_column_evidence(columns, expected):
    result = _assess(columns)
    assert result["domain"] == expected
    assert result["confidence"] > 0
    assert result["evidence_columns"]


def test_ambiguous_schema_falls_back_to_general_without_guessing():
    result = _assess(["name", "value", "group"])
    assert result["domain"] == "General / mixed data"
    assert result["confidence"] == 0


def test_manual_override_is_respected_and_marked():
    result = _assess(["order_id", "revenue"], override="Finance & accounting")
    assert result["domain"] == "Finance & accounting"
    assert result["is_overridden"]
    assert result["confidence"] is None


def test_templates_only_mark_available_when_required_fields_exist():
    result = _assess(["customer_id", "customer_segment", "lifetime_value"], numeric=["lifetime_value"], categorical=["customer_segment"])
    audience = next(item for item in result["templates"] if item["title"] == "Audience segments")
    assert audience["available"]
    assert audience["required_fields"] == ["customer_segment", "lifetime_value"]
    time_template = next(item for item in result["templates"] if item["title"] == "Customer activity over time")
    assert not time_template["available"]


def test_unsupported_override_is_rejected():
    with pytest.raises(ValueError, match="Unsupported domain"):
        _assess(["revenue"], override="Healthcare")
