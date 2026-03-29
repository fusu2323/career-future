"""
Career Report API

Endpoints for generating and managing career planning reports.
"""
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from app.services.report_generator import (
    generate_full_report,
    regenerate_section,
    generate_self_awareness_section,
    generate_career_exploration_section,
    generate_career_goal_section,
    generate_career_path_section,
    generate_action_plan_section
)

router = APIRouter(prefix="/report", tags=["Report"])


class ReportGenerateRequest(BaseModel):
    """Report generation request model"""
    student_profile: Dict[str, Any]
    matched_jobs: Optional[List[Dict[str, Any]]] = None
    gap_analysis: Optional[Dict[str, Any]] = None
    target_city: Optional[str] = None
    target_salary: Optional[float] = None


class ReportGenerateResponse(BaseModel):
    """Report generation response model"""
    student_id: str
    student_name: str
    generated_at: str
    sections: List[Dict[str, Any]]
    career_path: List[str]
    action_plan: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class ReportRegenerateRequest(BaseModel):
    """Report section regeneration request model"""
    student_profile: Dict[str, Any]
    section_id: str
    additional_context: Optional[Dict[str, Any]] = None


@router.post("/generate", response_model=ReportGenerateResponse)
async def generate_report(request: ReportGenerateRequest):
    """
    Generate a complete career planning report.

    The report includes:
    - **自我认知分析**: Analysis of student's strengths, weaknesses, interests, and values
    - **职业探索与岗位匹配**: Career exploration and job matching analysis
    - **职业目标设定**: Career goal setting using SMART principles
    - **职业路径规划**: Vertical promotion and horizontal transition paths
    - **行动计划**: Short/medium/long-term action plans with tasks and milestones

    - **student_profile**: Student's complete profile
    - **matched_jobs**: Optional list of matched job recommendations
    - **gap_analysis**: Optional skill gap analysis result
    - **target_city**: Optional target city override
    - **target_salary**: Optional target annual salary override
    """
    try:
        report = generate_full_report(
            student_profile=request.student_profile,
            matched_jobs=request.matched_jobs,
            gap_analysis=request.gap_analysis,
            target_city=request.target_city,
            target_salary=request.target_salary
        )

        # Validate report structure
        if not report.get("sections"):
            raise HTTPException(status_code=500, detail="Report generation failed: empty sections")

        return report

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.post("/regenerate")
async def regenerate_report_section(request: ReportRegenerateRequest):
    """
    Regenerate a specific section of the report.

    Use this endpoint when user wants to:
    - Change target city/salary and regenerate career goals
    - Update matched jobs and regenerate career exploration
    - Modify gap analysis and regenerate action plan

    - **student_profile**: Student's profile
    - **section_id**: Section to regenerate (self_awareness, career_exploration, career_goal, career_path, action_plan)
    - **additional_context**: Optional additional context for regeneration
    """
    try:
        section = regenerate_section(
            student_profile=request.student_profile,
            section_id=request.section_id,
            additional_context=request.additional_context
        )
        return section
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Section regeneration failed: {str(e)}")


@router.get("/sections")
async def get_report_sections():
    """Get available report section definitions"""
    return {
        "sections": [
            {
                "id": "self_awareness",
                "title": "自我认知分析",
                "description": "分析学生的优势、劣势、兴趣和价值观"
            },
            {
                "id": "career_exploration",
                "title": "职业探索与岗位匹配",
                "description": "分析职业方向选择、岗位匹配度和发展空间"
            },
            {
                "id": "career_goal",
                "title": "职业目标设定",
                "description": "基于 SMART 原则设定职业目标"
            },
            {
                "id": "career_path",
                "title": "职业路径规划",
                "description": "设计垂直晋升和横向发展的职业路径"
            },
            {
                "id": "action_plan",
                "title": "行动计划",
                "description": "制定短期、中期、长期的行动计划"
            }
        ]
    }


@router.get("/example")
async def report_example():
    """Get example of report generation request and response"""
    return {
        "example_request": {
            "student_profile": {
                "name": "张三",
                "education": [
                    {
                        "school": "某某大学",
                        "major": "计算机科学与技术",
                        "degree": "本科",
                        "end_date": "2026-06"
                    }
                ],
                "mastered_skills": ["Python", "Java", "MySQL", "Spring Boot"],
                "target_city": "北京",
                "target_salary": 150000,
                "dimensions": {
                    "base": {"score": 80, "details": {}},
                    "skill": {"score": 75, "details": {}},
                    "soft": {"score": 70, "details": {}},
                    "potential": {"score": 85, "details": {}}
                }
            },
            "matched_jobs": [
                {
                    "job_name": "Python 开发工程师",
                    "company": "某某科技",
                    "match_score": 85.5
                }
            ],
            "gap_analysis": {
                "mastered": ["Python", "MySQL"],
                "needs_improvement": ["Redis"],
                "not_learned": ["Docker", "Kubernetes"]
            }
        },
        "example_response": {
            "student_id": "",
            "student_name": "张三",
            "generated_at": "2026-03-02T10:00:00",
            "sections": [
                {
                    "id": "self_awareness",
                    "title": "自我认知分析",
                    "content": "（约 300-400 字的自我认知分析内容）..."
                },
                {
                    "id": "career_exploration",
                    "title": "职业探索与岗位匹配",
                    "content": "（约 300-400 字的职业探索分析）..."
                },
                {
                    "id": "career_goal",
                    "title": "职业目标设定",
                    "content": "（约 250-350 字的职业目标）..."
                },
                {
                    "id": "career_path",
                    "title": "职业路径规划",
                    "content": "",
                    "data": {
                        "vertical_path": ["初级工程师", "中级工程师", "高级工程师", "技术专家"],
                        "horizontal_options": [...],
                        "timeline": {...}
                    }
                },
                {
                    "id": "action_plan",
                    "title": "行动计划",
                    "content": "",
                    "data": {
                        "phases": [...],
                        "recommended_resources": [...]
                    }
                }
            ],
            "career_path": ["初级工程师", "中级工程师", "高级工程师", "技术专家"],
            "action_plan": [...],
            "metadata": {
                "total_words": 1500,
                "matched_jobs_count": 1,
                "target_city": "北京",
                "target_salary": 150000
            }
        }
    }
