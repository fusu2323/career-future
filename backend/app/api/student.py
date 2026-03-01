"""
Student Profile API

Endpoints for student capability profile generation and queries.
"""
import json
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.models.student import StudentProfile, StudentProfileCreate, StudentManualInput
from app.services.student_profile import generate_student_profile, get_profile_json

router = APIRouter(prefix="/student", tags=["Student"])

# In-memory storage for demo (replace with database in production)
student_profiles_db: Dict[str, Dict[str, Any]] = {}
draft_storage: Dict[str, Dict[str, Any]] = {}  # Draft storage for step-by-step form


# Step form models
class Step1BasicInfo(BaseModel):
    """Step 1: Basic Information"""
    name: str = Field(..., description="姓名")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="电话")
    gender: Optional[str] = Field(None, description="性别")
    birth_date: Optional[str] = Field(None, description="出生日期")


class Step2Education(BaseModel):
    """Step 2: Education Information"""
    school: str = Field(..., description="学校")
    major: str = Field(..., description="专业")
    degree: str = Field(..., description="学历")
    graduation_year: int = Field(..., description="毕业年份")
    start_date: Optional[str] = Field(None, description="开始日期")
    gpa: Optional[str] = Field(None, description="GPA")


class Step3Skills(BaseModel):
    """Step 3: Skills"""
    skills: List[str] = Field(default_factory=list, description="技能列表")
    skill_levels: Optional[Dict[str, str]] = Field(None, description="技能水平")


class Step4Experience(BaseModel):
    """Step 4: Experience (Projects + Internships)"""
    projects: Optional[List[Dict[str, Any]]] = Field(None, description="项目经历")
    internships: Optional[List[Dict[str, Any]]] = Field(None, description="实习经历")


class Step5Additional(BaseModel):
    """Step 5: Additional Information"""
    certificates: Optional[List[str]] = Field(None, description="证书")
    awards: Optional[List[str]] = Field(None, description="奖项")
    self_evaluation: Optional[str] = Field(None, description="自我评价")
    target_city: Optional[str] = Field(None, description="意向城市")
    target_salary: Optional[int] = Field(None, description="期望薪资")


class DraftSaveRequest(BaseModel):
    """Request model for saving draft"""
    step: int = Field(..., ge=1, le=5, description="当前步骤")
    data: Dict[str, Any] = Field(..., description="步骤数据")


class DraftSubmitRequest(BaseModel):
    """Request model for submitting final form"""
    draft_id: str = Field(..., description="草稿 ID")


@router.post("/profile", response_model=StudentProfile)
async def generate_profile_from_resume(request: StudentProfileCreate):
    """
    Generate student capability profile from parsed resume data.

    - **resume_id**: Resume ID from upload
    - **resume_data**: Parsed resume data from /api/resume/upload
    - **target_city**: Optional target city
    - **target_salary**: Optional target salary

    Returns student profile with:
    - Four-dimensional capability scores (base, skill, soft, potential)
    - Radar chart data for visualization
    - Completeness score
    - Competitiveness rank
    """
    try:
        # Generate profile
        profile = generate_student_profile(request.resume_data)

        # Store in database
        student_profiles_db[profile.student_id] = {
            "resume_id": request.resume_id,
            "profile": profile.model_dump(),
            "created_at": datetime.now().isoformat()
        }

        return profile

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate profile: {str(e)}")


@router.get("/profile/{student_id}", response_model=StudentProfile)
async def get_profile(student_id: str):
    """
    Get student profile by ID.

    - **student_id**: Student profile ID
    """
    if student_id not in student_profiles_db:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile_data = student_profiles_db[student_id]["profile"]
    return StudentProfile(**profile_data)


@router.post("/profile/manual", response_model=StudentProfile)
async def generate_profile_manual(input: StudentManualInput):
    """
    Generate student profile from manual input (no resume mode).

    - **name**: Student name
    - **email**: Email (optional)
    - **phone**: Phone number (optional)
    - **school**: School name
    - **major**: Major
    - **degree**: Degree (本科/硕士/博士)
    - **graduation_year**: Expected graduation year
    - **skills**: List of skills
    - **projects**: Project experiences
    - **internships**: Internship experiences
    - **certificates**: Certificates
    - **awards**: Awards
    - **target_city**: Target city (optional)
    - **target_salary**: Target salary (optional)
    """
    try:
        # Convert manual input to resume-like format
        resume_data = {
            "name": input.name,
            "email": input.email,
            "phone": input.phone,
            "education": [
                {
                    "school": input.school,
                    "major": input.major,
                    "degree": input.degree,
                    "start_date": f"{input.graduation_year - 4}-09",
                    "end_date": f"{input.graduation_year}-06"
                }
            ],
            "skills": input.skills or [],
            "internships": input.internships or [],
            "projects": input.projects or [],
            "certificates": input.certificates or [],
            "awards": input.awards or [],
            "self_evaluation": ""
        }

        # Generate profile
        profile = generate_student_profile(resume_data)

        # Store in database
        student_profiles_db[profile.student_id] = {
            "resume_id": "manual_input",
            "profile": profile.model_dump(),
            "created_at": datetime.now().isoformat()
        }

        return profile

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate profile: {str(e)}")


