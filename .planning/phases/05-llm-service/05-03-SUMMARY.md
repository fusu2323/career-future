---
phase: 05-llm-service
plan: "05-03"
subsystem: testing
tags: [pytest, fastapi, tenacity, mock, deepseek]

# Dependency graph
requires:
  - phase: 05-01
    provides: "LLM service layer with generate_structured, is_retryable_http_error, DeepSeek client"
  - phase: 05-02
    provides: "FastAPI router with /llm/* endpoints, /health endpoints, app.main"
provides:
  - "Pytest test infrastructure with 5 shared fixtures for mocking DeepSeek client"
  - "13 unit tests covering HTTP retry behavior, timeout configuration, JSON parse retry"
  - "10 integration tests covering HTTP endpoints and health checks"
affects: [phase-06-resume-parser, phase-07-student-profile, phase-08-matching, phase-09-report-gen]

# Tech tracking
tech-stack:
  added: [pytest, pytest-asyncio, starlette.testclient]
  patterns:
    - "FastAPI TestClient for integration testing without live server"
    - "app.dependency_overrides[get_deepseek_client] for mock injection"
    - "tenacity _retry_if_retryable_http_error predicate for selective retry"

key-files:
  created:
    - "pytest.ini"
    - "tests/__init__.py"
    - "tests/test_llm_service.py"
    - "tests/test_routes.py"
  modified:
    - "tests/conftest.py"
    - "app/services/llm_service.py"

key-decisions:
  - "Added _retry_if_retryable_http_error predicate to tenacity so it only retries on 5xx/503/429, not on 400/401"
  - "Set DEEPSEEK_API_KEY=test-key-for-unit-tests in conftest.py for lifespan startup"
  - "Used unittest.mock.patch to mock asyncio.timeout for timeout 504 test"

patterns-established:
  - "Pattern: dependency override for FastAPI dependency injection in tests"
  - "Pattern: async context manager mock for asyncio.timeout testing"
  - "Pattern: tenacity custom retry predicate combining exception type + application-level check"

requirements-completed: [TECH-01]

# Metrics
duration: 14min
completed: 2026-03-30
---

# Phase 05 Plan 03: Unit and Integration Tests Summary

**pytest test infrastructure with 22 passing tests covering HTTP retry behavior, timeout enforcement, JSON parse retry, and all HTTP endpoint responses**

## Performance

- **Duration:** 14 min
- **Started:** 2026-03-30T14:30:51Z
- **Completed:** 2026-03-30T14:45:25Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- Created pytest configuration (asyncio_mode=auto, testpaths=tests) and 5 mock fixtures for DeepSeek client testing
- Implemented 13 unit tests for service layer: retry/not-retry on HTTP codes, backoff, timeouts, JSON parse retry
- Implemented 10 integration tests for HTTP endpoints: health checks, success cases, validation errors, HTTP error handling
- Fixed tenacity retry bug: 400/401 were being retried 3 times despite is_retryable_http_error check

## Task Commits

1. **Task 1: pytest configuration and shared fixtures** - `436789b` (test)
2. **Task 2: 13 unit tests for service layer** - `7342dfd` (test)
3. **Task 3: 10 integration tests for HTTP endpoints** - `e86f8e3` (test)

## Files Created/Modified

- `pytest.ini` - pytest config with asyncio_mode=auto and testpaths=tests
- `tests/__init__.py` - empty package marker
- `tests/conftest.py` - 5 LLM service fixtures + DEEPSEEK_API_KEY env setup
- `tests/test_llm_service.py` - 13 unit tests for retry/timeout/JSON retry
- `tests/test_routes.py` - 10 integration tests for HTTP endpoints
- `app/services/llm_service.py` - Added _retry_if_retryable_http_error predicate (bug fix)

## Decisions Made

- tenacity retry predicate must check is_retryable_http_error directly (not just exception type) to prevent 400/401 retries
- asyncio.TimeoutError must be raised inside async context manager __aenter__ to be caught by async with block

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] tenacity was retrying 400/401 errors 3 times despite is_retryable_http_error check**

