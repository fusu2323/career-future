# Architecture Research: v1.1 New Feature Integration

**Domain:** AI Career Planning Agent (RAG + Agent pattern)
**Project:** 基于AI的大学生职业规划智能体
**Researched:** 2026-03-30
**Confidence:** MEDIUM-HIGH (existing v1.0 architecture validated; new features follow standard patterns)

---

## Executive Summary

v1.1 adds five major new capabilities to an existing FastAPI + ChromaDB + Neo4j + DeepSeek stack. This document specifies how each new service integrates with the existing codebase, what is NEW vs MODIFIED, and the correct build order respecting dependencies. The architecture follows a pipeline pattern: Resume -> Student Profile -> Match Results -> Career Report, with each stage reusing existing infrastructure (LLM service, vector store, graph DB).

---

## System Overview

### v1.1 Full Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         React Frontend (Phase 10)                           │
│     Resume Upload / Profile Radar / Job Graph Viz / Match Results / PDF    │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ HTTP JSON
┌──────────────────────────────────▼──────────────────────────────────────────┐
│                         FastAPI Backend                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ resume   │  │ student  │  │ matching │  │ report   │  │  health  │    │
│  │  router  │  │  router  │  │  router  │  │  router  │  │  router  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │             │              │           │
│  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐       │           │
│  │ resume   │  │ student  │  │ matching │  │ report   │       │           │
│  │ service  │  │ profiler │  │ engine   │  │ generator│       │           │
│  │(Phase 6) │  │(Phase 7) │  │(Phase 8) │  │(Phase 9) │       │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │           │
│       │             │             │             │              │           │
├───────┴─────────────┴─────────────┴─────────────┴──────────────┴───────────┤
│                            Shared Services                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │   LLM Service    │  │   ChromaDB       │  │   Neo4j                  │  │
│  │  (deepseek.py)   │  │  (job_vector)    │  │  (job_graph)             │  │
│  │  generate_struct │  │  student_vector  │  │  career_paths            │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### What Is NEW vs MODIFIED

| Component | Status | Notes |
|-----------|--------|-------|
| `app/routers/resume.py` | NEW | Phase 6, PDF/DOCX upload endpoint |
| `app/routers/student.py` | NEW | Phase 7, profile CRUD endpoints |
| `app/routers/matching.py` | NEW | Phase 8, match endpoints |
| `app/routers/report.py` | NEW | Phase 9, report generation endpoint |
| `app/services/resume_parser.py` | NEW | Phase 6, text extraction + LLM parsing |
| `app/services/student_profiler.py` | NEW | Phase 7, 7-dimension profile generation |
| `app/services/matching_engine.py` | NEW | Phase 8, 4-dimension scoring |
| `app/services/report_generator.py` | NEW | Phase 9, structured report pipeline |
| `app/models/resume_models.py` | NEW | Pydantic models for resume data |
| `app/models/student_models.py` | NEW | Pydantic models for student profile |
| `app/models/matching_models.py` | NEW | Pydantic models for match results |
| `app/models/report_models.py` | NEW | Pydantic models for career report |
| `app/main.py` | MODIFIED | Add 4 new routers |
| `app/config.py` | MODIFIED | Add new env vars (optional) |
| `app/services/llm_service.py` | REUSED | Existing, no changes needed |
| `app/clients/deepseek.py` | REUSED | Existing, no changes needed |
| `app/routers/llm.py` | REUSED | Existing, no changes needed |
| `app/routers/health.py` | REUSED | Existing, no changes needed |

---

## Component Responsibilities

### Phase 6: Resume Parser Service

**File:** `app/services/resume_parser.py`

**Responsibility:** Accept PDF/DOCX resume files, extract raw text, parse into structured resume data via LLM.

**Boundary:** Input is raw file bytes. Output is structured `ResumeData` Pydantic model.

| Input | Output | External Calls |
|-------|--------|----------------|
| `UploadFile` (PDF/DOCX) | `ResumeData` (name, education, skills, experience, etc.) | `pdfplumber`/`python-docx` for text extraction, `llm_service.generate_structured()` for LLM parsing |

**Key operation:** `parse_resume(file: UploadFile) -> ResumeData`

**Integration:** Reuses existing `llm_service.generate_structured()` with `task_type="profile"` (15s timeout). No new LLM client needed.

**Router:** `app/routers/resume.py` exposes `POST /api/resume/upload`

---

### Phase 7: Student Profiler Service

