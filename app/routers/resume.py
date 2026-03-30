"""Resume parsing router — /resume/parse endpoint for STU-01 through STU-05."""
from io import BytesIO
from typing import Optional

import pdfplumber
from docx import Document
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from openai import OpenAI

from app.clients.deepseek import get_deepseek_client
from app.models.resume_models import (
    ResumeData,
    ContactInfo,
    EducationEntry,
    ProfessionalSkills,
    Certificates,
    ExperienceEntry,
    ExperienceData,
)
from app.services.llm_service import generate_structured


router = APIRouter(prefix="/resume", tags=["Resume"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# LLM prompt for one-shot resume extraction (Chinese)
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
{{
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
  "communication": 1-5评分或null,
  "missing_fields": [],
  "parse_attempts": 1
}}"""

# Self-correction prompt (used on second attempt)
RESUME_PARSE_PROMPT_CORRECTED = """你是一个简历信息提取专家。上一次提取失败或字段不完整，请重新提取。

请从以下简历文本中提取结构化信息。
要求：
1. 只提取文本中明确存在的信息，不要编造
2. 如果某项信息不存在，返回 null，不要虚构
3. 特别关注上次缺失的字段：{missing_fields}

简历文本：
---
{resume_text}
---

返回JSON格式（只返回JSON，不要其他内容）：
{{
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
  "communication": 1-5评分或null,
  "missing_fields": [],
  "parse_attempts": 2
}}"""


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    text_parts = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def extract_docx_text(file_bytes: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    doc = Document(BytesIO(file_bytes))
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)


def _identify_missing_fields(raw_result: dict) -> list[str]:
    """Identify which expected fields are missing from LLM result."""
    missing = []
    if not raw_result.get("name"):
        missing.append("name")
    if not raw_result.get("education_level"):
        missing.append("education_level")
    if not raw_result.get("contact") or not raw_result["contact"].get("phone"):
        missing.append("contact")
    if not raw_result.get("education"):
        missing.append("education")
    if not raw_result.get("professional_skills") or not raw_result["professional_skills"].get("core"):
        missing.append("professional_skills.core")
    if not raw_result.get("experience"):
        missing.append("experience")
    return missing


def _identify_missing_fields_from_error(error: str, prompt: str) -> list[str]:
    """Infer which fields failed based on error message and prompt context."""
    # Heuristic: if we got a JSON parse error, likely structural mismatch
    # Return common problematic fields as a fallback
    return ["education", "professional_skills", "experience"]


def _build_partial_resume(
    raw_result: dict, parse_attempts: int, missing_fields: list[str]
) -> ResumeData:
    """Build a partial ResumeData from raw LLM result on failure."""
    # Safely extract sub-models
    contact: Optional[ContactInfo] = None
    if raw_result.get("contact"):
        try:
            contact = ContactInfo(**raw_result["contact"])
        except Exception:
            contact = None

    education = []
    for e in raw_result.get("education", []):
        try:
            education.append(EducationEntry(**e))
        except Exception:
            pass

    professional_skills = ProfessionalSkills()
    if raw_result.get("professional_skills"):
        try:
            professional_skills = ProfessionalSkills(**raw_result["professional_skills"])
        except Exception:
            pass

    certificates = Certificates()
    if raw_result.get("certificates"):
        try:
            certificates = Certificates(**raw_result["certificates"])
        except Exception:
            pass

    experience = ExperienceData()
    if raw_result.get("experience"):
        try:
            exp_dict = raw_result["experience"]
            experience = ExperienceData(
                internship=[ExperienceEntry(**e) for e in exp_dict.get("internship", [])],
                projects=[ExperienceEntry(**e) for e in exp_dict.get("projects", [])],
                extracurriculars=[ExperienceEntry(**e) for e in exp_dict.get("extracurriculars", [])],
            )
        except Exception:
            pass

    return ResumeData(
        name=raw_result.get("name"),
        education_level=raw_result.get("education_level"),
        contact=contact,
        education=education,
        professional_skills=professional_skills,
        certificates=certificates,
        experience=experience,
        innovation=raw_result.get("innovation"),
        learning=raw_result.get("learning"),
        stress_resistance=raw_result.get("stress_resistance"),
        communication=raw_result.get("communication"),
        missing_fields=missing_fields,
        parse_attempts=parse_attempts,
    )


@router.post("/parse", response_model=ResumeData)
async def parse_resume(
    file: UploadFile = File(...),
    client: OpenAI = Depends(get_deepseek_client),
) -> ResumeData:
    """
    Parse a resume file (PDF or DOCX) and extract structured data.

    STU-01: Accepts PDF/DOCX up to 10MB
    STU-02: Extracts basic info (name, education_level, contact)
    STU-03: Extracts education history
    STU-04: Extracts categorized skills
    STU-05: Extracts experience data

    Self-correction: On failure, retries once with corrected prompt focusing on missing fields.
    Ultimate failure returns partial result with missing_fields populated (D-05).
    """
    # File size check
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    # Determine file type and extract text
    content = await file.read()
    if file.content_type == "application/pdf":
        resume_text = extract_pdf_text(content)
    elif file.content_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ):
        resume_text = extract_docx_text(content)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type (only PDF/DOCX accepted)")

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from file")

    # Build the prompt
    prompt = RESUME_PARSE_PROMPT.format(resume_text=resume_text)

    # First attempt
    parse_attempts = 1
    missing_fields: list[str] = []
    last_error: Optional[str] = None
    raw_result: Optional[dict] = None

    try:
        raw_result = await generate_structured(
            task_type="profile",
            client=client,
            prompt=prompt,
            temperature=0.1,
            timeout_override=20.0,  # D-03: 20s timeout for resume parsing
        )
    except Exception as e:
        last_error = str(e)
        raw_result = None

    # Self-correction: retry with corrected prompt if first attempt failed
    if raw_result is None and last_error is not None:
        parse_attempts = 2
        # Identify missing fields from error context
        missing_fields = _identify_missing_fields_from_error(last_error, prompt)
        corrected_prompt = RESUME_PARSE_PROMPT_CORRECTED.format(
            resume_text=resume_text,
            missing_fields=", ".join(missing_fields) if missing_fields else "所有字段",
        )
        try:
            raw_result = await generate_structured(
                task_type="profile",
                client=client,
                prompt=corrected_prompt,
                temperature=0.1,
                timeout_override=20.0,
            )
        except Exception as e:
            last_error = str(e)
            raw_result = None

    # Build ResumeData from LLM result (or partial result on ultimate failure)
    if raw_result is not None:
        # Populate parse_attempts and missing_fields
        raw_result["parse_attempts"] = parse_attempts
        if missing_fields:
            raw_result["missing_fields"] = missing_fields
        else:
            raw_result["missing_fields"] = _identify_missing_fields(raw_result)

        try:
            return ResumeData(**raw_result)
        except Exception:
            # LLM returned partial/invalid structure — return what we can
            partial = _build_partial_resume(raw_result, parse_attempts, missing_fields)
            return partial

    # Ultimate failure: return partial result
    partial = _build_partial_resume({}, parse_attempts, missing_fields or ["all"])
    partial.missing_fields = missing_fields or ["all"]
    return partial
