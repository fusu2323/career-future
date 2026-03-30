import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from openai import APITimeoutError, APIStatusError


@pytest.fixture
def jobs_cleaned_path():
    return Path("data/processed/jobs_cleaned.json")


@pytest.fixture
def vector_db_path():
    return Path("data/vector_db")


@pytest.fixture
def collection(vector_db_path):
    import chromadb
    client = chromadb.PersistentClient(path=str(vector_db_path))
    return client.get_collection("job_postings")


@pytest.fixture
def sample_job_record(jobs_cleaned_path):
    with open(jobs_cleaned_path, encoding="utf-8") as f:
        jobs = json.load(f)
    return jobs[0]


# =============================================================================
# Phase 05 LLM Service Fixtures
# =============================================================================


@pytest.fixture
def mock_deepseek_client():
    """Return a MagicMock that simulates a successful DeepSeek API response."""
    client = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = '{"skill":"test","level":5}'
    mock_completion.choices[0].message.role = "assistant"
    mock_completion.model = "deepseek-chat"
    client.chat.completions.create.return_value = mock_completion
    return client


@pytest.fixture
def mock_deepseek_client_json_fail():
    """Return a client that returns non-JSON on first call, valid JSON on second."""
    client = MagicMock()
    mock_fail = MagicMock()
    mock_fail.choices = [MagicMock()]
    mock_fail.choices[0].message.content = "not json"
    mock_fail.choices[0].message.role = "assistant"
    mock_fail.model = "deepseek-chat"

    mock_success = MagicMock()
    mock_success.choices = [MagicMock()]
    mock_success.choices[0].message.content = '{"skill":"test","level":5}'
    mock_success.choices[0].message.role = "assistant"
    mock_success.model = "deepseek-chat"

    client.chat.completions.create.side_effect = [mock_fail, mock_success]
    return client


@pytest.fixture
def mock_timeout_client():
    """Return a client whose chat.completions.create raises APITimeoutError."""
    client = MagicMock()
    client.chat.completions.create.side_effect = APITimeoutError("timed out")
    return client


@pytest.fixture
def mock_500_client():
    """Return a client that raises APIStatusError(500) on first call, succeeds on second."""
    client = MagicMock()

    mock_response_500 = MagicMock()
    mock_response_500.status_code = 500

    mock_success = MagicMock()
    mock_success.choices = [MagicMock()]
    mock_success.choices[0].message.content = '{"skill":"test","level":5}'
    mock_success.choices[0].message.role = "assistant"
    mock_success.model = "deepseek-chat"

    client.chat.completions.create.side_effect = [
        APIStatusError("server error", response=mock_response_500, body=None),
        mock_success,
    ]
    return client


@pytest.fixture
def mock_400_client():
    """Return a client that raises APIStatusError(400) on every call (should NOT retry)."""
    client = MagicMock()
    mock_response_400 = MagicMock()
    mock_response_400.status_code = 400
    client.chat.completions.create.side_effect = APIStatusError(
        "bad request", response=mock_response_400, body=None
    )
    return client