**File:** `app/services/student_profiler.py`

**Responsibility:** Convert parsed `ResumeData` into a 7-dimension `StudentProfile` with completeness and competitiveness scores.

**Boundary:** Input is `ResumeData`. Output is `StudentProfile` (7 dimensions scored 1-10).

| Input | Output | External Calls |
|-------|--------|----------------|
| `ResumeData` | `StudentProfile` (7D: foundation, skills, quality, potential, etc.) | `llm_service.generate_structured(task_type="profile")`, ChromaDB (store student vector) |

**Key operation:** `build_profile(resume_data: ResumeData) -> StudentProfile`

**Integration:** Student profile vectors are stored in a NEW ChromaDB collection (`students`) for future similarity search. Existing job vector collection (`jobs`) is NOT modified.

**Router:** `app/routers/student.py` exposes `POST /api/student/profile`, `GET /api/student/profile/{id}`

---

### Phase 8: Matching Engine Service

**File:** `app/services/matching_engine.py`

**Responsibility:** Score a `StudentProfile` against a `JobProfile` across 4 dimensions (basic requirements, professional skills, professional quality, development potential).

**Boundary:** Input is `StudentProfile` + optional `JobProfile` (or auto-detect via ChromaDB search). Output is `MatchResult` with 4 dimension scores and an overall score.

| Input | Output | External Calls |
|-------|--------|----------------|
| `StudentProfile`, optional `JobProfile` | `MatchResult` (4D scores + overall) | ChromaDB (vector similarity search for top-K jobs), Neo4j (career path queries), `llm_service.generate_structured(task_type="match")` |

**Key operation:** `match_student_to_job(student: StudentProfile, job: JobProfile) -> MatchResult`

**Integration:** Uses existing ChromaDB job collection for vector search (reuse Phase 2 index). Uses existing Neo4j job graph for career path lookups (reuse Phase 4 graph).

**Router:** `app/routers/matching.py` exposes `POST /api/matching/analyze`, `GET /api/matching/top-jobs/{student_id}`

---

### Phase 9: Report Generator Service

**File:** `app/services/report_generator.py`

**Responsibility:** Generate a comprehensive career planning report from student profile, match results, and career paths.

**Boundary:** Input is `StudentProfile` + `MatchResult` + career path data. Output is `CareerReport` (goal setting, gap analysis, action plan, timeline).

| Input | Output | External Calls |
|-------|--------|----------------|
| `StudentProfile`, `MatchResult`, career path | `CareerReport` (sections + action items) | `llm_service.generate_structured(task_type="report")`, Neo4j (path retrieval), template engine (optional: weasyprint for PDF export) |

**Key operation:** `generate_report(student: StudentProfile, match: MatchResult) -> CareerReport`

**Integration:** Reuses existing Neo4j career path graph. Report is returned as structured JSON; PDF export is handled by frontend or a dedicated `/export` endpoint.

**Router:** `app/routers/report.py` exposes `POST /api/report/generate`

---

## Recommended Project Structure

```
app/
├── main.py                    # MODIFIED: add 4 new routers
├── config.py                  # MODIFIED: add optional new config
├── clients/
│   └── deepseek.py            # REUSED (existing)
├── services/
│   ├── llm_service.py         # REUSED (existing, generate_structured)
│   ├── resume_parser.py       # NEW (Phase 6)
│   ├── student_profiler.py    # NEW (Phase 7)
│   ├── matching_engine.py     # NEW (Phase 8)
│   └── report_generator.py    # NEW (Phase 9)
├── routers/
│   ├── llm.py                 # REUSED (existing)
│   ├── health.py              # REUSED (existing)
│   ├── resume.py              # NEW (Phase 6)
│   ├── student.py             # NEW (Phase 7)
│   ├── matching.py            # NEW (Phase 8)
│   └── report.py              # NEW (Phase 9)
├── models/
│   ├── llm_models.py           # REUSED (existing)
│   ├── resume_models.py        # NEW (Phase 6)
│   ├── student_models.py       # NEW (Phase 7)
│   ├── matching_models.py      # NEW (Phase 8)
│   └── report_models.py        # NEW (Phase 9)
├── exceptions/
│   └── llm_exceptions.py      # REUSED (existing)
```

### Structure Rationale

