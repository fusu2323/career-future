"""
Four-Dimensional Matching Algorithm

Calculates match score between student and job position.
Formula: S_total = w1×S_base + w2×S_skill + w3×S_soft + w4×S_potential
"""
from typing import Dict, Any, List, Tuple
from app.core.weights import get_weights_for_job, DEFAULT_WEIGHTS


def calculate_base_score(
    student_base: Dict[str, Any],
    job_requirements: Dict[str, Any]
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate base requirement match score (S_base)

    Factors:
    - Education level match (degree)
    - Major relevance
    - City preference match

    Args:
        student_base: Student's base info (degree, school, city, etc.)
        job_requirements: Job's base requirements

    Returns:
        (score, details)
    """
    score = 0.0
    details = {
        "degree_match": 0,
        "city_match": 0,
        "graduation_match": 0
    }

    # Degree match (0-40 points)
    degree_scores = {
        "专科": 1,
        "大专": 1,
        "本科": 2,
        "学士": 2,
        "硕士": 3,
        "研究生": 3,
        "博士": 4
    }

    student_degree = degree_scores.get(student_base.get("degree", ""), 1)
    required_degree = degree_scores.get(job_requirements.get("min_degree", "本科"), 2)

    if student_degree >= required_degree:
        details["degree_match"] = 40
    else:
        details["degree_match"] = max(0, 40 - (required_degree - student_degree) * 15)

    # City match (0-30 points)
    student_city = student_base.get("target_city", "")
    job_city = job_requirements.get("city", "")

    if student_city and job_city:
        if student_city in job_city or job_city in student_city:
            details["city_match"] = 30
        else:
            # Check province match (simplified)
            details["city_match"] = 15
    else:
        details["city_match"] = 20  # No preference, partial match

    # Graduation year match (0-30 points)
    # Jobs often prefer recent graduates
    student_grad_year_str = student_base.get("graduation_year", "2025")
    student_grad_year = int(student_grad_year_str) if isinstance(student_grad_year_str, str) and student_grad_year_str.isdigit() else (student_grad_year_str if isinstance(student_grad_year_str, int) else 2025)
    job_grad_range = job_requirements.get("graduation_year_range", (2024, 2026))

    if isinstance(job_grad_range, (list, tuple)) and len(job_grad_range) == 2:
        if job_grad_range[0] <= student_grad_year <= job_grad_range[1]:
            details["graduation_match"] = 30
        else:
            # Within 2 years is still acceptable
            diff = min(abs(student_grad_year - job_grad_range[0]),
                      abs(student_grad_year - job_grad_range[1]))
            details["graduation_match"] = max(0, 30 - diff * 10)
    else:
        details["graduation_match"] = 25

    score = details["degree_match"] + details["city_match"] + details["graduation_match"]
    return min(score, 100), details


def calculate_skill_score(
    student_skills: List[str],
    job_required_skills: List[str],
    job_preferred_skills: List[str] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate skill match score (S_skill)

    Factors:
    - Required skills match rate
    - Preferred skills bonus
    - Skill proficiency levels

    Args:
        student_skills: Student's skill list
        job_required_skills: Job's required skills
        job_preferred_skills: Job's preferred (nice-to-have) skills

    Returns:
        (score, details)
    """
    score = 0.0
    details = {
        "required_match_rate": 0,
        "required_match_count": 0,
        "required_total": len(job_required_skills),
        "preferred_match_count": 0,
        "matched_skills": [],
        "missing_skills": []
    }

    if not job_required_skills:
        return 50, details

    # Normalize skills for comparison
    student_skills_lower = [s.lower().strip() for s in student_skills]
    required_skills_lower = [s.lower().strip() for s in job_required_skills]
    preferred_skills_lower = [s.lower().strip() for s in (job_preferred_skills or [])]

    # Count required skill matches
    matched_required = []
    missing_required = []

    for req_skill in required_skills_lower:
        matched = False
        for stu_skill in student_skills_lower:
            if req_skill in stu_skill or stu_skill in req_skill:
                matched = True
                matched_required.append(req_skill)
                break
        if not matched:
            missing_required.append(req_skill)

    details["required_match_count"] = len(matched_required)
    details["matched_skills"] = matched_required
    details["missing_skills"] = missing_required

    # Required skills match rate (0-70 points)
    if details["required_total"] > 0:
        details["required_match_rate"] = len(matched_required) / details["required_total"]
        score += details["required_match_rate"] * 70

    # Preferred skills bonus (0-30 points)
    matched_preferred = 0
    for pref_skill in preferred_skills_lower:
        for stu_skill in student_skills_lower:
            if pref_skill in stu_skill or stu_skill in pref_skill:
                matched_preferred += 1
                break

    details["preferred_match_count"] = matched_preferred
    if preferred_skills_lower:
        score += (matched_preferred / len(preferred_skills_lower)) * 30
    else:
        # If no preferred skills, distribute points to required
        score += (len(matched_required) / max(1, details["required_total"])) * 30

    return min(score, 100), details


def calculate_soft_score(
    student_soft: Dict[str, Any],
    job_soft_requirements: Dict[str, Any]
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate soft skill match score (S_soft)

    Factors:
    - Communication skills
    - Teamwork ability
    - Leadership potential
    - Pressure handling

    Args:
        student_soft: Student's soft skill scores
        job_soft_requirements: Job's soft skill requirements

    Returns:
        (score, details)
    """
    score = 0.0
    details = {}

    # Default soft skill categories
    soft_categories = ["communication", "teamwork", "leadership", "pressure_handling"]

    for category in soft_categories:
        student_val = student_soft.get(category, 50)  # Default to 50 if not provided
        required_val = job_soft_requirements.get(category, 50)

        # Calculate match percentage for this category
        if required_val > 0:
            match_rate = min(student_val / required_val, 1.0)
        else:
            match_rate = 1.0 if student_val >= 50 else student_val / 50

        category_score = match_rate * 25  # Each category worth 25 points
        score += category_score
        details[f"{category}_match"] = round(match_rate * 100, 2)

    return min(score, 100), details


def calculate_potential_score(
    student_potential: Dict[str, Any],
    job_growth_factors: Dict[str, Any]
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate potential match score (S_potential)

    Factors:
    - Learning ability
    - Innovation capability
    - Career growth alignment
    - Adaptability

    Args:
        student_potential: Student's potential indicators
        job_growth_factors: Job's growth potential factors

    Returns:
        (score, details)
    """
    score = 0.0
    details = {}

    # Learning ability (0-30 points)
    learning_score = student_potential.get("learning_ability", 50)
    details["learning_match"] = min(learning_score, 100)
    score += learning_score * 0.3

    # Innovation capability (0-25 points)
    innovation_score = student_potential.get("innovation", 50)
    details["innovation_match"] = min(innovation_score, 100)
    score += innovation_score * 0.25

    # Career growth alignment (0-25 points)
    growth_alignment = student_potential.get("growth_alignment", 50)
    details["growth_alignment"] = min(growth_alignment, 100)
    score += growth_alignment * 0.25

    # Adaptability (0-20 points)
    adaptability = student_potential.get("adaptability", 50)
    details["adaptability_match"] = min(adaptability, 100)
    score += adaptability * 0.2

    return min(score, 100), details


def calculate_match(
    student_profile: Dict[str, Any],
    job_profile: Dict[str, Any],
    weights: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Calculate overall match score between student and job.

    Formula: S_total = w1×S_base + w2×S_skill + w3×S_soft + w4×S_potential

    Args:
        student_profile: Student's complete profile including:
            - dimensions: {base, skill, soft, potential} with scores and details
            - name, email, phone
            - education, skills, etc.
        job_profile: Job's profile including:
            - requirements: {min_degree, city, skills, etc.}
            - category: Job category for weight selection
            - level: Job level for weight adjustment

    Returns:
        Dict with total_score and dimension scores
    """
    # Get dynamic weights based on job type
    if weights is None:
        job_category = job_profile.get("category", "")
        job_level = job_profile.get("level", "")
        weights = get_weights_for_job(job_category, job_level)

    # Extract student data
    student_dimensions = student_profile.get("dimensions", {})
    student_base = {
        "degree": student_profile.get("education", [{}])[0].get("degree") if student_profile.get("education") else None,
        "target_city": student_profile.get("target_city"),
        "graduation_year": student_profile.get("education", [{}])[0].get("end_date", "")[:4] if student_profile.get("education") else None
    }
    student_skills = student_profile.get("mastered_skills", [])
    student_soft = student_dimensions.get("soft", {}).get("details", {})
    student_potential = student_dimensions.get("potential", {}).get("details", {})

    # Extract job requirements
    job_requirements = job_profile.get("requirements", {})
    job_required_skills = job_profile.get("required_skills", [])
    job_preferred_skills = job_profile.get("preferred_skills", [])
    job_soft_requirements = job_profile.get("soft_requirements", {})
    job_growth_factors = job_profile.get("growth_factors", {})

    # Calculate dimension scores
    base_score, base_details = calculate_base_score(student_base, job_requirements)
    skill_score, skill_details = calculate_skill_score(student_skills, job_required_skills, job_preferred_skills)
    soft_score, soft_details = calculate_soft_score(student_soft, job_soft_requirements)
    potential_score, potential_details = calculate_potential_score(student_potential, job_growth_factors)

    # Calculate total score
    total_score = (
        base_score * weights["base"] +
        skill_score * weights["skill"] +
        soft_score * weights["soft"] +
        potential_score * weights["potential"]
    )

    return {
        "total_score": round(total_score, 2),
        "dimensions": {
            "base": round(base_score, 2),
            "skill": round(skill_score, 2),
            "soft": round(soft_score, 2),
            "potential": round(potential_score, 2)
        },
        "details": {
            "base": base_details,
            "skill": skill_details,
            "soft": soft_details,
            "potential": potential_details
        },
        "weights_used": weights
    }


def batch_calculate_match(
    student_profile: Dict[str, Any],
    job_profiles: List[Dict[str, Any]],
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Calculate match scores for multiple jobs and return top N recommendations.

    Args:
        student_profile: Student's profile
        job_profiles: List of job profiles
        top_n: Number of top recommendations to return

    Returns:
        List of match results sorted by total_score (descending)
    """
    results = []

    for job in job_profiles:
        try:
            match_result = calculate_match(student_profile, job)
            results.append({
                "job_id": job.get("id", job.get("job_id", "")),
                "job_name": job.get("name", job.get("job_title", "")),
                "job_category": job.get("category", ""),
                "match_score": match_result["total_score"],
                "dimensions": match_result["dimensions"],
                "details": match_result.get("details", {})
            })
        except Exception as e:
            # Skip jobs that cause errors
            continue

    # Sort by match score (descending)
    results.sort(key=lambda x: x["match_score"], reverse=True)

    return results[:top_n]