@router.get("/profile/{student_id}/radar")
async def get_radar_chart_data(student_id: str):
    """
    Get radar chart data for student profile.

    Returns data formatted for ECharts radar chart.
    """
    if student_id not in student_profiles_db:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile_data = student_profiles_db[student_id]["profile"]
    return {
        "student_id": student_id,
        "radar_chart_data": profile_data.get("radar_chart_data", []),
        "indicators": [
            {"name": "基础能力", "max": 100},
            {"name": "专业技能", "max": 100},
            {"name": "职业素养", "max": 100},
            {"name": "发展潜力", "max": 100},
            {"name": "综合能力", "max": 100}
        ]
    }


@router.get("/profiles")
async def list_profiles(limit: int = 10):
    """
    List all student profiles (for debugging/demo).
    """
    profiles = []
    for student_id, data in list(student_profiles_db.items())[:limit]:
        profile_summary = {
            "student_id": student_id,
            "name": data["profile"].get("name"),
            "total_score": data["profile"].get("total_score"),
            "completeness": data["profile"].get("completeness"),
            "competitiveness_rank": data["profile"].get("competitiveness_rank"),
            "created_at": data.get("created_at")
        }
        profiles.append(profile_summary)

    return {"profiles": profiles, "total": len(profiles)}


@router.delete("/profile/{student_id}")
async def delete_profile(student_id: str):
    """
    Delete a student profile.
    """
    if student_id not in student_profiles_db:
        raise HTTPException(status_code=404, detail="Profile not found")

    del student_profiles_db[student_id]
    return {"message": "Profile deleted successfully", "student_id": student_id}


@router.post("/profile/bulk-generate")
async def bulk_generate_profiles(resume_data_list: list = Body(...)):
    """
    Bulk generate student profiles from multiple resume data.

    Useful for testing or batch processing.
    """
    results = []
    for i, resume_data in enumerate(resume_data_list):
        try:
            profile = generate_student_profile(resume_data)
            student_profiles_db[profile.student_id] = {
                "resume_id": f"bulk_{i}",
                "profile": profile.model_dump(),
                "created_at": datetime.now().isoformat()
            }
            results.append({
                "student_id": profile.student_id,
                "name": profile.name,
                "total_score": profile.total_score,
                "status": "success"
            })
        except Exception as e:
            results.append({
                "index": i,
                "status": "failed",
                "error": str(e)
            })

    return {"results": results, "total": len(results)}


# ========== Step-by-Step Form Endpoints ==========

