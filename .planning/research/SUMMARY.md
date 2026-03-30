# Project Research Summary

**Project:** 基于AI的大学生职业规划智能体 (AI Career Planning Agent)
**Domain:** AI Career Planning / Human Resources Matching
**Researched:** 2026-03-30
**Confidence:** MEDIUM (WebSearch unavailable; training knowledge with verified codebase patterns)

---

## Executive Summary

v1.1 adds four core features to an existing FastAPI + ChromaDB + Neo4j + DeepSeek stack: **resume parsing** (Phase 6), **student profiling** (Phase 7), **matching engine** (Phase 8), and **career report generation** (Phase 9), culminating in a React frontend (Phase 10). The system follows a strict pipeline: upload resume -> parse to structured data -> generate 7-dimension ability profile -> match against 9178 job profiles across 4 dimensions -> produce actionable career report with gap-prioritized action plans.

Experts build this type of system using a **LLM-as-Service pattern** where DeepSeek handles all structured extraction and synthesis via `generate_structured()`, with per-task timeouts (profile=15s, match=20s, report=45s) and 3x retry logic. The critical architectural insight is **two-stage matching**: ChromaDB vector recall for top-K candidates followed by LLM-driven 4-dimension scoring. For career reports, **RAG is mandatory** -- all career path suggestions must be grounded in actual Neo4j graph data to avoid hallucinated promotions.

Key risks include: PDF text extraction failures (scanned documents, encoding issues), LLM hallucination in gap analysis and report generation, and the Pydantic V1/V2 config mixing that must be resolved before Phase 6. The pipeline is sequential with no parallelization possible -- each phase feeds the next.

---

## Key Findings

### Recommended Stack

**v1.1 additions to validated v1.0 stack** (FastAPI + Uvicorn + ChromaDB + Neo4j + DeepSeek + BGE-m3):

**Core technologies:**
- **pdfplumber + pymupdf** -- PDF text/table extraction for resume parsing; pdfplumber is primary (best table/layout handling), pymupdf is speed fallback
- **python-docx** -- DOCX parsing for Word-format resumes; standard well-maintained library
- **WeasyPrint + Jinja2** -- Server-side HTML-to-PDF generation for career reports; HTML/CSS templates faster to iterate than low-level APIs
- **react-dropzone** -- Professional drag-and-drop file upload for React frontend
- **react-force-graph** -- Interactive 2D/3D career path visualization; node/edge model maps directly to Neo4j graph data
- **Recharts** (existing) -- Radar charts for 7-dimension profile, bar charts for match scores

**What NOT to add:**
- OCR libraries (paddleocr, marker) -- adds significant complexity for marginal gain; most resumes are digital text
- Client-side PDF rendering (@react-pdf/renderer) -- server-side WeasyPrint is simpler for Python/FastAPI stack
- Full LangChain or LlamaIndex -- direct API calls sufficient for structured prompting needs

### Expected Features

**Must have (table stakes):**
- PDF/DOCX resume upload and text extraction -- primary resume formats in China
- LLM-based structured extraction -- convert resume text to ResumeData (name, education, skills, experience)
- 7-dimension student profile generation -- mirrors job profiling pattern (professional_skills, certificates, innovation, learning, stress_resistance, communication, internship)
- 4-dimension matching -- per project spec: 基础要求/职业技能/职业素养/发展潜力
- Gap analysis -- specific skill gaps between student profile and target job requirements
- Career report JSON output -- structured report with action plans and timelines

**Should have (competitive differentiators):**
- Gap-prioritized learning path -- highest-impact gaps first with difficulty/ease weighting
- Neo4j career path visualization -- interactive graph of promotion and transition paths
- Competency radar comparison -- overlapping student vs. target job radar charts
- Top-K job recommendations -- ranked list with per-job match explanations

**Defer (v2+):**
- Competitiveness scoring against job market baseline -- requires statistical baseline from job profiles not yet computed
- Multi-target matching -- match against multiple job types simultaneously
- Learning resource recommendations -- no external course/certificate database exists
- Career path simulation -- "what if I choose X path vs Y" requires extensive Neo4j path validation
- Progress tracking with multiple resume uploads over time -- requires user accounts (out of scope)

### Architecture Approach

v1.1 integrates 4 new services into the existing FastAPI backend following a **Router -> Service -> Model** pattern. Each phase adds one router, one service, and one model file. Business logic lives entirely in services; routers are thin HTTP handlers.

**Major components:**

1. **Resume Parser Service** (Phase 6) -- accepts PDF/DOCX files, extracts raw text via pdfplumber/python-docx, calls LLM via `generate_structured(task_type="profile")` for structured ResumeData output. No new external dependencies beyond document parsers.

