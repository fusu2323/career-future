# Phase 6: 简历解析服务 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 06-jian-li-jie-xi-fu-wu
**Areas discussed:** Parsing strategy, Endpoint design, Parsed resume data model, Error handling

---

## Parsing Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| One-shot extraction | Feed all raw text to LLM in a single prompt via `generate_structured()` | ✓ |
| Section-by-section | Pre-parse sections (education, experience, skills) via text patterns, then LLM processes each separately | |
| Hybrid | Regex pre-extract obvious sections, then one-shot LLM for interpretation | |

**User's choice:** One-shot extraction
**Notes:** Simpler, works naturally with existing `generate_structured()` function, one LLM call

---

## Endpoint Design

| Option | Description | Selected |
|--------|-------------|----------|
| `/resume/parse` in main app | New `app/routers/resume.py`, standalone POST in main FastAPI app, calls LLM via HTTP internally | ✓ |
| `/llm/resume/parse` in llm router | Add as fourth endpoint in existing `llm.py` router, reuse `/llm/` prefix, call `generate_structured()` directly | |

**User's choice:** Standalone `/resume/parse` in main app
**Notes:** Cleaner separation between business logic (resume parsing) and LLM abstraction layer

---

## Parsed Resume Data Model

| Option | Description | Selected |
|--------|-------------|----------|
| Flat model | `BasicInfo`, `EducationList`, `SkillsDict`, `ExperienceList` as top-level simple fields | |
| Nested model (Phase 7-aligned) | Structure mirrors 7-dimension profile: `professional_skills: {core, soft, tools}`, `certificates: {required, preferred}`, etc. | ✓ |

**User's choice:** Nested model aligned with Phase 7
**Notes:** Direct field mapping for Phase 7's profiler, fewer transformations needed downstream

---

## Error Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Complete or nothing | Return error if any required section fails, user retries whole resume | |
| Partial success | Return parsed fields + `missing_fields` list, Phase 7 handles gaps via completeness score | |
| LLM self-correction | Retry with corrected prompt on failure, fall back to partial with `missing_fields` flagged | ✓ |

**User's choice:** LLM self-correction with partial fallback
**Notes:** Best quality outcome — first attempt standard prompt, second attempt corrected/reduced prompt focusing on missing fields, then partial result if still fails

---

## Claude's Discretion

- Exact timeout value: set to 20s (aligned with Phase 5 match timeout as comparable extraction task)
- LLM prompt wording and examples — not specified, open to standard approaches
- File size enforcement approach — upload time vs. after text extraction
- ContactInfo sub-model fields — email format validation, phone format

## Auto-Resolved

None — all decisions made interactively.

---
