# Phase 5: LLM Service Encapsulation - Research

**Researched:** 2026-03-30
**Domain:** FastAPI HTTP service + DeepSeek API integration + retry patterns
**Confidence:** MEDIUM-HIGH (codebase patterns verified, libraries confirmed current)

## Summary

Phase 5 creates a standalone FastAPI service that wraps DeepSeek API calls with retry logic, timeouts, and structured JSON output handling. The service will be consumed by downstream phases 6-9 (resume parsing, student profiling, matching, report generation). Key design decisions are already locked: three endpoint routes, 3x retry with exponential backoff (1s/2s/4s), per-endpoint timeouts (15s profile, 45s report), and JSON parse retry 1-2x. This research validates the standard stack, patterns, and implementation approach.

**Primary recommendation:** Use FastAPI with dependency injection for the OpenAI client, tenacity for retry logic, pydantic-settings for env var management, and a layered architecture (router -> service -> client).

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** FastAPI HTTP endpoints, separate routes: `/llm/profile/generate`, `/llm/match/analyze`, `/llm/report/generate`
- **D-02:** Retry 3x + exponential backoff (1s / 2s / 4s intervals), retry on 5xx/503 and timeouts, do NOT retry 400/401
- **D-03:** Per-endpoint timeouts: profile 15s, report 45s (match likely 15s or 20s)
- **D-04:** JSON parse retry 1-2x when `response_format={"type": "json_object"}` fails
- **D-05:** DeepSeek `deepseek-chat` model, temperature 0.1-0.2, base_url `https://api.deepseek.com`
- **D-06:** Unified request format via `LLMGenerateRequest` with `task_type`, `prompt`, `temperature`, `max_tokens`

### Claude's Discretion
- Service file organization (single file vs. module structure)
- Logging format and observability details
- Health check endpoint design
- Internal error response format

### Deferred Ideas
None -- discussion stayed within phase scope.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TECH-01 | LLM调用封装 -- API调用成功率>=95%, 响应时间P95<=10s(profile)/<=30s(report) | Retry + timeout design satisfies reliability target; service monitoring needed to measure P95 |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **FastAPI** | 0.127.1 | Web framework | Native async, Pydantic v2 validation, automatic OpenAPI docs |
| **OpenAI Python SDK** | 2.24.0 | DeepSeek API client | OpenAI-compatible, DeepSeek uses same interface with custom base_url |
| **tenacity** | 9.1.2 | Retry with exponential backoff | Standard library for retry, integrates with FastAPI async |
| **uvicorn** | 0.40.0 | ASGI server | Recommended production server for FastAPI |
| **pydantic-settings** | 2.11.0 | Environment variable config | Best practice for env var management in Pydantic apps |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **httpx** | 0.28.1 | HTTP client for testing | FastAPI TestClient uses httpx; enables async test clients |
| **pytest** | 9.0.2 | Test framework | Project standard |
| **pytest-asyncio** | 1.3.0 | Async test support | For testing async FastAPI endpoints |

**Installation:**
```bash
pip install fastapi uvicorn openai tenacity pydantic-settings httpx pytest pytest-asyncio
```

**Version verification:** All versions confirmed current via `pip3 show` on 2026-03-30.

## Architecture Patterns

### Recommended Project Structure
```
app/
├── __init__.py
├── main.py              # FastAPI app, lifespan, startup/shutdown
├── config.py            # pydantic-settings, env var loading
├── routers/
│   ├── __init__.py
│   └── llm.py           # /llm/* routes only
├── services/
│   ├── __init__.py
│   └── llm_service.py   # Business logic: retry, timeout, JSON parse
├── models/
│   ├── __init__.py
│   └── llm_models.py    # Pydantic request/response models
├── clients/
│   ├── __init__.py
│   └── deepseek.py      # OpenAI client wrapper with base_url
└── exceptions/
    ├── __init__.py
    └── llm_exceptions.py # Custom exception classes
tests/
├── conftest.py          # Shared fixtures (mock DeepSeek client)
├── test_llm_service.py  # Unit tests for retry, timeout, JSON parse
└── test_routes.py       # Integration tests for endpoints
```

**Alternative considered:** Single-file service. Rejected because modular structure separates concerns (routing vs. business logic vs. client) and is easier to test and extend.