2. **Student Profiler Service** (Phase 7) -- takes ResumeData, runs two-step LLM pipeline (extract stats then synthesize into 7-dimension profile). Stores student vectors in NEW ChromaDB `students` collection (existing `jobs` collection is NOT modified). Outputs StudentProfile with completeness and competitiveness scores.

3. **Matching Engine Service** (Phase 8) -- two-stage architecture: ChromaDB vector similarity召回 Top-50 candidates, then LLM-driven 4-dimension scoring for precise ranking. Uses existing Neo4j job graph for career path queries. Outputs MatchResult per job with evidence chains for each dimension score.

4. **Report Generator Service** (Phase 9) -- multi-step LLM pipeline: gap analysis -> career path retrieval from Neo4j -> action plan generation -> polishing. Strictly RAG-driven -- career path suggestions must exist in Neo4j data to avoid hallucination. Returns structured CareerReport JSON; PDF export via WeasyPrint if time permits.

5. **React Frontend** (Phase 10) -- thin client calling backend APIs. Uses react-dropzone for upload, react-force-graph for career path visualization, recharts for radar/bar charts. State managed via useState/useReducer (no Redux needed at this scale).

**Key architectural rules:**
- All LLM calls MUST route through existing `llm_service.generate_structured()` -- no direct DeepSeek API calls
- ChromaDB dual-collection: `jobs` (existing, Phase 2) and `students` (NEW, Phase 7) -- never modify `jobs` schema
- Report generation is a multi-step LLM chain, NOT a single LLM call
- Frontend state is ephemeral -- no user auth, no persistent server-side session state

### Critical Pitfalls

1. **R1: PDF/DOCX text extraction failure** -- Scanned PDFs (image-only), DOCX encoding issues, or large file timeouts cause downstream LLM parsing to receive empty/garbage input. **Avoid by:** validating file type via magic bytes (not extension), enforcing 5-10MB file size limit, setting 10s extraction timeout with partial result fallback, testing on 10+ diverse Chinese resume formats.

2. **R2: LLM hallucination in structured extraction** -- Resume parsing and gap analysis produce fabricated skills, dates, or certifications not present in source text. **Avoid by:** enforcing JSON schema in prompts, Pydantic model validation on output, requiring evidence citation per extracted field, confidence scoring with user confirmation for low-confidence fields.

3. **M2: Vector similarity confused with matching quality** -- ChromaDB returns "similar" jobs (semantic/keyword overlap) but these are not suitable matches for the student's ability profile. **Avoid by:** two-stage architecture (ChromaDB召回 Top-50, then LLM精排 scoring); do NOT use ChromaDB similarity as final match score.

4. **RPT1: Career report hallucination** -- Report generates promotion paths or certifications that do not exist in the 10K job dataset or Neo4j graph. **Avoid by:** mandatory RAG retrieval from Neo4j before LLM synthesis; report validation function checking all mentioned job titles exist in database; explicit "data-supported" vs "LLM-inferred" confidence labels.

5. **TD1: Pydantic V1/V2 config mixing** -- `app/config.py` uses deprecated nested `Config` class (V1 style) alongside `pydantic_settings`, causing warnings and future compatibility risk. **Avoid by:** refactoring to `model_config = SettingsConfigDict(...)` before Phase 6 begins.

---

## Implications for Roadmap

Based on research, the v1.1 phases form a strict sequential pipeline with clear dependencies. No phase can begin until its dependencies are complete.

### Phase 6: Resume Parsing
**Rationale:** Pipeline entry point -- all downstream phases (7, 8, 9, 10) depend on parsed resume data. Must be completed and tested first.

**Delivers:** `app/routers/resume.py`, `app/services/resume_parser.py`, `app/models/resume_models.py` with `POST /api/resume/upload` endpoint accepting PDF/DOCX up to 10MB.

**Addresses:** Resume upload (PDF/DOCX), text extraction, structured ability extraction, basic info extraction, education/experience/skill parsing.

**Avoids:** R1 (file extraction failure) -- implement magic byte validation, 10s timeout, format testing; R2 (LLM hallucination) -- JSON schema enforcement in prompts; F1 API route conflict -- use `/api/v1/resume/upload` prefix.

**Research flags:** Document parsing libraries (pdfplumber, python-docx) are well-established -- no need for `/gsd:research-phase`. Focus research on Chinese resume format diversity during implementation.

---

### Phase 7: Student Profiling
**Rationale:** Matching engine requires student profile as input. Cannot build Phase 8 without Phase 7 output. Must reuse existing `llm_service.generate_structured()` to maintain retry/timeout consistency.

