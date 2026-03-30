# Phase 6: Resume Parsing Service - Research

**Researched:** 2026-03-31
**Domain:** PDF/DOCX text extraction + LLM structured extraction
**Confidence:** HIGH

## Summary

Phase 6 implements a resume parsing service: user uploads PDF/DOCX file, system extracts text, feeds to LLM, returns structured resume data aligned with Phase 7's 7-dimension profile. The implementation reuses Phase 5's `generate_structured()` function with a 20-second timeout, leveraging existing DeepSeek client, retry logic, and router patterns. Key risk: `pdfplumber` is not currently installed (python-docx 1.2.0 is present).

**Primary recommendation:** Install `pdfplumber==0.11.9`, create `app/routers/resume.py` following the `llm.py` router pattern, define nested Pydantic `ResumeData` model per D-04, and call `generate_structured("profile", ...)` with a Chinese-resume-optimized prompt.

## User Constraints (from CONTEXT.md)

### Locked Decisions

| ID | Decision |
|----|----------|
| D-01 | One-shot extraction -- feed all raw resume text to LLM via `generate_structured()` in single prompt |
| D-02 | Standalone `/resume/parse` POST in new `app/routers/resume.py`, registered via `app.include_router(resume_router)` |
| D-03 | Resume parsing timeout: 20 seconds |
| D-04 | Nested Pydantic `ResumeData` model mirroring Phase 7's 7-dimension profile |
| D-05 | LLM self-correction with partial fallback: first attempt standard, on failure retry with corrected prompt, if still fails return partial result with `missing_fields` populated |

### Out of Scope

- Multi-file upload (single resume at a time)
- Resume validation against a schema (LLM extracts, frontend validates display)
- Direct database storage (Phase 7 handles persistence)

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STU-01 | Upload PDF/DOCX resume file (10MB limit, pdfplumber for PDF, python-docx for DOCX) | `pdfplumber==0.11.9` needs installation; `python-docx==1.2.0` already installed; FastAPI `UploadFile` handles 10MB via validation |
| STU-02 | Parsed basic info (name, education_level, contact) | `ResumeData.name`, `education_level`, `contact: ContactInfo` in nested model |
| STU-03 | Parsed education history (school, major, GPA, enrollment/graduation years) | `ResumeData.education: List[EducationEntry]` nested model |
| STU-04 | Parsed skills categorized: core / soft / tools | `ResumeData.professional_skills: ProfessionalSkills` with three sub-fields |
| STU-05 | Parsed experience: internship, projects, extracurriculars with dates and descriptions | `ResumeData.experience: ExperienceData` with three sub-fields |

## Standard Stack

### Core Dependencies

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| `pdfplumber` | 0.11.9 | PDF text extraction | **NOT INSTALLED** -- must add to requirements |
| `python-docx` | 1.2.0 | DOCX text extraction | Already installed |
| `FastAPI` | 0.127.1 | Web framework, file upload | Already installed |
| `openai` | 2.24.0 | DeepSeek API client | Already installed |
| `pydantic` | 2.11.7 | Data validation | Already installed |
| `tenacity` | 9.1.2 | Retry logic | Already installed |

**Installation:**
```bash
pip install pdfplumber==0.11.9
```

## Architecture Patterns

### Recommended Project Structure

```
app/
├── routers/
│   ├── __init__.py          # export resume_router
│   ├── llm.py               # existing LLM router
│   ├── health.py            # existing health router
│   └── resume.py            # NEW: /resume/parse endpoint
├── models/
│   ├── __init__.py
│   ├── llm_models.py        # existing LLM models
│   └── resume_models.py     # NEW: ResumeData, EducationEntry, etc.
└── services/
    └── llm_service.py       # existing generate_structured()
```

### Pattern 1: Router with Dependency Injection

**What:** FastAPI router with `Depends()` for client injection, same pattern as `app/routers/llm.py`.

**When to use:** For all business-logic endpoints.

