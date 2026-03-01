"""
Recommendation Service

Generates job recommendations for students based on match scores.
Supports filtering by city, salary, and other criteria.
"""
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json
import time

from app.core.matching import calculate_match, batch_calculate_match
from app.core.weights import get_weights_for_job

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def load_job_profiles(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load job profiles from JSON file.

    Args:
        limit: Optional limit on number of profiles to load

    Returns:
        List of job profiles
    """
    profiles_path = PROJECT_ROOT / "data" / "processed" / "job_profiles.json"
    if not profiles_path.exists():
        return []

    with open(profiles_path, 'r', encoding='utf-8') as f:
        all_profiles = json.load(f)

    if limit:
        return all_profiles[:limit]
    return all_profiles


def filter_jobs(
    jobs: List[Dict[str, Any]],
    city: Optional[str] = None,
    min_salary: Optional[float] = None,
    max_salary: Optional[float] = None,
    job_category: Optional[str] = None,
    industry: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter jobs by criteria.

    Args:
        jobs: List of job profiles
        city: Filter by city (e.g., "北京", "深圳")
        min_salary: Minimum monthly salary
        max_salary: Maximum monthly salary
        job_category: Filter by job category
        industry: Filter by industry

    Returns:
        Filtered list of jobs
    """
    filtered = []

    for job in jobs:
        # City filter (support partial match)
        if city:
            job_city = job.get("city", "")
            if city not in job_city:
                continue

        # Salary filter
        salary = job.get("salary", {})
        salary_min = salary.get("min", 0)
        salary_max = salary.get("max", 0)
        period = salary.get("period", "month")

        # Normalize salary to monthly
        if period == "year":
            salary_min = salary_min / 12
            salary_max = salary_max / 12

        # Filter by min_salary: job's max must be >= user's min requirement
        if min_salary is not None and salary_max < min_salary:
            continue
        # Filter by max_salary: job's min must be <= user's max requirement
        if max_salary is not None and salary_min > max_salary:
            continue

        # Job category filter
        if job_category:
            job_cat = job.get("job_category", "")
            if job_category.lower() not in job_cat.lower():
                continue

        # Industry filter
        if industry:
            job_industry = job.get("industry", "")
            if industry.lower() not in job_industry.lower():
                continue

        filtered.append(job)

    return filtered


def calculate_recommendation_score(
    student_profile: Dict[str, Any],
    job_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate match score between student and job.

    Args:
        student_profile: Student's profile
        job_profile: Job's profile

    Returns:
        Match result with score and details
    """
    try:
        match_result = calculate_match(student_profile, job_profile)

        return {
            "job_id": job_profile.get("id", ""),
            "job_name": job_profile.get("job_name", ""),
            "company": job_profile.get("company", ""),
            "city": job_profile.get("city", ""),
            "job_category": job_profile.get("job_category", ""),
            "salary": job_profile.get("salary", {}),
            "match_score": match_result["total_score"],
            "dimensions": match_result["dimensions"],
            "details": match_result.get("details", {}),
            "weights_used": match_result.get("weights_used", {})
        }
    except Exception as e:
        # Return low score for jobs that cause errors
        return {
            "job_id": job_profile.get("id", ""),
            "job_name": job_profile.get("job_name", ""),
            "company": job_profile.get("company", ""),
            "city": job_profile.get("city", ""),
            "job_category": job_profile.get("job_category", ""),
            "salary": job_profile.get("salary", {}),
            "match_score": 0,
            "error": str(e)
        }


def generate_recommendations(
    student_profile: Dict[str, Any],
    filters: Optional[Dict[str, Any]] = None,
    top_n: int = 10,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    Generate job recommendations for a student.

    Args:
        student_profile: Student's complete profile
        filters: Optional filter criteria:
            - city: Target city
            - min_salary: Minimum salary
            - max_salary: Maximum salary
            - job_category: Job category
            - industry: Industry
        top_n: Number of top recommendations to return
        page: Page number (1-indexed)
        page_size: Results per page

    Returns:
        Recommendation results with pagination
    """
    start_time = time.time()

    # Load all job profiles
    all_jobs = load_job_profiles()

    if not all_jobs:
        return {
            "results": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "processing_time_ms": 0
        }

    # Apply filters
    if filters:
        filtered_jobs = filter_jobs(
            all_jobs,
            city=filters.get("city"),
            min_salary=filters.get("min_salary"),
            max_salary=filters.get("max_salary"),
            job_category=filters.get("job_category"),
            industry=filters.get("industry")
        )
    else:
        filtered_jobs = all_jobs

    # Calculate match scores for all filtered jobs
    results = []
    for job in filtered_jobs:
        match_result = calculate_recommendation_score(student_profile, job)
        results.append(match_result)

    # Sort by match score (descending)
    results.sort(key=lambda x: x["match_score"], reverse=True)

    # Get top N
    top_results = results[:top_n]

    # Apply pagination
    total = len(top_results)
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = top_results[start_idx:end_idx]

    processing_time = time.time() - start_time

    return {
        "results": paginated_results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "processing_time_ms": round(processing_time * 1000, 2),
        "filters_applied": filters or {}
    }


def get_recommendation_with_gap(
    student_profile: Dict[str, Any],
    job_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get recommendation with detailed gap analysis.

    Args:
        student_profile: Student's profile
        job_profile: Job's profile

    Returns:
        Recommendation with gap analysis
    """
    from app.services.gap_analysis import full_gap_analysis

    # Calculate match score
    match_result = calculate_recommendation_score(student_profile, job_profile)

    # Perform gap analysis
    gap_result = full_gap_analysis(student_profile, job_profile)

    return {
        **match_result,
        "gap_analysis": gap_result
    }
