"""
Matching and Gap Analysis API

Endpoints for job matching and gap analysis.
"""
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from app.services.gap_analysis import (
    analyze_skill_gap,
    validate_gap_result,
    generate_learning_suggestions,
    full_gap_analysis
)
from app.core.matching import calculate_match, batch_calculate_match
from app.services.recommendation import (
    generate_recommendations,
    get_recommendation_with_gap
)

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


class RecommendationRequest(BaseModel):
    """Recommendation request model"""
    student_profile: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None
    top_n: int = 10
    page: int = 1
    page_size: int = 20


class RecommendationResponse(BaseModel):
    """Recommendation response model"""
    results: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    processing_time_ms: float


@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Get job recommendations for a student.

    - **student_profile**: Student's complete profile
    - **filters**: Optional filter criteria:
        - city: Target city (e.g., "北京", "深圳")
        - min_salary: Minimum monthly salary
        - max_salary: Maximum monthly salary
        - job_category: Job category
        - industry: Industry
    - **top_n**: Number of top recommendations to return (default: 10)
    - **page**: Page number for pagination (default: 1)
    - **page_size**: Results per page (default: 20)

    Returns job recommendations sorted by match score (descending).
    """
    try:
        result = generate_recommendations(
            student_profile=request.student_profile,
            filters=request.filters,
            top_n=request.top_n,
            page=request.page,
            page_size=request.page_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


@router.get("/recommend/example")
async def recommend_example():
    """
    Get example of recommendation API.
    """
    return {
        "example_request": {
            "student_profile": {
                "name": "张三",
                "education": [{"degree": "本科", "end_date": "2026-06"}],
                "target_city": "北京",
                "mastered_skills": ["Python", "Java", "MySQL"],
                "dimensions": {
                    "base": {"score": 80, "details": {}},
                    "skill": {"score": 75, "details": {}},
                    "soft": {"score": 70, "details": {}},
                    "potential": {"score": 85, "details": {}}
                }
            },
            "filters": {"city": "北京", "job_category": "互联网"},
            "top_n": 10,
            "page": 1,
            "page_size": 20
        },
        "example_response": {
            "results": [
                {
                    "job_id": "1",
                    "job_name": "Python 开发工程师",
                    "company": "某某科技",
                    "city": "北京",
                    "match_score": 85.5,
                    "dimensions": {
                        "base": 80,
                        "skill": 85,
                        "soft": 75,
                        "potential": 90
                    }
                }
            ],
            "total": 10,
            "page": 1,
            "page_size": 20,
            "total_pages": 1,
            "processing_time_ms": 150.5
        }
    }