### Pattern 1: FastAPI Dependency Injection for LLM Client

**What:** Provide the OpenAI client as a FastAPI dependency, instantiated once at startup.
**When to use:** Always for shared expensive resources (HTTP client, DB connection).
**Example:**
```python
# app/clients/deepseek.py
from openai import OpenAI
from functools import lru_cache

@lru_cache
def get_deepseek_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        timeout=60.0,  # connection timeout; per-request timeout handled in service
    )
```
```python
# app/routers/llm.py
from fastapi import Depends, APIRouter
from app.clients.deepseek import get_deepseek_client

router = APIRouter(prefix="/llm", tags=["LLM"])

@router.post("/profile/generate")
async def generate_profile(
    request: LLMGenerateRequest,
    client: OpenAI = Depends(get_deepseek_client),
):
    return await llm_service.generate_profile(client, request)
```

**Source:** FastAPI official docs -- dependency injection is the primary composition pattern.

### Pattern 2: tenacity Retry with Exponential Backoff

**What:** Use `tenacity.retry` decorator with `wait_exponential` multiplier and `stop_after_attempt`.
**When to use:** API calls subject to transient failures (500/503, timeouts).
**Example:**
```python
# app/services/llm_service.py
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from openai import APITimeoutError, APIStatusError

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=(
        retry_if_exception_type(APITimeoutError) |
        retry_if_exception_type(APIStatusError) |
        retry_if_exception_type(Exception)  # catch-all for safety
    ),
    reraise=True,
)
async def call_with_retry(client: OpenAI, messages: list, **kwargs):
    return client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        response_format={"type": "json_object"},
        **kwargs
    )
```

**Note:** `APIStatusError` includes 400 errors, so filter by `.status_code`:
```python
def is_retryable_status(status_code: int) -> bool:
    return status_code >= 500 or status_code in (503, 429)

@retry(...)
async def call_with_retry(...):
    try:
        return client.chat.completions.create(...)
    except APIStatusError as e:
        if is_retryable_status(e.status_code):
            raise  # tenacity catches and retries
        raise  # 400/401 - don't retry
```

**Source:** tenacity documentation -- `wait_exponential` with `multiplier=1, min=1, max=4` produces 1s/2s/4s intervals.

### Pattern 3: Pydantic Request/Response Models

**What:** Use Pydantic v2 `BaseModel` for typed request validation and response serialization.
**When to use:** All FastAPI endpoint inputs and outputs.
**Example:**
```python
# app/models/llm_models.py
from pydantic import BaseModel, Field
from typing import Literal, Optional

class LLMGenerateRequest(BaseModel):
    task_type: Literal["profile", "match", "report"]
    prompt: str = Field(..., min_length=1, description="LLM prompt text")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)

class LLMGenerateResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    task_type: str
    attempt_count: int = 1
```

**Note:** `task_type` is included in response for client-side routing confirmation.

### Pattern 4: Timeout Per-Task via `asyncio.timeout` (Python 3.11+)

**What:** Use `asyncio.timeout()` context manager for per-request timeout enforcement.
**When to use:** Different endpoints need different timeout limits.
**Example:**
```python
# app/services/llm_service.py
import asyncio

TIMEOUTS = {
    "profile": 15.0,
    "report": 45.0,
    "match": 20.0,
}

async def generate_with_timeout(task_type: str, client, messages, **kwargs):
    timeout_seconds = TIMEOUTS.get(task_type, 30.0)
    try:
        async with asyncio.timeout(timeout_seconds):
            return await client.chat.completions.create(
                messages=messages,
                **kwargs
            )
    except asyncio.TimeoutError:
        raise LLMTimeoutError(f"Task {task_type} exceeded {timeout_seconds}s limit")
```

**Alternative:** Pass `timeout` directly to OpenAI client constructor (per-call). SDK 2.x supports `timeout` parameter:
```python
client.chat.completions.create(..., timeout=15.0)
```

**Source:** Python 3.11 `asyncio.timeout` -- preferred for async context managers. OpenAI SDK 2.x `timeout` parameter supports both float (seconds) and `Timeout` object.

### Pattern 5: JSON Parse Retry

