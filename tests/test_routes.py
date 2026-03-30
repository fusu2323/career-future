"""Integration tests for LLM service HTTP endpoints and health checks."""

import asyncio
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from openai import APITimeoutError, APIStatusError

from app.main import app
from app.clients.deepseek import get_deepseek_client
from app.exceptions.llm_exceptions import LLMTimeoutError, LLMJSONParseError, LLMRetryExhaustedError


# =============================================================================
# Health endpoint tests
# =============================================================================


def test_health_returns_ok():
    """GET /health returns 200 with status ok without calling DeepSeek."""
    # Use a dummy client to ensure /health doesn't call DeepSeek
    dummy_client = MagicMock()
    app.dependency_overrides[get_deepseek_client] = lambda: dummy_client

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "llm-service"}

    # Verify DeepSeek was NOT called (dummy client still has 0 calls)
    assert dummy_client.chat.completions.create.call_count == 0

    # Clean up override
    app.dependency_overrides.clear()


@pytest.mark.skip(reason="requires live DeepSeek API")
def test_health_ready_when_deepseek_up():
    """GET /health/ready returns 200 when DeepSeek API is reachable."""
    with TestClient(app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 200


# =============================================================================
# LLM endpoint success tests
# =============================================================================


def test_profile_generate_success(mock_deepseek_client):
    """POST /llm/profile/generate returns 200 with success=True on valid mock."""
    app.dependency_overrides[get_deepseek_client] = lambda: mock_deepseek_client

    with TestClient(app) as client:
        response = client.post(
            "/llm/profile/generate",
            json={"task_type": "profile", "prompt": "Generate a profile", "temperature": 0.1},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["task_type"] == "profile"

    app.dependency_overrides.clear()


def test_match_analyze_success(mock_deepseek_client):
    """POST /llm/match/analyze returns 200 with success=True on valid mock."""
    app.dependency_overrides[get_deepseek_client] = lambda: mock_deepseek_client

    with TestClient(app) as client:
        response = client.post(
            "/llm/match/analyze",
            json={"task_type": "match", "prompt": "Analyze match", "temperature": 0.1},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["task_type"] == "match"

    app.dependency_overrides.clear()


def test_report_generate_success(mock_deepseek_client):
    """POST /llm/report/generate returns 200 with success=True on valid mock."""
    app.dependency_overrides[get_deepseek_client] = lambda: mock_deepseek_client

    with TestClient(app) as client:
        response = client.post(
            "/llm/report/generate",
            json={"task_type": "report", "prompt": "Generate a report", "temperature": 0.1},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["task_type"] == "report"

    app.dependency_overrides.clear()


# =============================================================================
# Validation error tests (422)
# =============================================================================


def test_invalid_prompt_returns_422(mock_deepseek_client):
    """POST with empty prompt returns 422 (min_length=1 violation)."""
    app.dependency_overrides[get_deepseek_client] = lambda: mock_deepseek_client

    with TestClient(app) as client:
        response = client.post(
            "/llm/profile/generate",
            json={"task_type": "profile", "prompt": "", "temperature": 0.1},
        )

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_invalid_temperature_returns_422(mock_deepseek_client):
    """POST with temperature > 2.0 returns 422 (max validation violation)."""
    app.dependency_overrides[get_deepseek_client] = lambda: mock_deepseek_client

    with TestClient(app) as client:
        response = client.post(
            "/llm/profile/generate",
            json={"task_type": "profile", "prompt": "test prompt", "temperature": 5.0},
        )

    assert response.status_code == 422

    app.dependency_overrides.clear()


# =============================================================================
# HTTP error handling tests
# =============================================================================


def test_400_not_retried(mock_400_client):
    """HTTP 400 returns 502 after 1 call (retry exhausted for non-retryable error)."""
    app.dependency_overrides[get_deepseek_client] = lambda: mock_400_client

    with TestClient(app) as client:
        response = client.post(
            "/llm/profile/generate",
            json={"task_type": "profile", "prompt": "test prompt", "temperature": 0.1},
        )

    assert response.status_code == 502
    # Verify only 1 call was made (no retry on 400)
    assert mock_400_client.chat.completions.create.call_count == 1

    app.dependency_overrides.clear()


def test_timeout_returns_504(mock_timeout_client):
    """HTTP timeout returns 504 Gateway Timeout."""
    app.dependency_overrides[get_deepseek_client] = lambda: mock_timeout_client

    # Mock asyncio.timeout to raise asyncio.TimeoutError on __aenter__
    class FakeTimeoutContext:
        async def __aenter__(self):
            raise asyncio.TimeoutError
        async def __aexit__(self, *args):
            return False

    def fake_timeout(*args, **kwargs):
        return FakeTimeoutContext()

    with TestClient(app) as client:
        with patch("app.services.llm_service.asyncio.timeout", side_effect=fake_timeout):
            response = client.post(
                "/llm/profile/generate",
                json={"task_type": "profile", "prompt": "test prompt", "temperature": 0.1},
            )

    assert response.status_code == 504

    app.dependency_overrides.clear()


def test_500_returns_502_after_retry(mock_500_client):
    """HTTP 500 returns 502 after all retries exhausted."""
    app.dependency_overrides[get_deepseek_client] = lambda: mock_500_client

    # Make mock_500_client raise 500 on first 3 calls
    from unittest.mock import MagicMock as Mock
    from openai import APIStatusError
    mock_response = Mock()
    mock_response.status_code = 500
    mock_500_client.chat.completions.create.side_effect = [
        APIStatusError("server error", response=mock_response, body=None),
        APIStatusError("server error", response=mock_response, body=None),
        APIStatusError("server error", response=mock_response, body=None),
    ]

    with TestClient(app) as client:
        response = client.post(
            "/llm/profile/generate",
            json={"task_type": "profile", "prompt": "test prompt", "temperature": 0.1},
        )

    assert response.status_code == 502
    # 3 calls: initial + 2 retries
    assert mock_500_client.chat.completions.create.call_count == 3

    app.dependency_overrides.clear()
