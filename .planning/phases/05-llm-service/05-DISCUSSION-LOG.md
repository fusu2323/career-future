# Phase 5: LLM服务封装 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 05-llm-service
**Mode:** discuss
**Areas discussed:** API design, Error handling

---

## API Design

| Option | Description | Selected |
|--------|-------------|----------|
| HTTP endpoints (recommended) | FastAPI routes like /llm/profile/generate — better observability, can call from frontend later | ✓ |
| Python service class | LLMService().generate() — less overhead, direct import, simpler for internal calls | |

**User's choice:** HTTP endpoints (recommended)
**Notes:** Better observability, future frontend integration possible

---

## Error Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Retry 3x + exponential backoff | Standard reliability pattern — try 3 times with 1s→2s→4s delay | ✓ |
| Retry 3x + fallback to alternative model | DeepSeek fails → switch to Qwen/other model automatically | |
| Fail-fast with detailed error | No automatic retry — return structured error immediately | |

**User's choice:** Retry 3x + exponential backoff
**Notes:** Standard approach for API reliability

---

## Timeout Configuration

| Option | Description | Selected |
|--------|-------------|----------|
| Profile: 15s, Report: 45s (recommended) | Headroom beyond TECH-01 targets (10s/30s) — handles variance | ✓ |
| Profile: 10s, Report: 30s (per TECH-01) | Strict TECH-01 compliance — no headroom | |
| Profile: 20s, Report: 60s | Generous timeouts — better completion rate, longer wait | |

**User's choice:** Profile: 15s, Report: 45s (recommended)
**Notes:** Provides headroom for network variance

---

## JSON Parse Failures

| Option | Description | Selected |
|--------|-------------|----------|
| Retry 1-2 times on parse error | Standard — attempt again if JSON parse fails | ✓ |
| Return raw text + error flag | Don't retry — return what we got with error flag for caller to handle | |
| Raise exception to caller | Let downstream handle — don't hide parse failures | |

**User's choice:** Retry 1-2 times on parse error
**Notes:** Most parse failures are temporary LLM output formatting issues

---

## Claude's Discretion

- Exact endpoint request/response schema design
- Internal retry implementation details
- Logging and observability approach
- Health check endpoint design

---

## Auto-Resolved

None — no auto mode used.

---

## External Research

None — this phase discusses architecture patterns already well-established in codebase.