@router.post("/draft/save")
async def save_draft(request: DraftSaveRequest):
    """
    Save form draft data for step-by-step submission.

    - **step**: Current step number (1-5)
    - **data**: Step data

    Returns draft_id for later submission.
    """
    draft_id = f"draft_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.getpid()}"

    # Initialize draft storage
    draft_storage[draft_id] = {
        "current_step": request.step,
        "steps": {str(request.step): request.data},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    return {
        "draft_id": draft_id,
        "current_step": request.step,
        "message": "Draft saved successfully"
    }


@router.post("/draft/update")
async def update_draft(draft_id: str, request: DraftSaveRequest):
    """
    Update existing draft with new step data.

    - **draft_id**: Draft ID from save_draft
    - **step**: Current step number (1-5)
    - **data**: Step data
    """
    if draft_id not in draft_storage:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft = draft_storage[draft_id]
    draft["steps"][str(request.step)] = request.data
    draft["current_step"] = request.step
    draft["updated_at"] = datetime.now().isoformat()

    return {
        "draft_id": draft_id,
        "current_step": request.step,
        "message": "Draft updated successfully"
    }


@router.get("/draft/{draft_id}")
async def get_draft(draft_id: str):
    """
    Get draft data by ID.

    Returns all saved step data.
    """
    if draft_id not in draft_storage:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft = draft_storage[draft_id]
    return {
        "draft_id": draft_id,
        "current_step": draft["current_step"],
        "steps": draft["steps"],
        "created_at": draft["created_at"],
        "updated_at": draft["updated_at"]
    }


@router.post("/manual-input", response_model=StudentProfile)
async def submit_manual_input(request: DraftSubmitRequest):
    """
    Submit final form data and generate student profile.

    This endpoint collects all step data from draft and generates
    a student profile with the same format as resume parsing.

    - **draft_id**: Draft ID from save_draft/update_draft

    **Step 1**: Basic Info (name, email, phone)
    **Step 2**: Education (school, major, degree, graduation_year)
    **Step 3**: Skills (skills list)
    **Step 4**: Experience (projects, internships)
    **Step 5**: Additional (certificates, awards, self_evaluation, target_city, target_salary)
    """
    if draft_id not in draft_storage:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft = draft_storage[draft_id]
    steps = draft["steps"]

    try:
        # Combine all step data
        step1 = steps.get("1", {})
        step2 = steps.get("2", {})
        step3 = steps.get("3", {})
        step4 = steps.get("4", {})
        step5 = steps.get("5", {})

        # Build resume-like data structure
        resume_data = {
            "name": step1.get("name", "Unknown"),
            "email": step1.get("email"),
            "phone": step1.get("phone"),
            "education": [
                {
                    "school": step2.get("school", "Unknown"),
                    "major": step2.get("major", "Unknown"),
                    "degree": step2.get("degree", "本科"),
                    "start_date": step2.get("start_date", f"{step2.get('graduation_year', 2025) - 4}-09"),
                    "end_date": f"{step2.get('graduation_year', 2025)}-06"
                }
            ],
            "skills": step3.get("skills", []),
            "projects": step4.get("projects", []),
            "internships": step4.get("internships", []),
            "certificates": step5.get("certificates", []),
            "awards": step5.get("awards", []),
            "self_evaluation": step5.get("self_evaluation", ""),
            "target_city": step5.get("target_city"),
            "target_salary": step5.get("target_salary")
        }

        # Generate profile
        profile = generate_student_profile(resume_data)

        # Store in database
        student_profiles_db[profile.student_id] = {
            "resume_id": "manual_input",
            "draft_id": draft_id,
            "profile": profile.model_dump(),
            "created_at": datetime.now().isoformat()
        }

        # Clean up draft
        del draft_storage[draft_id]

        return profile

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate profile: {str(e)}")


@router.delete("/draft/{draft_id}")
async def delete_draft(draft_id: str):
    """
    Delete a draft.
    """
    if draft_id not in draft_storage:
        raise HTTPException(status_code=404, detail="Draft not found")

    del draft_storage[draft_id]
    return {"message": "Draft deleted successfully", "draft_id": draft_id}


@router.get("/form/schema")
async def get_form_schema():
    """
    Get form schema for frontend rendering.

    Returns form structure with fields for each step.
    """
    return {
        "steps": [
            {
                "step": 1,
                "title": "基本信息",
                "fields": [
                    {"name": "name", "type": "text", "label": "姓名", "required": True},
                    {"name": "email", "type": "email", "label": "邮箱", "required": False},
                    {"name": "phone", "type": "tel", "label": "电话", "required": False},
                    {"name": "gender", "type": "select", "label": "性别", "options": ["男", "女"], "required": False},
                    {"name": "birth_date", "type": "date", "label": "出生日期", "required": False}
                ]
            },
            {
                "step": 2,
                "title": "教育信息",
                "fields": [
                    {"name": "school", "type": "text", "label": "学校", "required": True},
                    {"name": "major", "type": "text", "label": "专业", "required": True},
                    {"name": "degree", "type": "select", "label": "学历", "options": ["专科", "本科", "硕士", "博士"], "required": True},
                    {"name": "graduation_year", "type": "number", "label": "毕业年份", "required": True},
                    {"name": "start_date", "type": "date", "label": "入学日期", "required": False},
                    {"name": "gpa", "type": "text", "label": "GPA", "required": False}
                ]
            },
            {
                "step": 3,
                "title": "专业技能",
                "fields": [
                    {"name": "skills", "type": "tags", "label": "技能列表", "placeholder": "输入技能后按回车添加", "required": False},
                    {"name": "skill_levels", "type": "object", "label": "技能水平", "required": False}
                ]
            },
            {
                "step": 4,
                "title": "实践经历",
                "fields": [
                    {"name": "projects", "type": "array", "label": "项目经历", "fields": [
                        {"name": "name", "type": "text", "label": "项目名称"},
                        {"name": "role", "type": "text", "label": "担任角色"},
                        {"name": "start_date", "type": "date", "label": "开始日期"},
                        {"name": "end_date", "type": "date", "label": "结束日期"},
                        {"name": "description", "type": "textarea", "label": "项目描述"},
                        {"name": "technologies", "type": "tags", "label": "使用技术"}
                    ]},
                    {"name": "internships", "type": "array", "label": "实习经历", "fields": [
                        {"name": "company", "type": "text", "label": "公司名称"},
                        {"name": "position", "type": "text", "label": "职位"},
                        {"name": "start_date", "type": "date", "label": "开始日期"},
                        {"name": "end_date", "type": "date", "label": "结束日期"},
                        {"name": "description", "type": "textarea", "label": "工作描述"}
                    ]}
                ]
            },
            {
                "step": 5,
                "title": "其他信息",
                "fields": [
                    {"name": "certificates", "type": "tags", "label": "证书", "required": False},
                    {"name": "awards", "type": "tags", "label": "奖项", "required": False},
                    {"name": "self_evaluation", "type": "textarea", "label": "自我评价", "required": False},
                    {"name": "target_city", "type": "text", "label": "意向城市", "required": False},
                    {"name": "target_salary", "type": "number", "label": "期望薪资", "required": False}
                ]
            }
        ]
    }