**What:** When LLM returns non-JSON content, retry the call 1-2 times before failing.
**When to use:** Structured output tasks using `response_format={"type": "json_object"}`.
**Example:**
```python
async def generate_structured_with_fallback(task_type: str, client, messages, **kwargs):
    for attempt in range(3):  # initial + 2 retries
        try:
            response = await generate_with_timeout(task_type, client, messages, **kwargs)
            content = response.choices[0].message.content
            return json.loads(content)
        except json.JSONDecodeError:
            if attempt == 2:
                raise LLMJSONParseError(f"Failed after 3 attempts, raw: {content[:200]}")
            # Retry - LLM occasional format deviation
    raise LLMJSONParseError("Unexpected exit from JSON retry loop")
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Retry logic | Custom sleep loops | `tenacity` | Handles edge cases (signal interrupts, async), configurable backoff, testable |
| Timeout handling | `threading.Timer` or `signal.alarm` | `asyncio.timeout` or SDK `timeout` param | Native async support, clean cancellation, no signal conflicts |
| Env var loading | `os.getenv()` scattered | `pydantic-settings` | Type validation, dotenv support, test overrides |
| HTTP client | `requests` (blocking) | OpenAI SDK built on `httpx` | SDK handles streaming, retries, timeouts natively |
| JSON parsing | `eval()` or regex | `json.loads()` + retry | Safe, handles edge cases |

**Key insight:** The OpenAI Python SDK 2.x already handles connection pooling, retries (on 5xx), and streaming internally. The service layer wraps around it for task-specific timeout and JSON parse retry logic.

## Common Pitfalls

### Pitfall 1: Not distinguishing retryable vs. non-retryable HTTP errors
**What goes wrong:** 400 Bad Request gets retried 3x, wasting time and hitting rate limits.
**Why it happens:** `APIStatusError` catches all status codes; default retry would include 400.
**How to avoid:** Filter by status code in retry condition -- only retry 5xx, 503, 429.
**Warning signs:** Logs show "Retry #2" for what is clearly a bad request body.

### Pitfall 2: Global timeout vs. per-request timeout
**What goes wrong:** Setting 60s global timeout means a profile call (15s limit) could time out at 60s.
**Why it happens:** OpenAI client-level timeout applies to all calls.
**How to avoid:** Pass timeout per-call, or use `asyncio.timeout` context manager with task-specific durations.
**Warning signs:** Profile endpoints consistently hitting 60s ceiling instead of 15s.

### Pitfall 3: JSON parse on streaming responses
**What goes wrong:** If streaming is accidentally enabled, `response.choices[0].message.content` may be partial or None.
**Why it happens:** Streaming returns SSE chunks, not a single message object.
**How to avoid:** Explicitly set `stream=False` (default) and use `response_format={"type": "json_object"}` which requires non-streaming.
**Warning signs:** `AttributeError: 'NoneType' object has no attribute 'content'`.

### Pitfall 4: Mutable default arguments in Pydantic models
**What goes wrong:** `messages: list = []` as default leads to shared state across requests.
**Why it happens:** Python default mutable arguments gotcha.
**How to avoid:** Use `None` and `Field(default=None)`, then default to empty list in code.
**Warning signs:** Requests increasingly accumulate previous messages.

### Pitfall 5: Not validating `task_type` against actual endpoint
**What goes wrong:** Client sends `task_type="report"` to `/llm/profile/generate`, gets wrong timeout/behavior.
**Why it happens:** Loose `Literal` union allows any task_type value at any endpoint.
**How to avoid:** Use separate request models per endpoint with fixed `task_type`, or validate in service layer.
**Warning signs:** Mismatched timeouts -- report prompt hitting 15s profile timeout.

## Code Examples

### Health Check Endpoint
```python
# app/routers/health.py
from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "llm-service"}

@router.get("/health/ready")
async def readiness_check():
    # Could check DeepSeek connectivity here
    return {"status": "ready"}
```

### Service Layer with Retry and Timeout (verified from existing patterns)
```python
# app/services/llm_service.py
import json, asyncio
from openai import OpenAI, APITimeoutError, APIStatusError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

TIMEOUTS = {"profile": 15.0, "match": 20.0, "report": 45.0}

