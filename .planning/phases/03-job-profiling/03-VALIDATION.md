---
phase: 03
slug: job-profiling
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | tests/phase03/conftest.py (to be created) |
| **Quick run command** | pytest tests/phase03/ -v --tb=short |
| **Full suite command** | pytest tests/phase03/ -v --tb=long -q |
| **Estimated runtime** | ~60 seconds (LLM calls are the bottleneck) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/phase03/ -v --tb=short`
- **After every plan wave:** Full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~30 seconds per LLM call (batch profiling takes time)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | JOB-01 | unit + integration | `pytest tests/phase03/test_profile_generation.py -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase03/__init__.py` — test package init
- [ ] `tests/phase03/conftest.py` — shared fixtures (jobs_cleaned.json mock, DeepSeek mock)
- [ ] `tests/phase03/test_profile_generation.py` — unit tests for profile generation logic
- [ ] `tests/phase03/test_profile_quality.py` — accuracy validation tests

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Profile accuracy >= 90% | JOB-01 | Requires human sampling of generated profiles against raw job data | Sample 10 profiles, compare skills/salary/education against jobs_cleaned.json source records |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
