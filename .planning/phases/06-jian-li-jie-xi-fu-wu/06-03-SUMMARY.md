---
phase: 06-jian-li-jie-xi-fu-wu
plan: "06-03"
subsystem: api
tags: [fastapi, llm, resume, deepseek, pdf, docx]

# Dependency graph
requires:
  - phase: 06-02
    provides: Router skeleton with extract_pdf_text, extract_docx_text, stub parse_resume
  - phase: 05-llm-service
    provides: generate_structured() with timeout_override support
provides:
  - Full /resume/parse endpoint with LLM call, self-correction, partial fallback
  - TIMEOUTS["resume"] = 20.0 and timeout_override parameter in llm_service
  - 7 integration tests covering STU-01 through STU-05
affects:
  - Phase 07 (student profiling - imports ResumeData model)
  - Phase 10 (frontend - calls /resume/parse endpoint)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Self-correction LLM pattern: retry with corrected prompt focusing on missing fields
    - Partial fallback pattern: graceful degradation when LLM parsing fails
    - FastAPI dependency_overrides for test mocking

key-files:
  created: []
  modified:
    - app/services/llm_service.py - added resume timeout and timeout_override
    - app/routers/resume.py - full LLM parsing with self-correction
    - app/models/resume_models.py - added activity field to ExperienceEntry
    - tests/test_resume.py - 7 integration tests
    - tests/conftest.py - fixed MagicMock chain, added resume_client fixture

key-decisions:
  - "Self-correction on parse failure: retry once with corrected prompt focusing on missing_fields (D-05)"
  - "20s timeout for resume parsing: TIMEOUTS['resume'] = 20.0, timeout_override=20.0 (D-03)"
  - "Partial fallback: _build_partial_resume() returns ResumeData with missing_fields populated on ultimate failure"

patterns-established:
  - "FastAPI file upload with 10MB size check, 413 on exceed"
  - "LLM self-correction pattern: attempt 1 -> failure -> identify missing -> attempt 2 -> ultimate fallback"

requirements-completed: [STU-01, STU-02, STU-03, STU-04, STU-05]

# Metrics
duration: ~8min
completed: 2026-03-30
---

# Phase 6 Plan 3: Resume Parsing Endpoint Summary

**Full /resume/parse endpoint with LLM call, self-correction retry, and 7 passing integration tests covering STU-01 through STU-05**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-30T16:42:54Z
- **Completed:** 2026-03-30
- **Tasks:** 3/3
- **Files modified:** 5

## Accomplishments

- Full LLM-powered resume parsing with 20s timeout (timeout_override=20.0)
- Self-correction pattern: retry with corrected prompt on failure, populates missing_fields
- Partial fallback on ultimate failure: returns ResumeData with missing_fields tracking
- 7 integration tests covering all STU requirements (file upload, basic info, education, skills, experience)
- Fixed MagicMock chain bug in conftest fixtures (each `choices[0]` access was creating new mock)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add resume timeout to llm_service.py** - `cfae73d` (feat)
2. **Task 2: Implement full /resume/parse endpoint with self-correction** - `7865f8d` (feat)
3. **Task 3: Implement integration tests for STU-01 through STU-05** - `667098f` (test)

## Files Created/Modified

- `app/services/llm_service.py` - Added TIMEOUTS["resume"]=20.0 and timeout_override parameter to generate_structured()
- `app/routers/resume.py` - Full parse_resume with generate_structured call, self-correction, partial fallback; RESUME_PARSE_PROMPT_CORRECTED, _identify_missing_fields, _build_partial_resume
- `app/models/resume_models.py` - Added activity field to ExperienceEntry (was missing from original model)
- `tests/test_resume.py` - 7 tests: test_file_size_limit, test_parse_pdf_upload, test_parse_docx_upload, test_basic_info_fields, test_education_fields, test_skills_fields, test_experience_fields
- `tests/conftest.py` - Fixed sample_pdf_bytes (Chinese in bytes literal bug); fixed MagicMock chain (explicit mock_choice with message); added resume_client fixture using app.dependency_overrides

## Decisions Made

- Self-correction retry uses RESUME_PARSE_PROMPT_CORRECTED with {missing_fields} placeholder
- Self-correction is triggered when raw_result is None (any exception caught)
- _identify_missing_fields_from_error returns ["education", "professional_skills", "experience"] as heuristic fallback
- resume_client fixture uses app.dependency_overrides[get_deepseek_client] rather than patch (proper FastAPI DI mechanism)

## Deviations from Plan

None - plan executed exactly as written.

### Auto-fixed Issues

**1. [Rule 3 - Blocking] sample_pdf_bytes fixture had Chinese chars inside bytes literal (syntax error)**
- **Found during:** Task 3 (integration tests)
- **Issue:** tests/conftest.py line 125 had Chinese text inside b"" bytes literal - invalid Python syntax
- **Fix:** Replaced with pure ASCII PDF content, Chinese doesn't affect test since LLM client is mocked
- **Files modified:** tests/conftest.py
- **Verification:** pytest tests/test_resume.py passes
- **Committed in:** `667098f` (Task 3 commit)

**2. [Rule 1 - Bug] MagicMock chain: choices[0] returned new mock on each access**
- **Found during:** Task 3 (integration tests)
- **Issue:** mock_completion.choices = [MagicMock()] and then mock_completion.choices[0].message = mock_message - each choices[0] access created NEW MagicMock, losing message assignment
- **Fix:** Use explicit mock_choice = MagicMock(); mock_choice.message = mock_message; mock_completion.choices = [mock_choice]
- **Files modified:** tests/conftest.py (all mock fixtures: mock_deepseek_client, mock_resume_llm_client, mock_deepseek_client_json_fail, mock_500_client)
- **Verification:** All 7 tests pass
- **Committed in:** `667098f` (Task 3 commit)

**3. [Rule 2 - Missing Critical] ExperienceEntry missing 'activity' field**
- **Found during:** Task 3 (integration tests)
- **Issue:** ExperienceEntry model had company, name, position, role, duration, description but NOT activity field (used in extracurriculars)
- **Fix:** Added `activity: Optional[str] = None` to ExperienceEntry
- **Files modified:** app/models/resume_models.py
- **Verification:** test_experience_fields passes with activity assertion
- **Committed in:** `667098f` (Task 3 commit)

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 bug, 1 missing critical)
**Impact on plan:** All auto-fixes were necessary for tests to run and pass. No scope creep.

## Issues Encountered

- MagicMock's auto-creation of nested attributes (choices[0].message) made fixture setup non-obvious; resolved by using explicit mock objects in a real list
- FastAPI dependency_overrides requires using the actual function object as key; @lru_cache on get_deepseek_client meant override had to be set before any cached call

## Next Phase Readiness

- Phase 07 can import ResumeData model directly from app.models.resume_models
- /resume/parse endpoint ready for integration with Phase 07's profiling service
- All STU requirements (STU-01 through STU-05) are tested and passing

---
*Phase: 06-jian-li-jie-xi-fu-wu*
*Completed: 2026-03-30*