- **`routers/` flat**: All API routes at same level. No need for nested router groups at this scale. Each phase gets its own router file.
- **`services/` flat**: All business logic in flat service layer. No deep hierarchy needed for 5 new services.
- **`models/` flat by domain**: Models grouped by domain (resume, student, matching, report) rather than all in one file. Clear ownership.
- **No new shared modules**: Reuse existing `llm_service.py`, `deepseek.py`, `config.py` as-is.

---

## Data Flow

### End-to-End Flow: Resume to Report

```
[Frontend: Upload Resume]
         │
         ▼
POST /api/resume/upload (resume.py)
         │
         ▼
resume_parser.parse_resume(file)
  ├── pdfplumber/docx2txt → raw text
  └── LLM (task_type="profile") → ResumeData
         │
         ▼
student_profiler.build_profile(resume_data)
  └── LLM (task_type="profile") → StudentProfile (7D)
         │
    ┌────┴────┐
    │         │
    ▼         ▼
ChromaDB     [Store in memory or cache]
store vector
    │
    ▼
[Frontend: View Student Profile]
    │
    ▼
POST /api/matching/analyze (matching.py)
    │
    ▼
matching_engine.match_student_to_jobs(student, top_k=10)
  ├── ChromaDB query → top-K JobProfiles
  ├── Neo4j career paths → career context
  └── LLM (task_type="match") → MatchResult per job
         │
         ▼
[Frontend: View Match Results]
    │
    ▼
POST /api/report/generate (report.py)
    │
    ▼
report_generator.generate_report(student, match)
  ├── Neo4j career path retrieval
  └── LLM (task_type="report") → CareerReport
         │
         ▼
[Frontend: Render Report / Export PDF]
```

### State Management

**No persistent state for students (per PROJECT.md -- no user auth system).**

- Student profile is generated per-session and returned to frontend
- Frontend stores profile in React state (`useState`, `useReducer`, or Zustand)
- Match results stored in frontend state
- Career report stored in frontend state
- Optional: cache last profile/match/report in browser `localStorage` for demo continuity

**Server-side state (minimal):**
- ChromaDB: job vectors (existing, Phase 2) + student vectors (NEW, Phase 7)
- Neo4j: job graph with career paths (existing, Phase 4)

---

## Architectural Patterns

### Pattern 1: LLM-as-Service with Structured Output

**What:** All new services use `llm_service.generate_structured()` for LLM calls instead of raw DeepSeek API calls.

**When to use:** Every new feature that needs LLM reasoning (resume parsing, profiling, matching, report generation).

**Trade-offs:**
- Pros: Consistent retry/timeout/error handling across all features; easy to swap LLM
- Cons: `generate_structured()` always returns JSON (may be limiting for free-form text needs)

**Example:**
```python
from app.services.llm_service import generate_structured

async def parse_resume_with_llm(resume_text: str, client) -> ResumeData:
    prompt = f"""从以下简历文本提取结构化信息...{resume_text}"""
    result = await generate_structured("profile", client, prompt)
    return ResumeData(**result)
```

### Pattern 2: ChromaDB Dual-Collection

**What:** Keep existing `jobs` collection untouched. Create a separate `students` collection for student profile vectors.

**When to use:** When storing both job and student vectors in ChromaDB.

**Trade-offs:**
- Pros: Clean separation; existing Phase 2 code unaffected; easy to query "students similar to me"
- Cons: Two collections to manage; cross-collection queries require two lookups

**Example:**
```python
# Existing (Phase 2) - do not modify
job_collection = chroma_client.get_collection("jobs")

# New (Phase 7) - separate collection
student_collection = chroma_client.get_or_create_collection("students")
```

### Pattern 3: LLM-Chain Pipeline for Reports

**What:** Report generation is a multi-step pipeline: gap analysis -> path planning -> plan generation -> polishing, each step calling LLM.

**When to use:** Report generation that requires synthesis of multiple data sources (profile + match + career path).

**Trade-offs:**
- Pros: Each step is testable; failure isolated to specific step; can cache intermediate results
- Cons: Higher latency (multiple LLM calls); more complex error handling

**Example:**
```python
async def generate_report(student, match) -> CareerReport:
    gaps = await analyze_gaps(student, match)          # LLM call 1
    paths = await plan_career_paths(student, match)    # LLM call 2 + Neo4j
    actions = await generate_actions(gaps, paths)      # LLM call 3
    return await polish_report(gaps, paths, actions)    # LLM call 4
```

### Pattern 4: Service-Router Separation

**What:** Business logic lives in `services/*.py`. FastAPI routing logic lives in `routers/*.py`.

