# Feature Research: v1.1 New Features

**Domain:** AI Career Planning - Resume Parsing, Student Profiling, Matching Engine, Report Generation
**Project:** 基于AI的大学生职业规划智能体 (AI Career Planning Agent for University Students)
**Researched:** 2026-03-30
**Research Mode:** Ecosystem (what exists, patterns, expected behavior)
**Confidence:** MEDIUM (WebSearch unavailable; based on verified codebase patterns and training knowledge)

---

## Executive Summary

v1.1 adds four core features to the existing career planning agent: **resume parsing** (Phase 6), **student profiling** (Phase 7), **matching engine** (Phase 8), and **career report generation** (Phase 9). These features form a complete pipeline: upload resume, generate student ability profile, match against job database, produce actionable career report.

The existing codebase provides critical foundations: the LLM service (`generate_structured()` in `app/services/llm_service.py`) with 3x retry, per-task timeouts (profile=15s, match=20s, report=45s), and JSON parse retry; the two-step LLM extraction-synthesis pattern from job profiling (`scripts/build_job_profiles.py`); and the Pydantic request/response models.

**Key insight:** Resume parsing and student profiling should mirror the job profiling pattern -- extract structured data first, then synthesize into a multi-dimension profile. The matching engine should follow a similar LLM-based gap analysis but structured as 4-dimension quantitative comparison. Report generation should aggregate outputs from all previous phases into a single structured document.

---

## Feature Landscape: v1.1 New Features

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or broken.

#### Resume Parsing (Phase 6)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| PDF/DOCX upload | Primary resume formats in China | MEDIUM | Need pdfplumber (PDF) and python-docx (DOCX); various templates create parsing complexity |
| Text extraction | Raw content for LLM processing | MEDIUM | Chinese text encoding, table extraction, section detection |
| Structured ability extraction | Core value -- convert resume to usable data | HIGH | LLM-based; similar to job profile extraction pattern |
| Basic info extraction | Name, education, contact | LOW | Straightforward field mapping |
| Education history parsing | Critical for Chinese job matching | LOW | School, major, GPA if available |
| Skill identification | Core matching input | HIGH | Domain-specific Chinese NLP; overlap with job requirements |
| Experience parsing | Internships, projects, extracurriculars | MEDIUM | Varying formats and depth |

**How it works (expected behavior):**
1. User uploads PDF or DOCX file via FastAPI endpoint
2. File is parsed: pdfplumber extracts PDF text/tables; python-docx extracts DOCX paragraphs/lists
3. Extracted text is cleaned (encoding fixes, whitespace normalization)
4. LLM (DeepSeek) extracts structured data using a Chinese resume extraction prompt
5. Output is validated against a Pydantic model and returned as JSON

**Dependencies:** Phase 6 is the entry point -- all subsequent phases depend on its output.

---

#### Student Ability Profiling (Phase 7)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| 7-dimension profile | Core value proposition --全面的自我认知 | HIGH | Mirrors job profile dimensions: professional_skills, certificates, innovation, learning, stress_resistance, communication, internship |
| Completeness score | Incentive to improve profile | LOW | Percentage of fields populated |
| Competitiveness score | Relative to job market peers | MEDIUM | Requires job profile baseline data |
| Profile visualization | Make abstract abilities concrete | MEDIUM | Radar chart for 7 dimensions |
| Structured JSON output | Downstream consumption | LOW | Pydantic model validation |

**How it works (expected behavior):**
1. Takes structured resume data from Phase 6
2. Two-step LLM pipeline (mirrors job profiling pattern):
   - Step 1: Extract structured stats from resume (skills mentioned, education level, experience breadth)
   - Step 2: Synthesize into 7-dimension profile with scores 1-5
