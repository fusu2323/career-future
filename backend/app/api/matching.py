"""
Matching and Gap Analysis API

Endpoints for job matching and gap analysis.
"""
from fastapi import APIRouter, HTTPException, Body, Query
from typing import Dict, Any, List

from app.services.gap_analysis import (
    analyze_skill_gap,
    validate_gap_result,
    generate_learning_suggestions,
    full_gap_analysis
)
from app.core.matching import calculate_match, batch_calculate_match

router = APIRouter(prefix="/matching", tags=["Matching"])


@router.post("/gap-analysis")
async def gap_analysis(
    student_skills: List[str] = Body(..., description="学生技能列表"),
    job_required_skills: List[str] = Body(..., description="岗位必需技能"),
    job_preferred_skills: List[str] = Body(default=[], description="岗位优先技能"),
    student_proficiency: Dict[str, str] = Body(default={}, description="学生技能熟练度")
):
    """
    Analyze skill gap between student and job requirements.

    Generates three lists:
    - **mastered**: Skills the student has mastered
    - **needs_improvement**: Skills that need improvement
    - **not_learned**: Skills the student hasn't learned

    Also returns priority actions for closing the gap.
    """
    try:
        result = analyze_skill_gap(
            student_skills,
            job_required_skills,
            job_preferred_skills,
            student_proficiency
        )

        # Validate result
        is_valid, errors = validate_gap_result(result)
        if not is_valid:
            raise HTTPException(status_code=500, detail=f"Validation failed: {errors}")

        # Generate learning suggestions
        result["learning_suggestions"] = generate_learning_suggestions(result)

        # Add summary
        result["summary"] = {
            "total_required": len(job_required_skills),
            "total_preferred": len(job_preferred_skills) if job_preferred_skills else 0,
            "mastered_count": len(result["mastered"]),
            "needs_improvement_count": len(result["needs_improvement"]),
            "not_learned_count": len(result["not_learned"]),
            "match_rate": len(result["mastered"]) / max(len(job_required_skills), 1)
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")


@router.post("/gap-analysis/full")
async def full_gap_analysis_endpoint(
    student_profile: Dict[str, Any] = Body(..., description="学生完整画像"),
    job_profile: Dict[str, Any] = Body(..., description="岗位完整画像")
):
    """
    Perform complete gap analysis using full student and job profiles.

    This endpoint combines skill gap analysis with learning suggestions.
    """
    try:
        result = full_gap_analysis(student_profile, job_profile)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")


@router.post("/calculate")
async def calculate_match_endpoint(
    student_profile: Dict[str, Any] = Body(..., description="学生画像"),
    job_profile: Dict[str, Any] = Body(..., description="岗位画像")
):
    """
    Calculate match score between student and job.

    Returns total_score and dimension scores.
    """
    try:
        result = calculate_match(student_profile, job_profile)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Match calculation failed: {str(e)}")


@router.post("/batch-calculate")
async def batch_calculate_endpoint(
    student_profile: Dict[str, Any] = Body(..., description="学生画像"),
    job_profiles: List[Dict[str, Any]] = Body(..., description="岗位画像列表"),
    top_n: int = Body(default=10, ge=1, le=100, description="返回前 N 个推荐")
):
    """
    Calculate match scores for multiple jobs and return top N recommendations.
    """
    try:
        results = batch_calculate_match(student_profile, job_profiles, top_n)
        return {"results": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch calculation failed: {str(e)}")


@router.get("/gap-analysis/example")
async def gap_analysis_example():
    """
    Get example of gap analysis input and output.
    """
    return {
        "example_request": {
            "student_skills": ["Python", "MySQL", "Java"],
            "job_required_skills": ["Python", "Redis", "Docker"],
            "job_preferred_skills": ["Kubernetes", "AWS"],
            "student_proficiency": {
                "python": "advanced",
                "mysql": "intermediate",
                "java": "basic"
            }
        },
        "example_response": {
            "mastered": ["Python"],
            "needs_improvement": [],
            "not_learned": ["Redis", "Docker", "Kubernetes", "AWS"],
            "priority_actions": [
                {"skill": "Redis", "reason": "岗位必备", "priority": "高", "action_type": "learn"},
                {"skill": "Docker", "reason": "岗位必备", "priority": "高", "action_type": "learn"},
                {"skill": "Kubernetes", "reason": "优先考虑", "priority": "中", "action_type": "learn"},
                {"skill": "AWS", "reason": "加分项", "priority": "低", "action_type": "learn"}
            ],
            "learning_suggestions": [
                {"skill": "Redis", "priority": "高", "action_type": "learn", "suggestion": "建议优先学习 Redis，这是岗位的必备技能", "estimated_hours": 40},
                ...
            ],
            "summary": {
                "total_required_skills": 3,
                "mastered_count": 1,
                "needs_improvement_count": 0,
                "not_learned_count": 4,
                "match_rate": 0.33
            }
        }
    }