**When to use:** All new features in v1.1.

**Trade-offs:**
- Pros: Testable (can unit test service without HTTP); reusable (service can be called programmatically); clean separation
- Cons: Slight indirection; more files

**Example:**
```python
# router (thin, only HTTP handling)
@router.post("/resume/upload")
async def upload_resume(file: UploadFile):
    return await resume_parser.parse_resume(file)

# service (thick, business logic)
async def parse_resume(file: UploadFile) -> ResumeData:
    text = extract_text(file)
    llm_result = await generate_structured("profile", client, prompt)
    return ResumeData(**llm_result)
```

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **DeepSeek LLM** | Reuse `app/clients/deepseek.py` | Existing client, `generate_structured()` handles all retry/timeout. No new LLM integration needed. |
| **ChromaDB** | Existing `chroma_client` | Job collection `jobs` (existing). Add new `students` collection for student vectors. |
| **Neo4j** | Existing `planer` connection | Existing job graph. No schema changes needed. Career paths queried via Cypher. |
| **PDF Parser** | New dependency: `pdfplumber` | Extract text from PDF resumes. `python-docx` for DOCX. |
| **PDF Export** | Frontend handles | Frontend uses browser `window.print()` or React-PDF. Backend only returns JSON. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `resume_parser` -> `student_profiler` | Function call (`ResumeData` object) | Direct Python object, no serialization needed |
| `student_profiler` -> `matching_engine` | Function call (`StudentProfile` object) | Same process, direct call |
| `matching_engine` -> `report_generator` | Function call (`MatchResult` object) | Same process, direct call |
| Frontend -> Backend | HTTP JSON (FastAPI) | All inter-process communication via REST endpoints |
| Matching Engine -> ChromaDB | Direct SDK call | Existing `chroma_client` |
| Matching Engine -> Neo4j | Cypher query via driver | Existing `planer` driver |
| Report Generator -> Neo4j | Cypher query via driver | Existing `planer` driver |

---

## Build Order (Respecting Dependencies)

### Phase 6 First: Resume Parser

**Why:** All downstream features (profiling, matching, report) depend on parsed resume data. If resume parsing fails, nothing else works.

**Dependencies:** `llm_service.generate_structured()` (existing)

**Deliverable:** `app/services/resume_parser.py`, `app/routers/resume.py`, `app/models/resume_models.py`

---

### Phase 7 Second: Student Profiler

**Why:** Matching engine needs student profile as input. Cannot build matching without profiling.

**Dependencies:** Resume parser (Phase 6 output), `llm_service.generate_structured()` (existing)

**Deliverable:** `app/services/student_profiler.py`, `app/routers/student.py`, `app/models/student_models.py`

---

### Phase 8 Third: Matching Engine

**Why:** Report generation needs match results. Cannot generate useful reports without match data.

**Dependencies:** Student profiler (Phase 7 output), ChromaDB `jobs` collection (existing, Phase 2), Neo4j job graph (existing, Phase 4)

**Deliverable:** `app/services/matching_engine.py`, `app/routers/matching.py`, `app/models/matching_models.py`

---

### Phase 9 Fourth: Report Generator

**Why:** Final output in the pipeline. Depends on all preceding phases.

**Dependencies:** Student profiler (Phase 7), matching engine (Phase 8), Neo4j career paths (existing, Phase 4)

**Deliverable:** `app/services/report_generator.py`, `app/routers/report.py`, `app/models/report_models.py`

---

### Phase 10 Last: React Frontend

**Why:** Frontend simply calls the backend APIs built in Phases 6-9. No backend changes needed for frontend.

**Dependencies:** All 4 backend services (Phases 6-9) must be complete and tested first.

**Deliverable:** React app with components for: ResumeUpload, ProfileRadar, JobGraphViz, MatchResults, ReportView

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 concurrent users | Monolithic FastAPI, single ChromaDB instance, single Neo4j — current architecture is sufficient |
| 100-1,000 concurrent users | Add connection pooling for ChromaDB/Neo4j; consider async ChromaDB client; add Redis for caching match results |
| 1,000+ concurrent users | Split into microservices (resume-service, matching-service, report-service); ChromaDB clustering; Neo4j causal cluster |

### Scaling Priorities for v1.1

1. **First bottleneck:** LLM API rate limits. Mitigation: implement request queuing and caching of repeated analyses.
2. **Second bottleneck:** ChromaDB vector search latency at high concurrency. Mitigation: batch queries, connection pooling.
3. **Third bottleneck:** Neo4j path queries. Mitigation: cache frequent paths, limit path depth.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Calling DeepSeek Directly in Services