3. Calculate completeness score (what fields are populated / total fields)
4. Calculate competitiveness score (student's profile against job market averages from job profiles)
5. Output to JSON for matching engine consumption

**Dependencies:** Requires Phase 6 (resume parsing) output. Feeds Phase 8 (matching) and Phase 9 (report).

---

#### Matching Engine (Phase 8)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| 4-dimension matching | Project requirement: 基础要求/职业技能/职业素养/发展潜力 | HIGH | Quantitative comparison per dimension |
| Gap analysis | Core value -- "我缺什么" | HIGH | Identify missing skills, cert gaps |
| Match score | Quick suitability indicator | LOW | Percentage or 0-100 score |
| Match explanation | Why match/no-match reasons | MEDIUM | Natural language from LLM |
| Top-K job recommendations | Primary output | LOW | Return ranked list of matching jobs |

**How it works (expected behavior):**
1. Takes student profile (from Phase 7) and job profiles (from Phase 3/4)
2. Per-dimension comparison:
   - **基础要求 (Basic Requirements):** Education match, certificate match, experience years
   - **职业技能 (Professional Skills):** Core skill overlap (Jaccard similarity), tool/framework overlap
   - **职业素养 (Professional Qualities):** Innovation, learning, stress_resistance, communication scores comparison
   - **发展潜力 (Development Potential):** Based on learning ability, internship importance, skill breadth
3. Aggregate weighted score (weights may vary by job type)
4. LLM generates gap analysis: "Missing: Python (required), SQL (preferred), 6-month experience gap"
5. Output: ranked job list with scores and gap explanations

**Dependencies:** Requires Phase 7 (student profile) and job profiles (Phase 3). Feeds Phase 9 (report).

---

#### Career Report Generation (Phase 9)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Career path planning | Answer "where can I go" | HIGH | Based on Neo4j job graph (promotion paths, transition paths) |
| Action plan generation | Answer "how to get there" | HIGH | Specific learning activities, timelines |
| Evaluation metrics | Answer "am I improving" | MEDIUM | Milestones, success criteria |
| Report export | Submission-ready document | LOW | PDF format expected |
| Gap remediation recommendations | Close the "精准" value loop | HIGH | Learning resources, courses, certificates |

**How it works (expected behavior):**
1. Takes: student profile (Phase 7), match results (Phase 8), job graph paths (Phase 4)
2. LLM synthesizes a comprehensive report including:
   - Summary of student profile and match results
   - Career path options (from Neo4j: promotion paths + transition paths)
   - Specific gaps for target jobs
   - Action plan with timeline (short-term: 3 months, mid-term: 6 months, long-term: 1 year)
   - Evaluation metrics for each milestone
3. Report validated against Pydantic model
4. Exported as PDF or returned as structured JSON

**Dependencies:** Requires Phase 7 (student profile), Phase 8 (matching), Phase 4 (Neo4j job graph). Final output for frontend display.

---

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Gap-prioritized learning path | "What to learn first" -- highest impact gaps | HIGH | Weight gaps by job relevance and ease of acquisition |
| Multi-target matching | Match against multiple job types simultaneously | MEDIUM | Show student versatility |
| Career path simulation | "What if I choose X path vs Y" | HIGH | Leverage Neo4j graph for path alternatives |
| Competency radar comparison | Visual overlay: student vs. target job | LOW | Two radar charts overlapped |
| AI-powered report polishing | Professional tone, completeness check | MEDIUM | LLM re-reads and improves own output |

**Why these matter:** The existing Chinese career platforms (智联招聘, 猎聘, BOSS直聘) provide basic matching. Our differentiation is the **图谱可视化 (graph visualization)** of career paths combined with **gap-prioritized action plans**. This aligns directly with the Core Value: "精准匹配" -- helping students know "能做什么"、"缺什么"、"该怎么补".

---

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time resume scanning | "Always current" appeal | Adds latency, complexity, external dependencies | Static parsing with refresh button |
| Manual profile editing | "User control" appeal | Breaks automated pipeline, introduces inconsistency | LLM-based suggestion refinement instead |
| Salary prediction | "Realistic expectations" | No historical salary data for students | Show market range from job data instead |
| Job application integration | "Complete workflow" appeal | Out of scope for competition, adds complexity | Focus on matching and reports |
| Peer comparison/social | "Motivation" appeal | Privacy concerns, complexity, not core value | Competitiveness score vs. job market instead |

---

## Feature Dependencies

Understanding dependencies is critical for phase ordering.

```
PHASE 6: Resume Parsing
        │
        └──► PHASE 7: Student Profiling
                     │
                     ├──► Completeness/Competitiveness Scores (part of Phase 7)
                     │
                     └──► PHASE 8: Matching Engine
                                  │
                                  ├──► Gap Analysis (part of Phase 8)
                                  │
                                  └──► PHASE 9: Career Report
                                               │
                                               └──► PHASE 10: Frontend Display
```

**Dependency Notes:**

- **Phase 6 requires Phase 6:** Resume parsing is the pipeline entry point -- no dependencies on prior phases for its implementation. However, it depends on the LLM service from Phase 5.
- **Phase 7 requires Phase 6:** Student profiling cannot start until resume parsing output is available.
- **Phase 8 requires Phase 7 + Phase 3 (job profiles):** Matching engine needs both student profile and job profiles as inputs.
- **Phase 9 requires Phase 7 + Phase 8 + Phase 4 (Neo4j graph):** Report generation aggregates all previous outputs.
- **Phase 10 (Frontend) requires Phase 6-9:** Frontend displays outputs from all backend phases.

**Conflict note:** None identified among v1.1 features. The pipeline is sequential.

---

## MVP Definition

### Launch With (v1.1)

Minimum viable product -- what's needed to validate the concept end-to-end.

- [ ] **Phase 6: Resume upload + LLM extraction** -- Single PDF/DOCX upload, extract structured data, return JSON. No batch processing.
- [ ] **Phase 7: 7-dimension profile generation** -- Two-step LLM (extract + synthesize), output completeness score. No competitiveness scoring initially.
- [ ] **Phase 8: Basic 4-dimension matching** -- Compare student to job profiles, return top-5 matches with gap list. Single target job initially.
- [ ] **Phase 9: Report generation** -- Aggregate profile + match + gaps into a structured report JSON. PDF export if time permits.

### Add After Validation (v1.2)

Features to add once core is working.

- [ ] **Competitiveness scoring** -- Requires baseline statistics from job profiles (average skills per dimension per job type)
- [ ] **Multi-target matching** -- Match student against multiple job types simultaneously
- [ ] **PDF export with formatting** -- Use reportlab or weasyprint for styled PDF output
- [ ] **Learning resource recommendations** -- Would require external course/certificate data

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Career path simulation** -- "What if I choose X path vs Y" -- needs extensive Neo4j path query validation
- [ ] **Progress tracking** -- Multiple resume uploads over time -- requires user accounts (out of scope)
- [ ] **Salary trajectory prediction** -- Requires market data the project doesn't have

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Resume upload + text extraction | HIGH | MEDIUM | P1 |
| LLM structured extraction from resume | HIGH | HIGH | P1 |
| 7-dimension student profile generation | HIGH | HIGH | P1 |
| Basic 4-dimension matching (single job) | HIGH | MEDIUM | P1 |
| Gap analysis | HIGH | HIGH | P1 |
| Career report JSON output | HIGH | MEDIUM | P1 |
| Completeness scoring | MEDIUM | LOW | P2 |
| Competitiveness scoring | MEDIUM | MEDIUM | P2 |
| Top-K job recommendations | MEDIUM | LOW | P2 |
| PDF export | MEDIUM | MEDIUM | P2 |
| Career path planning (Neo4j-based) | MEDIUM | HIGH | P2 |
| Action plan with timelines | MEDIUM | HIGH | P2 |
| Multi-target matching | MEDIUM | MEDIUM | P3 |
| AI-powered report polishing | LOW | MEDIUM | P3 |
| Learning resource recommendations | LOW | HIGH | P3 |
| Career path simulation | LOW | VERY HIGH | P3 |

**Priority key:**
- P1: Must have for v1.1 launch
- P2: Should have, add when core is stable
- P3: Nice to have, defer to v2

---

## Competitor Feature Analysis

| Feature | 智联招聘AI | 猎聘 | BOSS直聘 | Our Approach (v1.1) |
|---------|-----------|------|----------|---------------------|
| Resume upload | Yes | Yes | Yes | PDF/DOCX via FastAPI |
| Structured extraction | Basic | Advanced | Basic | LLM-based (DeepSeek) |
| 7-dimension profile | No | Some | No | Yes -- mirrors job profiling |
| 4-dimension matching | No | No | No | Yes -- per project spec |
| Gap analysis | Limited | Yes | Limited | Yes -- LLM-generated |
| Career path (graph) | No | No | No | Yes -- Neo4j integration |
| Action plan | No | Yes | No | Yes -- timeline-based |
| Report export | No | Yes | No | PDF via Phase 10 |

**Key insight:** No major Chinese platform combines **LLM-driven resume parsing + gap analysis + Neo4j career path graph + action plan generation** in a single student-facing flow. This is our competitive window.

---

## Phase-Specific Complexity Notes

### Phase 6: Resume Parsing

| Risk | Mitigation |
|------|------------|
| Various PDF templates break parsing | Use pdfplumber with fallback to PyPDF2; test on diverse samples |
| Chinese text encoding issues | Explicit UTF-8 handling; test with WPS/Word/Adobe exports |
| LLM extraction inconsistent | Use extraction prompt pattern from `build_job_profiles.py`; validate with Pydantic |
| File size limits | Set 10MB limit; truncate text if > 8000 tokens |

### Phase 7: Student Profiling

| Risk | Mitigation |
|------|------------|
| Incomplete resume = sparse profile | Calculate and display completeness score; prompt user to add missing info |
| LLM synthesis quality varies | Use two-step pattern (extract then synthesize) as in job profiling |
| Competitiveness scoring needs baseline | Defer to v1.2; use completeness score only for v1.1 |

### Phase 8: Matching Engine

| Risk | Mitigation |
|------|------------|
| 4-dimension weights not calibrated | Start with equal weights; adjust based on job type later |
| Gap analysis hallucinations | Validate against job profile data; use RAG pattern (retrieve relevant job profile context) |
| Performance at scale (9178 jobs) | Pre-compute job profile vectors; use ChromaDB similarity search to shortlist top-50 before detailed matching |

### Phase 9: Report Generation

| Risk | Mitigation |
|------|------------|
| Report too generic | Include student-specific details from Phase 7/8; use few-shot prompting |
| Long generation time (>45s timeout) | Stream output if needed; optimize prompt length |
| Neo4j path queries slow | Pre-compute common paths; cache promotion/transition graphs |

---

## Sources

### Primary (HIGH confidence -- verified in codebase)
- `app/services/llm_service.py` -- Verified LLM service pattern: `generate_structured()` with 3x retry, per-task timeouts (profile=15s, match=20s, report=45s), JSON parse retry
- `app/models/llm_models.py` -- Verified Pydantic models: `LLMGenerateRequest` with `task_type` in ["profile", "match", "report"], `LLMGenerateResponse` with `success`, `data`, `error`
- `scripts/build_job_profiles.py` -- Verified two-step LLM pattern: EXTRACTION_PROMPT then SYNTHESIS_PROMPT; token budget with tiktoken; JSON + Neo4j dual storage

### Secondary (MEDIUM confidence -- training knowledge, not web-verified)
- PDF parsing: `pdfplumber` for text/table extraction, `python-docx` for DOCX
- Chinese resume extraction patterns: Similar to job profile extraction but focused on education, experience, skills
- 4-dimension matching: Basic requirements, professional skills, professional qualities, development potential
- Gap analysis: LLM-generated natural language explanations of mismatches

### Tertiary (LOW confidence -- needs validation)
- Competitiveness scoring methodology: (student score / job market average) or similar ratio-based approach
- Optimal dimension weights for matching: Equal weights initially, empirical tuning needed
- PDF export approach: `reportlab` vs `weasyprint` vs browser-based (playwright)

---

## Gaps to Address

1. **Competitiveness scoring methodology:** How exactly to calculate " competitiveness score" relative to job market is not specified. Needs Phase 7 research or empirical definition.

2. **Matching dimension weights:** Whether all 4 dimensions should be weighted equally or differently per job type. Needs calibration with job profile data.

3. **Learning resource recommendations:** No external course/certificate database exists. May need to use LLM to generate generic recommendations or skip for v1.1.

4. **PDF export implementation:** No PDF generation library is in the current requirements. Needs tech stack decision in Phase 10.

5. **Frontend-backend API contracts:** Phase 10 (frontend) needs defined API schemas for resume upload, profile display, matching results, and report editing.

*Research for: v1.1 new features (Resume Parsing, Student Profiling, Matching Engine, Report Generation)*
*Researched: 2026-03-30*
