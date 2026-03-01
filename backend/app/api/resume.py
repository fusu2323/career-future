"""
Resume Upload and Parsing API

Endpoints for uploading and parsing resumes (PDF/Word).
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import os

from app.models.resume import ResumeData, ResumeUploadResponse
from app.services.resume_parser import parse_resume_file

router = APIRouter(prefix="/resume", tags=["Resume"])

# Upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "uploads")

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    save_raw: bool = Form(default=True, description="Whether to save raw file")
):
    """
    Upload and parse a resume file.

    - **file**: Resume file in PDF or DOCX format
    - **save_raw**: Whether to save the raw file to disk (default: True)

    Returns parsed resume data including:
    - Personal info (name, phone, email)
    - Education history
    - Skills
    - Certificates
    - Internship experience
    - Project experience
    - Awards
    - Self evaluation
    """
    # Validate file type
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in ['.pdf', '.docx']:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Only .pdf and .docx are supported."
        )

    # Validate file size (max 10MB)
    file_content = await file.read()
    file_size = len(file_content)
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10MB limit"
        )

    if file_size < 1024:
        raise HTTPException(
            status_code=400,
            detail="File size too small, may be corrupted"
        )

    # Determine file type
    file_type = 'pdf' if file_ext == '.pdf' else 'docx'

    try:
        # Parse resume
        parsed_data = parse_resume_file(file_content, file_type)

        # Generate resume ID
        resume_id = str(uuid.uuid4())

        # Save raw file if requested
        if save_raw:
            file_path = os.path.join(UPLOAD_DIR, f"{resume_id}{file_ext}")
            with open(file_path, 'wb') as f:
                f.write(file_content)

        # Create response
        response = ResumeUploadResponse(
            resume_id=resume_id,
            file_name=file.filename,
            file_type=file_type,
            file_size=file_size,
            parsed_data=ResumeData(
                name=parsed_data.get('name'),
                phone=parsed_data.get('phone'),
                email=parsed_data.get('email'),
                education=[
                    {"school": edu.get('school'), "degree": edu.get('degree'),
                     "major": edu.get('major'), "start_date": edu.get('start_date'),
                     "end_date": edu.get('end_date')}
                    for edu in (parsed_data.get('education') or [])
                ] if parsed_data.get('education') else None,
                skills=parsed_data.get('skills'),
                certificates=parsed_data.get('certificates'),
                internships=[
                    {"company": intern.get('company'), "position": intern.get('position'),
                     "start_date": intern.get('start_date'), "end_date": intern.get('end_date'),
                     "description": intern.get('description')}
                    for intern in (parsed_data.get('internships') or [])
                ] if parsed_data.get('internships') else None,
                projects=[
                    {"name": proj.get('name'), "role": proj.get('role'),
                     "start_date": proj.get('start_date'), "end_date": proj.get('end_date'),
                     "description": proj.get('description'),
                     "technologies": proj.get('technologies')}
                    for proj in (parsed_data.get('projects') or [])
                ] if parsed_data.get('projects') else None,
                awards=parsed_data.get('awards'),
                self_evaluation=parsed_data.get('self_evaluation')
            ),
            upload_time=datetime.now().isoformat(),
            status="success"
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")


@router.get("/parse-example")
async def parse_example():
    """
    Get example of parsed resume structure.

    Shows the expected output format for resume parsing.
    """
    return {
        "structure": {
            "name": "张三",
            "phone": "138****5678",
            "email": "zhangsan@email.com",
            "education": [
                {
                    "school": "XX 大学",
                    "degree": "本科",
                    "major": "计算机科学与技术",
                    "start_date": "2021-09",
                    "end_date": "2025-06"
                }
            ],
            "skills": ["Java", "Python", "MySQL", "Spring Boot"],
            "certificates": ["大学英语四级", "软件设计师"],
            "internships": [
                {
                    "company": "XX 科技有限公司",
                    "position": "后端开发实习生",
                    "start_date": "2024-06",
                    "end_date": "2024-09",
                    "description": "负责公司内部管理系统开发..."
                }
            ],
            "projects": [
                {
                    "name": "在线书城系统",
                    "role": "项目负责人",
                    "start_date": "2023-10",
                    "end_date": "2024-01",
                    "description": "基于 Spring Boot 的在线书城系统",
                    "technologies": ["Spring Boot", "Vue3", "MySQL"]
                }
            ],
            "awards": ["校级一等奖学金", "ACM 程序设计竞赛省级二等奖"],
            "self_evaluation": "热爱编程，学习能力强..."
        }
    }