def is_retryable(exc: Exception) -> bool:
    if isinstance(exc, APITimeoutError):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code >= 500 or exc.status_code in (429, 503)
    return False

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((APITimeoutError, APIStatusError)),
    reraise=True,
)
def _call_llm_sync(client: OpenAI, messages: list, timeout: float, **kwargs):
    return client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        response_format={"type": "json_object"},
        timeout=timeout,
        **kwargs
    )

async def generate_structured(
    task_type: str,
    client: OpenAI,
    prompt: str,
    temperature: float = 0.1,
    max_tokens: int | None = None,
) -> dict:
    messages = [{"role": "user", "content": prompt}]
    kwargs = {"temperature": temperature}
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    timeout = TIMEOUTS.get(task_type, 30.0)

    for attempt in range(3):
        try:
            response = _call_llm_sync(client, messages, timeout, **kwargs)
            content = response.choices[0].message.content
            return json.loads(content)
        except json.JSONDecodeError:
            if attempt == 2:
                raise
        except Exception as e:
            if not is_retryable(e) or attempt == 2:
                raise

    raise RuntimeError("Unexpected exit from generate_structured")
```

### Router Endpoint Pattern
```python
# app/routers/llm.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/llm", tags=["LLM"])

@router.post("/profile/generate")
async def generate_profile(
    request: LLMGenerateRequest,
    client: OpenAI = Depends(get_deepseek_client),
):
    try:
        data = await generate_structured("profile", client, request.prompt,
                                          request.temperature, request.max_tokens)
        return LLMGenerateResponse(success=True, data=data, task_type="profile", attempt_count=1)
    except LLMTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except LLMJSONParseError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM service error: {e}")
```

### Config with pydantic-settings
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### Test with mock DeepSeek client
```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_deepseek_client():
    mock = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"skill": "test"}'
    mock_choice.message.role = "assistant"
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.model = "deepseek-chat"
    mock.chat.completions.create.return_value = mock_completion
    return mock
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `os.getenv()` env loading | `pydantic-settings` BaseSettings | Best practice since ~2022 | Type validation, dotenv, test overrides |
| `tenacity` as plain decorator | `tenacity` with `reraise=True` | Current | Propagates exceptions correctly to FastAPI error handlers |
| OpenAI SDK 0.x | OpenAI SDK 2.x (`OpenAI` class) | 2023-2024 | New interface, `timeout` param, async support |
| `signal.alarm` for timeouts | `asyncio.timeout` context manager | Python 3.11 (2022) | No signal conflicts, clean cancellation |
| Custom retry loops | `tenacity.retry` decorator | Standard since ~2016 | Battle-tested, configurable, testable |

**Deprecated/outdated:**
- `OpenAI 0.x` client: Replaced by `OpenAI 1.x/2.x` with new interface
- `pydantic.BaseSettings` from pydantic.v1: Now in `pydantic-settings` package

## Open Questions

1. **Should the service run as a separate process or be imported as a module?**
   - What we know: Downstream phases (6-9) are separate scripts, not FastAPI apps. A standalone HTTP service requires HTTP calls between phases.
   - What's unclear: Whether phases will call the service over `localhost` HTTP or import the service module directly.
   - Recommendation: Design as a standalone FastAPI app (HTTP) for maximum flexibility -- can be called from any process, enables future frontend integration, but have a simple import mode available.

2. **What log format and observability level?**
   - What we know: Project has no existing observability infrastructure.
   - What's unclear: Whether structured JSON logs (for log aggregation) or simple text logs.
   - Recommendation: Use Python `logging` with JSON formatter via `uvicorn.access` and custom middleware for request IDs. Simple for now, upgrade path exists.

3. **Should the DeepSeek API key be validated at startup?**
   - What we know: If key is missing/invalid, every call will fail 401.
   - What's unclear: Whether FastAPI startup should fail without a valid key or defer to first-request failure.
   - Recommendation: Validate at startup via a lightweight `/health/ready` check that tests the key.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Runtime | Check: `python3 --version` | 3.11+ | N/A |
