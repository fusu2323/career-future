---
phase: 05-llm-service
plan: "05-01"
subsystem: infra
tags: [fastapi, deepseek, openai-sdk, tenacity, pydantic, retry, timeout]

# Dependency graph
requires: []
provides:
  - "LLM service layer with generate_structured() for profile/match/report tasks"
  - "DeepSeek client factory (get_deepseek_client) with OpenAI-compatible interface"
  - "Pydantic models: LLMGenerateRequest, LLMGenerateResponse, HealthResponse"
  - "5 custom exception types: LLMServiceError, LLMTimeoutError, LLMJSONParseError, LLMRetryExhaustedError, LLMValidationError"
affects: [phase-06-resume-parser, phase-07-student-profile, phase-08-matching, phase-09-report-gen]

# Tech tracking
tech-stack:
  added: [fastapi, openai (SDK 2.x), tenacity, pydantic-settings]
  patterns:
    - "Lazy Settings initialization to avoid import-time ValidationError"
    - "asyncio.timeout + asyncio.to_thread for async timeout of sync SDK calls"
    - "tenacity retry with exponential backoff on APITimeoutError/APIStatusError"
    - "Separate JSON parse retry loop (up to 2 additional calls) inside HTTP retry loop"

key-files:
  created:
    - "app/models/llm_models.py"
    - "app/clients/deepseek.py"
    - "app/config.py"
    - "app/exceptions/llm_exceptions.py"
    - "app/services/llm_service.py"

key-decisions:
  - "DeepSeek deepseek-chat model, base_url https://api.deepseek.com, temperature 0.1"
  - "HTTP retry: 3x with exponential backoff (1s/2s/4s), retry on 5xx/503/429/timeout, NOT on 400/401"
  - "Timeout per task: profile=15s, match=20s, report=45s via asyncio.timeout"
  - "JSON parse retry: 1-2 additional LLM calls on JSONDecodeError before raising LLMJSONParseError"
  - "Lazy Settings loading in get_deepseek_client() to allow module import without DEEPSEEK_API_KEY"

patterns-established:
  - "Pattern: LLM client factory with @lru_cache for connection reuse"
  - "Pattern: is_retryable_http_error() predicate for selective retry"
  - "Pattern: generate_structured(task_type, client, prompt) async function"

requirements-completed: [TECH-01]

# Metrics
duration: 3min
completed: 2026-03-30
---

# Phase 05 Plan 01: Core Service Infrastructure Summary

**LLM service infrastructure with DeepSeek client factory, Pydantic models, custom exceptions, and retry/timeout/JSON-parse-retry logic**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-30T14:19:48Z
- **Completed:** 2026-03-30T14:22:44Z
- **Tasks:** 4
- **Files modified:** 9

## Accomplishments

- Pydantic request/response models with field validation (task_type, prompt, temperature, max_tokens)
- DeepSeek client factory using OpenAI SDK 2.x with @lru_cache and lazy Settings loading
- 5 custom exception types for granular LLM error handling
- LLM service with tenacity HTTP retry (3x, exponential backoff), asyncio.timeout per task, and JSON parse retry (up to 2x)

## Task Commits

Each task was committed atomically:

1. **Task 1: Pydantic request/response models** - `bc47298` (feat)
2. **Task 2: DeepSeek client wrapper + config** - `a14f5ce` (feat)
3. **Task 3: Custom exceptions** - `7d188e1` (feat)
4. **Task 4: LLM service with retry + timeout + JSON parse retry** - `872e245` (feat)
5. **Fix: Lazy Settings loading** - `512428f` (fix)

## Files Created/Modified

- `app/__init__.py` - Package init
- `app/models/__init__.py` - Model exports
- `app/models/llm_models.py` - LLMGenerateRequest, LLMGenerateResponse, HealthResponse
- `app/clients/__init__.py` - Client exports
- `app/clients/deepseek.py` - get_deepseek_client() factory with lazy Settings
- `app/config.py` - pydantic-settings with deepseek_api_key, base_url, log_level
- `app/exceptions/__init__.py` - Exception exports
- `app/exceptions/llm_exceptions.py` - LLMServiceError, LLMTimeoutError, LLMJSONParseError, LLMRetryExhaustedError, LLMValidationError
- `app/services/__init__.py` - Package init
- `app/services/llm_service.py` - generate_structured, TIMEOUTS, is_retryable_http_error

## Decisions Made

- Used lazy Settings initialization in get_deepseek_client() to avoid import-time failure when DEEPSEEK_API_KEY is not set
- is_retryable_http_error returns True for 5xx, 503, 429, and APITimeoutError; returns False for 400, 401
- generate_structured uses asyncio.to_thread to run sync OpenAI SDK from async context while preserving asyncio.timeout semantics

## Deviations from Plan

None - plan executed exactly as written.

## Auto-fixed Issues

**1. [Rule 3 - Blocking] Settings instantiated at module load time caused import-time ValidationError**

- **Found during:** Task 2 (verification step)
- **Issue:** `deepseek.py` called `Settings()` at module import, failing when DEEPSEEK_API_KEY not set
- **Fix:** Moved Settings() instantiation inside `get_deepseek_client()` function (lazy initialization)
- **Files modified:** `app/clients/deepseek.py`
- **Verification:** All imports resolve without DEEPSEEK_API_KEY; client still works when key is set
- **Committed in:** `512428f` (fix)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Blocking issue fixed inline. No scope creep.

## Issues Encountered

None

## User Setup Required

The `DEEPSEEK_API_KEY` environment variable must be set before the service can make API calls. See `.env.example` or set directly:

```bash
export DEEPSEEK_API_KEY=your_key_here
```

## Next Phase Readiness

- Phase 06 (resume parsing) and Phase 07-09 can now import `app.services.llm_service.generate_structured`
- DeepSeek client factory ready for FastAPI dependency injection in Wave 2 router endpoints
- All must_have truths verified:
  - Retry 3x with 1s/2s/4s backoff on 5xx/503/timeout
  - No retry on 400/401
  - Correct timeouts: profile=15s, match=20s, report=45s
  - JSON parse retry 1-2x

---
*Phase: 05-llm-service / Plan 05-01*
*Completed: 2026-03-30*