**Example (from llm.py):**
```python
from app.clients.deepseek import get_deepseek_client

router = APIRouter(prefix="/resume", tags=["Resume"])

@router.post("/parse")
async def parse_resume(
    request: ResumeParseRequest,
    client: OpenAI = Depends(get_deepseek_client),
) -> ResumeParseResponse:
    ...
```

### Pattern 2: Nested Pydantic Model for Phase 7 Alignment

**What:** `ResumeData` with nested sub-models matching Phase 7's 7-dimension structure.

**Example (from D-04):**
```python
class ResumeData(BaseModel):
    # Basic info (STU-02)
    name: Optional[str]
    education_level: Optional[str]  # 高中/大专/本科/硕士/博士
    contact: Optional[ContactInfo]  # phone, email

    # Education history (STU-03)
    education: List[EducationEntry]  # school, major, gpa, years

    # Skills categorized (STU-04)
    professional_skills: ProfessionalSkills  # core, soft, tools
    certificates: Certificates  # required, preferred

    # Experience (STU-05)
    experience: ExperienceData  # internship, projects, extracurriculars

    # Phase 7 mapping helpers
    innovation: Optional[float]  # 1-5
    learning: Optional[float]  # 1-5
    stress_resistance: Optional[float]  # 1-5
    communication: Optional[float]  # 1-5

    # Metadata
    missing_fields: List[str] = []
    parse_attempts: int = 1
```

### Pattern 3: Error Handling with Partial Fallback

**What:** On parse failure, retry with reduced prompt, then return partial result.

**Flow (from D-05):**
1. First attempt: standard one-shot prompt
2. On failure: retry with corrected/reduced prompt (focus on missing fields)
3. If still fails: return partial result with `missing_fields` populated

**Why:** Partial results still useful for Phase 7 profiling (completeness score handles missing).

### Pattern 4: File Upload with Size Validation

**What:** FastAPI `UploadFile` with explicit content-length check.

**Example:**
```python
from fastapi import File, UploadFile, HTTPException

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    # proceed with extraction
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF text extraction | Custom PDF parser using PyMuPDF/raw bytes | `pdfplumber` | Handles tables, layouts, encoding detection -- custom code misses edge cases |
| DOCX text extraction | Custom XML parser for .docx | `python-docx` | Battle-tested, handles all Word features |
| LLM JSON output | Custom prompt templating | Existing `generate_structured()` | Already has retry, timeout, JSON parse retry |
| Retry/backoff | Custom retry logic | `tenacity` (already in use) | Already configured in llm_service.py |

## Common Pitfalls

### Pitfall 1: PDF Encoding Errors
**What goes wrong:** Chinese PDF text extracted as garbled characters.
**Why it happens:** PDF encoding mismatch (e.g., CID-keyed fonts in Chinese PDFs).
**How to avoid:** Use `pdfplumber` which handles encoding detection; test with multiple Chinese resumes.
**Warning signs:** `json.JSONDecodeError` on valid-looking content, or LLM returns nonsense.

### Pitfall 2: Large PDF Memory Usage
**What goes wrong:** Very large PDF (scanned image) causes memory spike.
**Why it happens:** pdfplumber loads entire page into memory.
**How to avoid:** Enforce 10MB file size limit at upload time (before extraction).
**Warning signs:** Server memory usage spikes, slow response times.

### Pitfall 3: DOCX List/Table Formatting Loss
**What goes wrong:** Experience bullet points or table data lost in extraction.
**Why it happens:** python-docx extracts paragraph-by-paragraph, no structure preservation.
**How to avoid:** Join paragraphs with newlines, instruct LLM to reconstruct structured data from flat text.
**Warning signs:** LLM reports empty experience section despite visible content in original DOCX.

### Pitfall 4: Timeout Without Partial Result
**What goes wrong:** 20s timeout expires, user gets error instead of partial result.
**Why it happens:** Timeout fires before self-correction retry completes.
**How to avoid:** D-05 partial fallback ensures partial results returned on ultimate failure.

### Pitfall 5: LLM Hallucination on Sparse Resume
**What goes wrong:** LLM invents details when resume text is sparse.
**Why it happens:** One-shot prompt with no schema constraint on output fields.
**How to avoid:** Include explicit instruction in prompt: "If information not found, use null; do not fabricate."

## Code Examples

### File Text Extraction

**PDF (pdfplumber):**
```python
import pdfplumber

