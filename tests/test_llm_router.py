"""
Unit Tests for src/core/llm_router.py.
Verifies programmatic version sorting and dynamic model discovery.
"""
from unittest.mock import MagicMock, patch
import pytest

from src.core.llm_router import (
    parse_model_version_tuple,
    discover_and_sort_available_models,
    execute_dynamic_json_query,
)


def test_parse_model_version_tuple_sorting():
    """Verify version tuples sort newer versions and flash tiers higher."""
    v37_flash = parse_model_version_tuple("gemini-3.7-flash")
    v25_flash = parse_model_version_tuple("gemini-2.5-flash")
    v15_flash = parse_model_version_tuple("gemini-1.5-flash")
    v15_pro = parse_model_version_tuple("gemini-1.5-pro")

    assert v37_flash > v25_flash
    assert v25_flash > v15_flash
    assert v15_flash > v15_pro


def test_discover_and_sort_available_models_mocked():
    """Verify models are dynamically filtered and sorted from newest to oldest."""
    mock_client = MagicMock()

    m1 = MagicMock(); m1.name = "models/gemini-1.5-flash"
    m2 = MagicMock(); m2.name = "models/gemini-2.5-flash"
    m3 = MagicMock(); m3.name = "models/text-embedding-004"
    m4 = MagicMock(); m4.name = "models/gemini-3.7-flash"

    mock_client.models.list.return_value = [m1, m2, m3, m4]

    sorted_models = discover_and_sort_available_models(mock_client)

    assert "text-embedding-004" not in sorted_models
    assert sorted_models[0] == "gemini-3.7-flash"
    assert sorted_models[1] == "gemini-2.5-flash"
    assert sorted_models[2] == "gemini-1.5-flash"


@patch("google.genai.Client")
def test_execute_dynamic_json_query_fallback(mock_client_cls):
    """Verify router automatically falls back from 503 on newest to second newest."""
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    m1 = MagicMock(); m1.name = "models/gemini-3.7-flash"
    m2 = MagicMock(); m2.name = "models/gemini-2.5-flash"
    mock_client.models.list.return_value = [m1, m2]

    mock_resp_success = MagicMock()
    mock_resp_success.text = '{"status": "success", "tier": "TIER_1"}'

    # Model 1 fails with 503 twice, Model 2 succeeds
    mock_client.models.generate_content.side_effect = [
        Exception("503 UNAVAILABLE: Server high demand"),
        Exception("503 UNAVAILABLE: Server high demand"),
        mock_resp_success
    ]

    result_json, chosen_model = execute_dynamic_json_query(
        prompt="Test Prompt",
        api_key="valid_test_format_key_12345",
    )

    assert result_json["status"] == "success"
    assert chosen_model == "gemini-2.5-flash"