**Delivers:** `app/routers/student.py`, `app/services/student_profiler.py`, `app/models/student_models.py` with `POST /api/student/profile`, `GET /api/student/profile/{id}` endpoints. NEW ChromaDB `students` collection for student profile vectors.

**Addresses:** 7-dimension profile generation (two-step LLM pipeline), completeness score, profile visualization data.

**Avoids:** P1 (profile-data misalignment) -- dimension definitions with evidence requirements, evidence tracking per score; P2 (completeness score misleading) -- separate completeness vs accuracy scoring, key field weighting; P3 (LLM service not reused) -- all calls through `llm_service.generate_structured()`.

**Research flags:** Competitiveness scoring methodology is not yet defined -- may need empirical definition during this phase or defer to v1.2.

---

### Phase 8: Matching Engine
**Rationale:** Report generation requires match results. Cannot build Phase 9 without Phase 8 output. Must implement two-stage architecture (ChromaDB召回 + LLM精排) to avoid M2 pitfall.

**Delivers:** `app/routers/matching.py`, `app/services/matching_engine.py`, `app/models/matching_models.py` with `POST /api/matching/analyze`, `GET /api/matching/top-jobs/{student_id}` endpoints. Reuses existing ChromaDB `jobs` collection and Neo4j job graph.

**Addresses:** 4-dimension matching (基础要求/职业技能/职业素养/发展潜力), gap analysis, top-K job recommendations with explanations.

**Avoids:** M1 (score unexplainable) -- evidence field per dimension with matched/gap skill lists; M2 (similarity vs matching) -- two-stage召回+精排, Top-50 from ChromaDB then LLM scoring; M3 (cold start failure) -- minimum 50% profile completeness threshold, freshman default profiles, exploration mode for sparse data.

**Research flags:** Matching dimension weights are uncalibrated -- start with equal weights, note for empirical tuning. Gap analysis hallucination risk requires active monitoring against job profile data.

---

### Phase 9: Career Report Generation
**Rationale:** Final backend output in the pipeline. Must aggregate data from Phases 6, 7, 8 and query Neo4j career paths. Long task (45s) requires progress notification design.

**Delivers:** `app/routers/report.py`, `app/services/report_generator.py`, `app/models/report_models.py` with `POST /api/report/generate` endpoint. Returns structured CareerReport JSON with goal setting, gap analysis, action plan, and timeline.

**Addresses:** Career path planning (RAG from Neo4j), action plan generation with specific activities/timelines, evaluation metrics for milestones, gap remediation recommendations.

**Avoids:** RPT1 (hallucinated career paths) -- mandatory Neo4j RAG retrieval before LLM synthesis, all mentioned job titles validated against database; RPT2 (generic/inactionable advice) -- forced structured template (current position -> target -> gap list -> specific actions with resources + time -> success metrics); RPT3 (timeout with no progress) -- task-ID pattern with `/report/status/{task_id}` polling, stage progress (gap_analysis=25%, path_planning=50%, etc.).

**Research flags:** WeasyPrint Windows dependency (GTK/VC++ redistributables) -- test PDF generation early in this phase. Report generation timeout (45s) may need extension for complex cases.

---

### Phase 10: React Frontend
**Rationale:** Frontend simply calls the 4 backend services built in Phases 6-9. No backend changes needed for frontend. Must wait for all backend services to be complete and tested.

**Delivers:** React app with: ResumeUpload (react-dropzone), StudentProfileRadar (recharts radar), JobGraphViz (react-force-graph for career paths), MatchResults (bar charts + skill gap lists), ReportView (structured JSON display + PDF export via browser print).

**Addresses:** Full UI for resume upload flow, profile visualization, matching results display, career path graph visualization, report viewing/export.

**Avoids:** F1 (API route mismatch) -- all backend routes use `/api/v1/` prefix, frontend env var `VITE_API_BASE_URL=/api/v1`; F2 (async state mismatch) -- state-driven UI with parsing/ready/error states, upload completes before "generate report" is enabled; F3 (large dataset UI freeze) -- virtual list for >20 matches, animation disabled for charts with >10 data points.

**Research flags:** Well-documented React patterns -- no need for `/gsd:research-phase`. Focus on react-force-graph bundle size and React 18/19 compatibility verification.

---

### Phase Ordering Rationale

- **Sequential pipeline**: Phase 6 -> 7 -> 8 -> 9 with no parallelization possible. Each phase's output feeds the next. Only Phase 10 (frontend) can overlap with backend completion as long as API contracts are stable.