**What people do:** Bypass `llm_service.generate_structured()` and call `deepseek_client.chat.completions.create()` directly in each new service.

**Why it's wrong:** Inconsistent retry/timeout handling; duplicated error handling code; harder to swap LLM later.

**Do this instead:** Always use `await generate_structured(task_type, client, prompt)`.

---

### Anti-Pattern 2: Adding New LLM Task Types Without Updating TIMEOUTS

**What people do:** Add new `task_type` values (e.g., "resume", "student") without updating the `TIMEOUTS` dict in `llm_service.py`.

**Why it's wrong:** New task types default to no timeout or wrong timeout. Resume parsing might need 15s like "profile"; report generation might need 45s like "report".

**Do this instead:** Map each new task type to an explicit timeout in `TIMEOUTS`.

```python
TIMEOUTS = {"profile": 15.0, "match": 20.0, "report": 45.0, "resume": 15.0, "student": 15.0}
```

---

### Anti-Pattern 3: Modifying Existing ChromaDB `jobs` Collection

**What people do:** Add student-related data to the existing `jobs` collection, or change the job vector schema.

**Why it's wrong:** Breaks existing Phase 2 vector search that depends on the current schema. Requires re-indexing all 9178 jobs.

**Do this instead:** Create a separate `students` collection for student profile vectors. Keep `jobs` collection unchanged.

---

### Anti-Pattern 4: Single LLM Call for Full Report

**What people do:** Attempt to generate the entire career report in one LLM call.

**Why it's wrong:** Report has multiple sections (goals, gaps, actions, timeline) with different data requirements. Single call leads to hallucinated data and unstructured output.

**Do this instead:** Use multi-step pipeline (gap analysis -> path planning -> action generation -> polishing). Each step is testable and can be refined independently.

---

## Phase-Specific Architecture Notes

### Phase 6 (Resume Parser): File Upload Considerations

- Use `fastapi.UploadFile` for file input
- Validate file extension (.pdf, .docx) before processing
- Maximum file size: 10MB (enforce in router)
- Store raw file temporarily, then delete after text extraction
- Consider: `pdfplumber` for PDF text extraction (Python 3.11+, well-maintained)

### Phase 7 (Student Profiler): Profile Completeness

- Reject profiles with <50% completeness (missing critical fields)
- Score completeness based on filled fields vs. expected fields
- Competitiveness score requires comparison against job data (defer to matching phase)
- Profile completeness score = filled fields / total possible fields

### Phase 8 (Matching Engine): ChromaDB vs Neo4j Responsibilities

- **ChromaDB:** Vector similarity search for top-K relevant jobs based on student skill vector
- **Neo4j:** Career path queries (promotion paths, transition paths) for matched jobs
- **LLM:** Scoring of 4 dimensions based on structured comparison of profile vs job requirements
- Do NOT use Neo4j for vector similarity (wrong tool)
- Do NOT use ChromaDB for career path queries (no relationship traversal)

### Phase 9 (Report Generator): PDF Export Decision

- **Option A (recommended for v1.1):** Frontend handles PDF export via browser `window.print()` or React-PDF library. Backend returns structured JSON.
- **Option B:** Backend generates PDF via WeasyPrint/Jinja2 and returns binary. More complex, adds WeasyPrint dependency.

**Recommendation:** Option A — simpler, less backend complexity, browser printing is sufficient for a competition project.

---

## Sources

- FastAPI: https://fastapi.tiangolo.com/ (existing pattern verified via existing `app/main.py`)
- ChromaDB: existing Phase 2 integration (`scripts/build_job_vector_db_fast.py`)
- Neo4j: existing Phase 4 integration (`app/services/llm_service.py` references, `planer` connection)
- DeepSeek client: existing `app/clients/deepseek.py`
- LLM service: existing `app/services/llm_service.py` with `TIMEOUTS` and `generate_structured()`

**Confidence:**
- FastAPI integration patterns: HIGH (existing code validates these patterns)
- ChromaDB/Neo4j reuse: HIGH (existing collections/connections reused, no modifications)
- LLM service reuse: HIGH (existing `generate_structured()` used as-is)
- New service design: MEDIUM (follows established FastAPI patterns; no external verification)

---

*Architecture research for v1.1 feature integration*
*Researched: 2026-03-30*
