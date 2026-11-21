import pandas as pd

from semantic_engine import infer_semantic_fields


def test_semantic_inference_identifies_percentages_currency_and_duration_without_inventing_units():
    frame = pd.DataFrame({
        "conversion_rate": [0.1, 0.2, 0.3],
        "unit_price": [10.5, 12.0, 9.5],
        "response_time_seconds": [1.2, 2.3, 1.8],
        "country": ["MA", "FR", "ES"],
    })
    result = {item["column"]: item for item in infer_semantic_fields(frame)}
    assert result["conversion_rate"]["semantic_type"] == "Percentage / rate"
    assert "0–1" in result["conversion_rate"]["unit_hint"]
    assert result["unit_price"]["semantic_type"] == "Currency-like amount"
    assert result["unit_price"]["unit_hint"] == "Currency not identified"
    assert result["response_time_seconds"]["semantic_type"] == "Duration"
    assert result["country"]["semantic_type"] == "Text / category"


def test_semantic_inference_identifies_sensitive_identifiers_and_coordinates():
    frame = pd.DataFrame({
        "email_address": ["a@example.com", "b@example.com"],
        "phone_number": ["+212600000001", "+212600000002"],
        "latitude": [31.6, 34.0],
        "longitude": [-7.9, -6.8],
        "is_active": [True, False],
    })
    result = {item["column"]: item for item in infer_semantic_fields(frame)}
    assert result["email_address"]["semantic_type"] == "Email identifier"
    assert result["phone_number"]["semantic_type"] == "Phone identifier"
    assert result["latitude"]["semantic_type"] == "Latitude"
    assert result["longitude"]["semantic_type"] == "Longitude"
    assert result["is_active"]["semantic_type"] == "Boolean / flag"
    assert "personal data" in result["email_address"]["semantic_reason"]


def test_semantic_inference_does_not_guess_currency_or_coordinate_system_from_values():
    frame = pd.DataFrame({
        "misc_value": [10, 20, 30],
        "score": [0.2, 0.5, 0.9],
        "created_at": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
    })
    result = {item["column"]: item for item in infer_semantic_fields(frame)}
    assert result["misc_value"]["semantic_type"] == "Numeric measure"
    assert result["score"]["semantic_type"] == "Numeric measure"
    assert result["created_at"]["semantic_type"] == "Date / time"



def test_semantic_inference_avoids_partial_word_coordinate_false_positives():
    frame = pd.DataFrame({"platform": ["web", "mobile"], "latitude": [30.0, 31.0]})
    result = {item["column"]: item for item in infer_semantic_fields(frame)}
    assert result["platform"]["semantic_type"] == "Text / category"
    assert result["latitude"]["semantic_type"] == "Latitude"