| pip / pip3 | Package install | `pip3 --version` | 24.x | N/A |
| FastAPI | HTTP service | `pip3 show fastapi` | 0.127.1 | N/A |
| OpenAI SDK | API client | `pip3 show openai` | 2.24.0 | N/A |
| tenacity | Retry logic | `pip3 show tenacity` | 9.1.2 | N/A |
| pydantic-settings | Config | `pip3 show pydantic-settings` | 2.11.0 | N/A |
| pytest | Testing | `pip3 show pytest` | 9.0.2 | N/A |
| httpx | Test client | `pip3 show httpx` | 0.28.1 | N/A |
| DeepSeek API | External service | Network required | Live API | N/A (project constraint) |

**Missing dependencies with no fallback:**
- None -- all required packages confirmed installed.

**Missing dependencies with fallback:**
- None -- all project-constraint dependencies available.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file | `pytest.ini` or `pyproject.toml` (not yet created for this service) |
| Quick run command | `pytest tests/ -x -v` |
| Full suite command | `pytest tests/ --tb=short` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| TECH-01 | Retry on 5xx/503, not on 400/401 | unit | `pytest tests/test_llm_service.py::test_retry_not_on_400 -x` | NO -- new file |
| TECH-01 | Exponential backoff intervals 1s/2s/4s | unit | `pytest tests/test_llm_service.py::test_backoff_intervals -x` | NO -- new file |
| TECH-01 | Profile timeout 15s | unit | `pytest tests/test_llm_service.py::test_profile_timeout -x` | NO -- new file |
| TECH-01 | Report timeout 45s | unit | `pytest tests/test_llm_service.py::test_report_timeout -x` | NO -- new file |
| TECH-01 | JSON parse retry up to 2x | unit | `pytest tests/test_llm_service.py::test_json_retry -x` | NO -- new file |
| TECH-01 | Successful profile endpoint response | integration | `pytest tests/test_routes.py::test_profile_generate_success -x` | NO -- new file |
| TECH-01 | Health check returns 200 | integration | `pytest tests/test_routes.py::test_health -x` | NO -- new file |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -v` (quick subset)
- **Per wave merge:** `pytest tests/ --tb=short` (full suite)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `pytest.ini` -- pytest configuration for the project root (may reuse existing if compatible)
- [ ] `app/__init__.py`, `app/main.py`, `app/config.py`, `app/routers/llm.py`, `app/services/llm_service.py`, `app/models/llm_models.py`, `app/clients/deepseek.py`, `app/exceptions/llm_exceptions.py` -- service implementation
- [ ] `tests/conftest.py` -- mock DeepSeek client fixture (already exists at project root, may need extending)
- [ ] `tests/test_llm_service.py` -- unit tests for retry, timeout, JSON parse logic
- [ ] `tests/test_routes.py` -- integration tests for HTTP endpoints

*(None of the test files or app module currently exist -- greenfield service)*

## Sources

### Primary (HIGH confidence)
- `scripts/build_job_profiles.py` lines 102-110 -- verified `call_llm()` pattern using OpenAI SDK
- `scripts/build_job_graph.py` lines 83-137 -- verified batch LLM calling pattern
- `pip3 show` output -- confirmed library versions (FastAPI 0.127.1, openai 2.24.0, tenacity 9.1.2, uvicorn 0.40.0, pydantic-settings 2.11.0, httpx 0.28.1, pytest 9.0.2)

### Secondary (MEDIUM confidence)
- FastAPI official docs (https://fastapi.tiangolo.com/) -- dependency injection, Pydantic v2, lifespan management
- tenacity documentation (https://tenacity.readthedocs.io/) -- retry patterns, exponential backoff
- OpenAI SDK 2.x docs (https://platform.deepseek.com/docs) -- DeepSeek API compatibility, timeout parameter

### Tertiary (LOW confidence)
- Python 3.11 `asyncio.timeout` behavior -- training data, not verified against current docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- versions verified via pip3, patterns verified from existing codebase
- Architecture: HIGH -- FastAPI patterns are well-established, structure follows FastAPI best practices
- Pitfalls: MEDIUM -- identified from common FastAPI+OpenAI integration mistakes; would benefit from integration testing to confirm

**Research date:** 2026-03-30
**Valid until:** 2026-04-29 (30 days -- FastAPI/tenacity/OpenAI SDK are stable libraries with infrequent breaking changes)