def extract_pdf_text(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)
```

**DOCX (python-docx):**
```python
from docx import Document

def extract_docx_text(file_bytes: bytes) -> str:
    doc = Document(BytesIO(file_bytes))
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)
```

### LLM Prompt for Resume Extraction

```python
RESUME_PARSE_PROMPT = """你是一个简历信息提取专家。请从以下简历文本中提取结构化信息。

要求：
1. 只提取文本中明确存在的信息，不要编造
2. 如果某项信息不存在，返回 null，不要虚构
3. 返回JSON格式，包含以下字段：

简历文本：
---
{resume_text}
---

返回JSON格式：
{
  "name": "姓名或null",
  "education_level": "高中/大专/本科/硕士/博士之一或null",
  "contact": {{"phone": "手机号或null", "email": "邮箱或null"}},
  "education": [{{"school": "学校名", "major": "专业", "gpa": "GPA或null", "start_year": "入学年", "end_year": "毕业年"}}],
  "professional_skills": {{"core": ["核心技能列表"], "soft": ["软技能列表"], "tools": ["工具软件列表"]}},
  "certificates": {{"required": ["必要证书列表"], "preferred": ["优先证书列表"]}},
  "experience": {{
    "internship": [{{"company": "公司", "position": "职位", "duration": "时长", "description": "描述"}}],
    "projects": [{{"name": "项目名", "role": "角色", "duration": "时长", "description": "描述"}}],
    "extracurriculars": [{{"activity": "活动名", "role": "角色", "duration": "时长", "description": "描述"}}]
  }},
  "innovation": 1-5评分或null,
  "learning": 1-5评分或null,
  "stress_resistance": 1-5评分或null,
  "communication": 1-5评分或null
}}"""
```

### Reuse generate_structured()

```python
from app.services.llm_service import generate_structured

async def parse_resume_with_llm(resume_text: str, client) -> dict:
    prompt = RESUME_PARSE_PROMPT.format(resume_text=resume_text)
    result = await generate_structured(
        task_type="profile",  # reuse profile timeout (15s) - actually should be 20s per D-03
        client=client,
        prompt=prompt,
        temperature=0.1,
    )
    return result