- **Found during:** Task 2 (writing test_retry_not_on_400)
- **Issue:** tenacity decorator had `retry=retry_if_exception_type((APITimeoutError, APIStatusError))` which retries on ALL APIStatusError including 400/401. The re-raise in `_call_with_retry_sync` still allowed tenacity to retry because tenacity intercepts before our code.
- **Fix:** Added `_retry_if_retryable_http_error` predicate that combines exception type check with `is_retryable_http_error()` result. Updated tenacity decorator to use this predicate. Removed redundant try/except in `_call_with_retry_sync`.
- **Files modified:** `app/services/llm_service.py`
- **Verification:** test_retry_not_on_400 and test_retry_not_on_401 now pass with call_count == 1
- **Committed in:** `7342dfd` (part of Task 2 commit)

**2. [Rule 3 - Blocking] TestClient startup failed due to missing DEEPSEEK_API_KEY**

- **Found during:** Task 3 (running first integration test)
- **Issue:** `lifespan` context manager in app.main validates Settings() which requires DEEPSEEK_API_KEY. Tests failed with ValidationError before any test logic ran.
- **Fix:** Added `os.environ.setdefault("DEEPSEEK_API_KEY", "test-key-for-unit-tests")` at top of tests/conftest.py
- **Files modified:** `tests/conftest.py`
- **Verification:** All TestClient tests now start without lifespan errors
- **Committed in:** `e86f8e3` (part of Task 3 commit)

**3. [Rule 1 - Bug] test_timeout_returns_504 raised nameError in mock**

- **Found during:** Task 3 (running timeout test)
- **Issue:** `FakeTimeoutContext.__aenter__` raised `asyncio.TimeoutError` but `asyncio` was not defined in the closure (only imported as `asyncio_module` later). Error: "name 'asyncio' is not defined"
- **Fix:** Added `import asyncio` at top of test_routes.py, removed local import alias
- **Files modified:** `tests/test_routes.py`
- **Verification:** test_timeout_returns_504 now passes with status 504
- **Committed in:** `e86f8e3` (part of Task 3 commit)

---

**Total deviations:** 3 auto-fixed (1 bug, 2 blocking)
**Impact on plan:** All auto-fixes essential for test correctness. No scope creep.

## Issues Encountered

- pytest asyncio_mode=auto required for async test functions to run properly
- `async with` context manager mocking requires __aenter__ to be async and raise inside it (not in body)
- tenacity `wait_exponential` timing cannot be measured with mocked instant API responses (test only verifies call count)

## Must-Haves Verified

All truths from plan verified:
- HTTP 400 and 401 NOT retried (call count == 1): PASS
- HTTP 500, 503, 429 retried with backoff: PASS (3 calls on persistent 500)
- Profile timeout 15s, match 20s, report 45s: PASS (verified via TIMEOUTS dict)
- JSON parse retry up to 2 times: PASS
- All three LLM endpoints return 200 with success=True: PASS
- GET /health returns 200 without calling DeepSeek: PASS
- Invalid prompt (empty) returns 422: PASS
- Invalid temperature (>2.0) returns 422: PASS
- HTTP timeout returns 504: PASS (via asyncio.timeout mock)
- HTTP 400 returns 502: PASS

## Self-Check

- [x] pytest.ini with asyncio_mode=auto exists at project root
- [x] tests/conftest.py has 5 fixtures: mock_deepseek_client, mock_deepseek_client_json_fail, mock_timeout_client, mock_500_client, mock_400_client
- [x] tests/test_llm_service.py has 13 unit tests
- [x] tests/test_routes.py has 10 integration tests (9 pass, 1 skipped - requires live API)
- [x] All tests pass: 22 passed, 1 skipped
- [x] Commit 436789b found in git log
- [x] Commit 7342dfd found in git log
- [x] Commit e86f8e3 found in git log

## Self-Check: PASSED

---
*Phase: 05-llm-service / Plan 05-03*
*Completed: 2026-03-30*