- **LLM service is the backbone**: All phases use `generate_structured()` with appropriate task_type timeouts. New task types ("resume", "student") must be added to TIMEOUTS dict in llm_service.py alongside existing "profile", "match", "report".

- **Config fix before Phase 6**: Pydantic V1/V2 mixing (TD1) must be resolved as a pre Phase-6 task. This is technical debt that affects all phases.

- **Two-phase matching for quality**: Phase 8's two-stage architecture (ChromaDB召回 + LLM精排) is essential to avoid the M2 pitfall of confusing semantic similarity with actual job fit.

- **RAG mandatory for reports**: Phase 9 must retrieve actual career paths from Neo4j before LLM synthesis. Single-LLM-call report generation will produce hallucinated promotions and certifications.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Additions (pdfplumber, python-docx, WeasyPrint, react-dropzone, react-force-graph) are well-established libraries. WebSearch unavailable so versions not web-verified. Existing v1.0 stack (FastAPI, ChromaDB, Neo4j, DeepSeek, BGE-m3) is validated. |
| Features | MEDIUM | Table stakes are clearly defined from project requirements. Differentiators (gap-prioritized paths, Neo4j visualization) are well-grounded. Competitive analysis (智联, 猎聘, BOSS) confirms unique positioning. Some v2+ features deferred appropriately. |
| Architecture | MEDIUM-HIGH | Existing v1.0 patterns are validated in actual codebase. New services follow standard FastAPI patterns. Two-stage matching, LLM-chain reports, dual-collection ChromaDB are all standard patterns with clear rationale. |
| Pitfalls | MEDIUM | Research identifies most critical pitfalls (extraction, hallucination, similarity vs matching). Recovery strategies provided. LOW confidence overall due to WebSearch unavailability -- actual Chinese resume edge cases, WeasyPrint Windows behavior, and react-force-graph large dataset performance need empirical validation. |

**Overall confidence:** MEDIUM

### Gaps to Address

- **Competitiveness scoring methodology:** How to calculate "student competitiveness relative to job market" is not yet specified. Needs empirical definition during Phase 7 or deferral to v1.2.

- **Matching dimension weights:** Whether all 4 dimensions should be weighted equally or differently per job type. Start with equal weights, tune empirically.

- **WeasyPrint Windows dependency:** GTK/VC++ redistributable requirements on Windows need early testing during Phase 9. May require fallback to browser-based PDF export.

- **react-force-graph performance:** Bundle size and rendering performance on large Neo4j result sets (career paths with 50+ nodes) not validated. Test early in Phase 10.

- **Chinese resume format diversity:** PDF parsing tested on limited formats. Need 20+ diverse Chinese resume formats for robust testing before Phase 6 is considered complete.

- **Frontend-backend API contracts:** Phase 10 needs defined Pydantic schemas for all 4 new endpoints. These should be stabilized before Phase 10 begins.

---

## Sources

### Primary (HIGH confidence -- verified in codebase)
- `app/services/llm_service.py` -- LLM service pattern: `generate_structured()` with 3x retry, per-task timeouts, JSON parse retry
- `app/models/llm_models.py` -- Pydantic models: `LLMGenerateRequest` with `task_type`, `LLMGenerateResponse` with `success`, `data`, `error`
- `scripts/build_job_profiles.py` -- two-step LLM pattern: EXTRACTION_PROMPT then SYNTHESIS_PROMPT; token budget with tiktoken; JSON + Neo4j dual storage
- `app/main.py` -- existing FastAPI router registration pattern
- `app/config.py` -- existing config structure (with noted Pydantic V1/V2 mixing issue)

### Secondary (MEDIUM confidence -- training knowledge, not web-verified)
- pdfplumber, pymupdf, python-docx -- PDF/DOCX parsing libraries, well-established but version not web-verified
- WeasyPrint + Jinja2 -- HTML-to-PDF pattern, mature library but Windows dependency concerns
- react-dropzone -- industry standard file upload, React 18/19 compatibility needs verification
- react-force-graph -- strong graph visualization choice but bundle size/performance on large graphs needs validation
- 4-dimension matching: 基础要求/职业技能/职业素养/发展潜力 -- per project specification
- Two-stage matching architecture (ChromaDB召回 + LLM精排) -- standard pattern in recommendation systems

### Tertiary (LOW confidence -- needs validation)
- Competitiveness scoring formula -- needs empirical definition or deferral
- Matching dimension weights -- equal weights starting point, empirical tuning required
- WeasyPrint Windows GTK dependency -- may require fallback approach
- react-force-graph large dataset rendering performance -- needs stress testing
- Chinese resume format diversity coverage -- needs 20+ sample test set

---

*Research completed: 2026-03-30*
*Ready for roadmap: yes*