```

**Note:** `TIMEOUTS["profile"]` is 15s but D-03 requires 20s for resume parsing. The planner should either:
1. Add `"resume": 20.0` to `TIMEOUTS` dict, OR
2. Pass explicit timeout to `generate_structured` (if supported)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Section-based extraction (parse header, then body) | One-shot LLM extraction (feed all text at once) | Phase 6 decision | Simpler pipeline, fewer failure modes |
| Rule-based field extraction | LLM-guided structured extraction | Phase 6 decision | Handles non-standard resume formats naturally |

**Deprecated/outdated:**
- pdfminer.six: Older PDF extraction, slower than pdfplumber
- textract: Heavy external dependency (requires system packages)

## Open Questions

1. **Timeout mismatch**
   - What we know: `TIMEOUTS["profile"]=15s` in llm_service.py, but D-03 specifies 20s for resume parsing
   - What's unclear: Should we add a new `TIMEOUTS["resume"]=20.0` entry or pass explicit timeout?
   - Recommendation: Add `TIMEOUTS["resume"] = 20.0` to llm_service.py; update `generate_structured` to accept optional timeout override

2. **Retry count for self-correction**
   - What we know: D-05 describes a retry-with-corrected-prompt flow
   - What's unclear: How many total attempts (initial + correction)? Standard is 3 max
   - Recommendation: 3 total attempts (1 initial + 2 correction retries), matching existing HTTP retry behavior

3. **Resume model file location**
   - What we know: `app/models/resume_models.py` would hold `ResumeData`
   - What's unclear: Should these models live in `app/models/` or `app/routers/resume.py`?
   - Recommendation: Separate `app/models/resume_models.py` for reusability (Phase 7 imports these)

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `pdfplumber` | STU-01 PDF parsing | NO | -- | Install `pip install pdfplumber==0.11.9` |
| `python-docx` | STU-01 DOCX parsing | YES | 1.2.0 | None needed |
| `FastAPI` | File upload endpoint | YES | 0.127.1 | None needed |
| `openai` (DeepSeek) | LLM extraction | YES | 2.24.0 | None needed |
| `pydantic` | Data validation | YES | 2.11.7 | None needed |

**Missing dependencies with no fallback:**
- `pdfplumber` -- must install before phase can execute

**Missing dependencies with fallback:**
- None

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (inferred from Phase 5 test patterns) |
| Config file | `pytest.ini` or `pyproject.toml` -- verify in Phase 5 artifacts |
| Quick run command | `pytest tests/test_resume.py -x -v` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STU-01 | Upload PDF, receive 200 with parsed data | integration | `pytest tests/test_resume.py::test_parse_pdf_upload -x` | NO - Wave 0 |
| STU-01 | Upload DOCX, receive 200 with parsed data | integration | `pytest tests/test_resume.py::test_parse_docx_upload -x` | NO - Wave 0 |
| STU-01 | Upload >10MB file, receive 413 | unit | `pytest tests/test_resume.py::test_file_size_limit -x` | NO - Wave 0 |
| STU-02 | Response contains name, education_level, contact | unit | `pytest tests/test_resume.py::test_basic_info_fields -x` | NO - Wave 0 |
| STU-03 | Response contains education array with school/major/gpa | unit | `pytest tests/test_resume.py::test_education_fields -x` | NO - Wave 0 |
| STU-04 | Response contains professional_skills with core/soft/tools | unit | `pytest tests/test_resume.py::test_skills_fields -x` | NO - Wave 0 |
| STU-05 | Response contains experience with internship/projects/extracurriculars | unit | `pytest tests/test_resume.py::test_experience_fields -x` | NO - Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_resume.py -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_resume.py` -- covers STU-01~05
- [ ] `tests/conftest.py` -- shared fixtures (sample PDF/DOCX, mock DeepSeek client)
- [ ] `app/models/resume_models.py` -- `ResumeData`, `EducationEntry`, `ProfessionalSkills`, etc.
- [ ] Framework install: already present (pytest detected in existing test structure)

*(If no gaps: "None -- existing test infrastructure covers all phase requirements")*

## Sources

### Primary (HIGH confidence)
- `app/services/llm_service.py` -- `generate_structured()` implementation, `TIMEOUTS` dict, retry logic
- `app/routers/llm.py` -- router pattern, dependency injection, error handling
- `app/clients/deepseek.py` -- `get_deepseek_client()` singleton
- `app/models/llm_models.py` -- Pydantic model patterns
- `pip index versions pdfplumber` -- confirmed version 0.11.9 is latest

### Secondary (MEDIUM confidence)
- `python-docx==1.2.0` API (well-established library)
- FastAPI `UploadFile` pattern (standard FastAPI pattern)

### Tertiary (LOW confidence)
- LLM prompt engineering for Chinese resume extraction (training knowledge, not verified with current DeepSeek model)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- confirmed versions via pip
- Architecture: HIGH -- follows existing Phase 5 patterns exactly
- Pitfalls: MEDIUM -- based on training knowledge of pdfplumber/python-docx edge cases

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (30 days; pdfplumber/DOCX libraries are stable)
