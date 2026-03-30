---
phase: 6
slug: jian-li-jie-xi-fu-wu
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini (verify in existing test structure) |
| **Quick run command** | `pytest tests/test_resume.py -x -v` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_resume.py -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 6-01-01 | 01 | 1 | STU-01 | unit | `pytest tests/test_resume.py::test_file_size_limit -x` | ❌ W0 | ⬜ pending |
| 6-01-02 | 01 | 1 | STU-01 | integration | `pytest tests/test_resume.py::test_parse_pdf_upload -x` | ❌ W0 | ⬜ pending |
| 6-01-03 | 01 | 1 | STU-01 | integration | `pytest tests/test_resume.py::test_parse_docx_upload -x` | ❌ W0 | ⬜ pending |
| 6-02-01 | 01 | 1 | STU-02 | unit | `pytest tests/test_resume.py::test_basic_info_fields -x` | ❌ W0 | ⬜ pending |
| 6-03-01 | 01 | 1 | STU-03 | unit | `pytest tests/test_resume.py::test_education_fields -x` | ❌ W0 | ⬜ pending |
| 6-04-01 | 01 | 1 | STU-04 | unit | `pytest tests/test_resume.py::test_skills_fields -x` | ❌ W0 | ⬜ pending |
| 6-05-01 | 01 | 1 | STU-05 | unit | `pytest tests/test_resume.py::test_experience_fields -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_resume.py` — stubs for STU-01~05
- [ ] `tests/conftest.py` — shared fixtures (sample PDF/DOCX bytes, mock DeepSeek client)
- [ ] `app/models/resume_models.py` — `ResumeData`, `EducationEntry`, `ProfessionalSkills`, etc.
- [ ] Framework install: already present (pytest detected in existing test structure)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| LLM extraction quality (Chinese resume parsing accuracy) | STU-02~05 | Requires real DeepSeek API calls with actual resume examples | Upload 3 sample Chinese resumes, verify parsed fields match expected values |

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
