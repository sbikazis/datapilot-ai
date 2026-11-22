import json
from io import BytesIO
from urllib.error import HTTPError

import pandas as pd
import pytest

from ai_copilot import (
    XAIError,
    ask_grok,
    build_ai_context,
    get_api_key,
    test_connection as check_xai_connection,
)


class FakeResponse:
    status = 200

    def __init__(self, payload=None):
        self.payload = payload or {"output": [{"type": "message", "content": [{"type": "output_text", "text": "Evidence summary."}]}]}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_api_key_prefers_streamlit_secret_without_exposing_it():
    assert get_api_key({"XAI_API_KEY": " secret "}, {"XAI_API_KEY": "env"}) == "secret"


def test_api_key_falls_back_to_environment():
    assert get_api_key({}, {"XAI_API_KEY": " env-key "}) == "env-key"


def test_api_key_missing_returns_none():
    assert get_api_key({}, {}) is None


def test_context_contains_aggregates_but_not_source_rows_or_sensitive_columns():
    frame = pd.DataFrame({
        "revenue": [10, 20, 30],
        "region": ["North", "South", "North"],
        "customer_email": ["a@example.com", "b@example.com", "c@example.com"],
        "name": ["Alice", "Bob", "Cara"],
    })
    context = build_ai_context(
        frame, frame, ["revenue"], ["region", "customer_email", "name"], [],
        "Sales & commerce", [{"kind": "trend", "evidence_level": "exploratory", "title": "North"}], [],
    )
    serialized = json.dumps(context)
    assert context["numeric_measures"][0]["mean"] == 20
    assert "North" not in serialized
    assert "example.com" not in serialized
    assert "a@example.com" not in serialized
    assert "Alice" not in serialized
    assert "source_row_count" in context


def test_ask_grok_posts_to_responses_api_and_extracts_text():
    seen = {}

    def opener(request, timeout):
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        seen["headers"] = dict(request.header_items())
        seen["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    answer = ask_grok("Explain revenue", {"numeric_measures": [{"field": "revenue", "mean": 20}]}, "test-key", opener=opener)
    assert answer == "Evidence summary."
    assert seen["url"].endswith("/responses")
    assert seen["timeout"] == 120
    assert seen["headers"]["Authorization"] == "Bearer test-key"
    assert seen["body"]["store"] is False
    assert seen["body"]["model"] == "grok-4.7"


def test_ask_grok_rejects_empty_or_oversized_question_without_network():
    with pytest.raises(XAIError, match="Enter a question"):
        ask_grok(" ", {}, "test-key")
    with pytest.raises(XAIError, match="under 1000"):
        ask_grok("x" * 1001, {}, "test-key")


def test_ask_grok_requires_key():
    with pytest.raises(XAIError, match="not configured"):
        ask_grok("Question", {}, api_key="")


def test_test_connection_uses_models_endpoint_without_generation():
    seen = {}

    def opener(request, timeout):
        seen["url"] = request.full_url
        return FakeResponse({"data": []})

    check_xai_connection("test-key", opener=opener)
    assert seen["url"].endswith("/models")


def test_unauthorized_key_error_is_actionable():
    def opener(request, timeout):
        raise HTTPError(request.full_url, 401, "Unauthorized", {}, BytesIO(b""))
    with pytest.raises(XAIError, match="rejected the API key"):
        check_xai_connection("bad-key", opener=opener)
