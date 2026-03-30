# 项目状态

**项目：** 基于AI的大学生职业规划智能体
**当前版本：** v1.1 (started 2026-03-30)
**下一步：** Phase 6 开始执行

---

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-03-30)

**Core value:** 帮助大学生从"盲目规划"走向"精准匹配"——通过AI分析让学生清楚知道自己"能做什么"、"缺什么"、"该怎么补"。
**Current focus:** Phase 6 (简历解析服务)

## Current Position

Phase: 6 of 10 (简历解析服务)
Plan: TBD
Status: Roadmap created, ready to plan
Last activity: 2026-03-30 — v1.1 roadmap created

Progress: [░░░░░░░░░░] 0%

---

## Performance Metrics

**Velocity:**
- Total plans completed: 9 (v1.0)
- Average duration: N/A (v1.0 completed in milestone mode)
- Total execution time: N/A

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 1/1 | Complete | - |
| 2 | 1/1 | Complete | - |
| 3 | 3/3 | Complete | - |
| 4 | 1/1 | Complete | - |
| 5 | 3/3 | Complete | - |

**Recent Trend:**
- v1.0 just completed, no v1.1 data yet

*Updated after each plan completion*

---

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Phase 5: DeepSeek LLM with per-task timeouts (profile=15s, match=20s, report=45s)
- Phase 5: HTTP retry 3x (1s/2s/4s), retry on 5xx/503/429/timeout
- Phase 6: PDF via pdfplumber, DOCX via python-docx, 10MB file limit
- Phase 8: Two-stage matching (ChromaDB召回 Top-50 + LLM精排)
- Phase 9: RAG mandatory — career paths must be retrieved from Neo4j

### Pending Todos

None yet.

### Blockers/Concerns

- Pydantic V1/V2 mixing in app/config.py (Phase 5 tech debt) — must resolve before Phase 6
- WeasyPrint Windows dependency for PDF export — may need fallback approach in Phase 9

---

## Session Continuity

Last session: 2026-03-30
Stopped at: v1.1 roadmap created
Resume file: None
