"""Resume parsing router — /resume/parse endpoint for STU-01 through STU-05."""
from io import BytesIO
from typing import Annotated

import pdfplumber
from docx import Document
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from openai import OpenAI

from app.clients.deepseek import get_deepseek_client
from app.models.resume_models import ResumeData
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

    Implementation: Plan 06-03 (self-correction logic, actual LLM call)
    """
    # File size check
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    # Determine file type and extract text
    content = await file.read()
    if file.content_type == "application/pdf":
        resume_text = extract_pdf_text(content)
    elif file.content_type in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"):
        resume_text = extract_docx_text(content)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type (only PDF/DOCX accepted)")

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from file")

    # STUB: Return empty ResumeData — Plan 06-03 implements the full LLM call
    return ResumeData()
