"""
Resume Parser Service

Parse PDF/Word resumes and extract structured information using GLM-5.
"""
import io
import re
from typing import Dict, Any, List, Optional
from PyPDF2 import PdfReader
from docx import Document
from app.services.glm_client import generate_with_json


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF file

    Args:
        file_bytes: PDF file content in bytes

    Returns:
        Extracted text content
    """
    try:
        pdf_reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from Word (.docx) file

    Args:
        file_bytes: DOCX file content in bytes

    Returns:
        Extracted text content
    """
    try:
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX: {str(e)}")


def clean_text(text: str) -> str:
    """Clean and normalize extracted text"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters that might interfere with parsing
    text = re.sub(r'[^\w\s\u4e00-\u9fff.,;:()\-@/]', '', text)
    return text.strip()


RESUME_PARSE_PROMPT = """
你是一位专业的简历解析专家。请从以下简历文本中提取结构化信息。

请严格按照以下 JSON Schema 返回结果：
{
    "name": "string - 姓名",
    "phone": "string - 电话号码",
    "email": "string - 邮箱地址",
    "education": [
        {
            "school": "string - 学校名称",
            "degree": "string - 学历 (本科/硕士/博士)",
            "major": "string - 专业",
            "start_date": "string - 开始日期 (YYYY-MM 或 YYYY)",
            "end_date": "string - 结束日期 (YYYY-MM 或 YYYY 或 在读)"
        }
    ],
    "skills": [
        "string - 技能列表 (编程语言、工具、框架等)"
    ],
    "certificates": [
        "string - 证书名称"
    ],
    "internships": [
        {
            "company": "string - 公司名称",
            "position": "string - 职位",
            "start_date": "string - 开始日期",
            "end_date": "string - 结束日期",
            "description": "string - 工作描述"
        }
    ],
    "projects": [
        {
            "name": "string - 项目名称",
            "role": "string - 担任角色",
            "start_date": "string - 开始日期",
            "end_date": "string - 结束日期",
            "description": "string - 项目描述",
            "technologies": ["string - 使用的技术"]
        }
    ],
    "awards": [
        "string - 奖项/荣誉"
    ],
    "self_evaluation": "string - 自我评价"
}

注意：
1. 如果某个字段在简历中找不到，返回 null 或空数组
2. 日期格式尽量统一为 YYYY-MM 或 YYYY
3. 技能需要拆分到最细粒度（如"Java, Python, MySQL"应拆分为 ["Java", "Python", "MySQL"]）
4. 保持客观，只提取简历中明确提到的信息

简历文本如下：
"""


def parse_resume_text(text: str) -> Dict[str, Any]:
    """
    Parse resume text and extract structured information using GLM

    Args:
        text: Resume text content

    Returns:
        Structured resume data
    """
    if not text or len(text.strip()) < 50:
        raise ValueError("简历文本内容过少，可能解析失败")

    # Clean text
    cleaned_text = clean_text(text)

    # Call GLM to parse
    try:
        result = generate_with_json(
            prompt=f"{RESUME_PARSE_PROMPT}\n\n{cleaned_text}",
            system_prompt="你是一个专业的简历解析 AI，专注于从简历中提取结构化信息。请始终以合法 JSON 格式返回结果。",
            model="glm-4"
        )
        return result
    except Exception as e:
        raise ValueError(f"GLM 解析失败：{str(e)}")


def parse_resume_file(file_bytes: bytes, file_type: str) -> Dict[str, Any]:
    """
    Parse resume file (PDF or DOCX) and return structured data

    Args:
        file_bytes: File content in bytes
        file_type: File type ('pdf' or 'docx')

    Returns:
        Structured resume data
    """
    # Extract text based on file type
    if file_type.lower() == 'pdf':
        text = extract_text_from_pdf(file_bytes)
    elif file_type.lower() == 'docx':
        text = extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {file_type}. Only 'pdf' and 'docx' are supported.")

    # Parse text with GLM
    parsed_data = parse_resume_text(text)

    # Add raw text for reference
    parsed_data['raw_text'] = text

    return parsed_data
