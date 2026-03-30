"""Unit tests for LLM service retry, timeout, and JSON parse retry logic."""

import json
import time
import pytest
from unittest.mock import MagicMock

from openai import APITimeoutError, APIStatusError

from app.services.llm_service import (
    generate_structured,
    is_retryable_http_error,
    TIMEOUTS,
)
from app.exceptions.llm_exceptions import (
    LLMRetryExhaustedError,
    LLMJSONParseError,
    LLMTimeoutError,
)


# =============================================================================
# Retry behavior tests (D-02)
# =============================================================================


@pytest.mark.asyncio
async def test_retry_not_on_400(mock_400_client):
    """HTTP 400 errors should NOT be retried - exactly 1 call made."""
    with pytest.raises(LLMRetryExhaustedError):
        await generate_structured("profile", mock_400_client, "test prompt")
    assert mock_400_client.chat.completions.create.call_count == 1


@pytest.mark.asyncio
async def test_retry_not_on_401():
    """HTTP 401 errors should NOT be retried - exactly 1 call made."""
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 401
    client.chat.completions.create.side_effect = APIStatusError(
        "unauthorized", response=mock_response, body=None
    )
    with pytest.raises(LLMRetryExhaustedError):
        await generate_structured("profile", client, "test prompt")
    assert client.chat.completions.create.call_count == 1


@pytest.mark.asyncio
async def test_retry_yes_on_500(mock_500_client):
    """HTTP 500 errors should be retried - succeeds on second attempt."""
    result = await generate_structured("profile", mock_500_client, "test prompt")
    assert result == {"skill": "test", "level": 5}
    assert mock_500_client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_retry_yes_on_503():
    """HTTP 503 errors should be retried - succeeds on second attempt."""
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 503

    mock_success = MagicMock()
    mock_success.choices = [MagicMock()]
    mock_success.choices[0].message.content = '{"skill":"test","level":5}'
    mock_success.choices[0].message.role = "assistant"
    mock_success.model = "deepseek-chat"

    client.chat.completions.create.side_effect = [
        APIStatusError("service unavailable", response=mock_response, body=None),
        mock_success,
    ]
    result = await generate_structured("profile", client, "test prompt")
    assert result == {"skill": "test", "level": 5}
    assert client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_backoff_intervals():
    """Retry backoff intervals should be approximately 1s, 2s, 4s (tenacity wait_exponential).

    Note: With mocked instant responses, actual wall-clock timing cannot be verified.
    This test verifies tenacity makes 3 calls (2 retries after first failure) which
    demonstrates the backoff retry mechanism is engaged.
    """
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_success = MagicMock()
    mock_success.choices = [MagicMock()]
    mock_success.choices[0].message.content = '{"skill":"test","level":5}'
    mock_success.choices[0].message.role = "assistant"
    mock_success.model = "deepseek-chat"

    # First 2 calls fail with 500, third succeeds
    client.chat.completions.create.side_effect = [
        APIStatusError("server error", response=mock_response, body=None),
        APIStatusError("server error", response=mock_response, body=None),
        mock_success,
    ]

    result = await generate_structured("profile", client, "test prompt")

    assert result == {"skill": "test", "level": 5}
    # tenacity should make 3 total calls: initial + 2 retries (backoff: 1s, 2s, 4s)
    assert client.chat.completions.create.call_count == 3


# =============================================================================
# Timeout configuration tests (D-03)
# =============================================================================


def test_profile_timeout_15s():
    """Profile task timeout should be 15 seconds."""
    assert TIMEOUTS["profile"] == 15.0


def test_report_timeout_45s():
    """Report task timeout should be 45 seconds."""
    assert TIMEOUTS["report"] == 45.0


def test_match_timeout_20s():
    """Match task timeout should be 20 seconds."""
    assert TIMEOUTS["match"] == 20.0


# =============================================================================
# JSON parse retry tests (D-04)
# =============================================================================


@pytest.mark.asyncio
async def test_json_retry_succeeds_second_attempt(mock_deepseek_client_json_fail):
    """JSON parse failure triggers retry; succeeds on second attempt."""
    result = await generate_structured(
        "profile", mock_deepseek_client_json_fail, "test prompt"
    )
    assert result == {"skill": "test", "level": 5}
    assert mock_deepseek_client_json_fail.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_json_retry_fails_both():
    """If JSON parse fails on all 3 attempts, raise LLMJSONParseError."""
    client = MagicMock()
    mock_bad = MagicMock()
    mock_bad.choices = [MagicMock()]
    mock_bad.choices[0].message.content = "not json at all"
    mock_bad.choices[0].message.role = "assistant"

    # All 3 calls return non-JSON
    client.chat.completions.create.return_value = mock_bad

    with pytest.raises(LLMJSONParseError):
        await generate_structured("profile", client, "test prompt")
    # 1 initial + 2 retries = 3 total calls
    assert client.chat.completions.create.call_count == 3


# =============================================================================
# is_retryable_http_error predicate tests
# =============================================================================


def test_is_retryable_true_for_timeout():
    """APITimeoutError should be retryable."""
    assert is_retryable_http_error(APITimeoutError("timed out")) is True


def test_is_retryable_true_for_500_503_429():
    """500, 503, and 429 status codes should be retryable."""
    for code in (500, 503, 429):
        mock_response = MagicMock()
        mock_response.status_code = code
        exc = APIStatusError("error", response=mock_response, body=None)
        assert is_retryable_http_error(exc) is True, f"Status {code} should be retryable"


def test_is_retryable_false_for_400_401():
    """400 and 401 status codes should NOT be retryable."""
    for code in (400, 401):
        mock_response = MagicMock()
        mock_response.status_code = code
        exc = APIStatusError("error", response=mock_response, body=None)
        assert is_retryable_http_error(exc) is False, f"Status {code} should NOT be retryable"
