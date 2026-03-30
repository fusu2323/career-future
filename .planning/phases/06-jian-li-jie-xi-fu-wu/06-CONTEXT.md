# Phase 6: 简历解析服务 - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

PDF/DOCX resume file upload → LLM extracts structured ability data (basic info, education, skills, experience). Output feeds Phase 7 (student profiling). Phase 10 frontend will call this endpoint.

**Scope:**
- File upload endpoint (PDF/DOCX, 10MB limit)
- Text extraction (pdfplumber for PDF, python-docx for DOCX)
- LLM one-shot extraction of all resume fields
- Return nested data model aligned with Phase 7's 7-dimension profile

**Out of scope:**
- Multi-file upload (single resume at a time)
- Resume validation against a schema (LLM extracts, frontend validates display)
- Direct database storage (Phase 7 handles persistence)

</domain>

<decisions>
## Implementation Decisions

### Parsing strategy
- **D-01:** One-shot extraction — feed all raw resume text to LLM in a single prompt via `generate_structured()`
  - Single LLM call, simpler pipeline
  - Works naturally with existing Phase 5 `generate_structured()` function (takes plain text prompt)
  - No section pre-parsing needed

### Endpoint design
- **D-02:** Standalone `/resume/parse` POST in new `app/routers/resume.py`
  - Registered in `app/main.py` via `app.include_router(resume_router)`
  - Calls LLM via internal HTTP (reuses existing llm service via `app.clients.deepseek`)
  - Separate from `/llm/` prefix — cleaner separation between "business logic" and "LLM abstraction"

### Timeout
- **D-03:** Resume parsing timeout: 20 seconds
  - Reasonable for one-shot extraction of a typical Chinese resume
  - Aligned with Phase 5 `match` timeout (20s) as a comparable extraction task

### Parsed resume data model (nested, Phase 7-aligned)
- **D-04:** Nested Pydantic model structure mirroring Phase 7's 7-dimension profile:
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
      missing_fields: List[str] = []  # populated on partial parse
      parse_attempts: int = 1
  ```
  - Reason: Phase 7's profiler can consume these fields directly with minimal transformation
  - `missing_fields` list enables partial-success error handling

### Error handling — LLM self-correction with partial fallback
- **D-05:** On parse failure:
  1. First attempt: standard one-shot prompt
  2. On failure: retry with a corrected/reduced prompt (focus on missing fields only)
  3. If still fails: return partial result with `missing_fields` populated
  - Partial results still useful for Phase 7 profiling (completeness score handles missing)
  - `parse_attempts` field tracks whether 1 or 2 attempts were needed

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Context
- `.planning/ROADMAP.md` §Phase 6 — 阶段目标、成功标准（STU-01~05）、依赖关系
- `.planning/REQUIREMENTS.md` §STU-01~05 — 简历解析需求细节
- `.planning/PROJECT.md` — DeepSeek已选型（Phase 5决策），技术栈约束

### Prior Phases Integration
- `.planning/phases/05-llm-service/05-CONTEXT.md` — `generate_structured()` 使用方式、超时配置、重试策略
- `app/services/llm_service.py` — `TIMEOUTS = {"profile": 15.0, "match": 20.0, "report": 45.0}`，JSON parse retry 1-2x
- `app/models/llm_models.py` — `LLMGenerateRequest` model with `task_type` Literal
- `app/routers/llm.py` — existing three endpoints pattern (`/llm/profile/generate`等)

### Requirements
- `.planning/REQUIREMENTS.md` — STU-01（文件上传、pdfplumber、python-docx、10MB）直接影响实现细节

</canonical_refs>

<codebase_context>
## Existing Code Insights

### Reusable Assets
- `app/services/llm_service.py` — `generate_structured(task_type, client, prompt, temperature, max_tokens)` — 直接复用，传入 `task_type="profile"` 和拼接的resume文本prompt
- `app/models/llm_models.py` — `LLMGenerateRequest` / `LLMGenerateResponse` — 参考响应格式
- `app/clients/deepseek.py` — `get_deepseek_client()` dependency — resume router需要自己的OpenAI客户端实例

### Established Patterns
- FastAPI router pattern: `router = APIRouter(...)`, `@router.post(...)`, dependency injection via `Depends()`
- Pydantic BaseModel for request/response validation
- `openai.OpenAI` client with `chat.completions.create()`
- `response_format={"type": "json_object"}` for JSON output
- Phase 5 timeout: profile=15s, match=20s, report=45s

### Integration Points
- Input: PDF/DOCX file upload via FastAPI `UploadFile`
- Output: Pydantic `ResumeData` model → JSON
- Calls: Phase 5 LLM service via internal HTTP or direct `generate_structured()` import
- Phase 7 will import `ResumeData` model directly
- Environment: needs `DEEPSEEK_API_KEY` (reuse Settings)

</codebase_context>

<specifics>
## Specific Ideas

- LLM prompt should instruct JSON output in Chinese for consistency
- Consider including examples of good resume text in the prompt for better extraction
- File size enforcement at upload time (before text extraction)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---
*Phase: 06-jian-li-jie-xi-fu-wu*
*Context gathered: 2026-03-31*
