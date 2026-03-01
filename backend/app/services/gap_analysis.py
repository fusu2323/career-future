"""
Gap Analysis Service

Analyzes the gap between student skills and job requirements.
Generates "mastered", "needs_improvement", "not_learned" lists.
"""
from typing import Dict, Any, List, Tuple, Set
from collections import defaultdict


# Skill proficiency levels
PROFICIENCY_LEVELS = {
    "expert": 4,      # 专家水平
    "advanced": 3,    # 高级
    "intermediate": 2,  # 中级
    "basic": 1,       # 基础
    "novice": 0       # 入门/未掌握
}

# Skill priority keywords
PRIORITY_KEYWORDS = {
    "high": ["必备", "必须", "required", "must", "core", "核心"],
    "medium": ["优先", "prefer", "important", "主要"],
    "low": ["加分", "nice to have", "bonus", "了解"]
}


def normalize_skill_name(skill: str) -> str:
    """
    Normalize skill name for comparison.

    Args:
        skill: Skill name

    Returns:
        Normalized skill name (lowercase, stripped)
    """
    return skill.lower().strip()


def check_skill_match(student_skill: str, required_skill: str) -> bool:
    """
    Check if a student skill matches a required skill.

    Args:
        student_skill: Student's skill
        required_skill: Required skill from job

    Returns:
        True if skills match
    """
    student_norm = normalize_skill_name(student_skill)
    required_norm = normalize_skill_name(required_skill)

    # Exact match
    if student_norm == required_norm:
        return True

    # Partial match (one contains the other)
    if student_norm in required_norm or required_norm in student_norm:
        return True

    # Common aliases
    aliases = {
        "js": "javascript",
        "py": "python",
        "springboot": "spring boot",
        "spring cloud": "springcloud",
        "mysql": "sql",
        "postgresql": "sql",
        "postgres": "sql",
    }

    student_alias = aliases.get(student_norm, student_norm)
    required_alias = aliases.get(required_norm, required_norm)

    return student_alias == required_alias or student_norm in required_alias or required_norm in student_alias


def determine_skill_priority(skill: str, job_required_skills: List[str],
                            job_preferred_skills: List[str] = None) -> str:
    """
    Determine the priority level of a skill.

    Args:
        skill: Skill name
        job_required_skills: Job's required skills
        job_preferred_skills: Job's preferred skills

    Returns:
        "high", "medium", or "low"
    """
    skill_norm = normalize_skill_name(skill)

    # Check if in required skills (high priority)
    for req_skill in job_required_skills:
        if check_skill_match(skill, req_skill):
            return "high"

    # Check if in preferred skills (medium priority)
    if job_preferred_skills:
        for pref_skill in job_preferred_skills:
            if check_skill_match(skill, pref_skill):
                return "medium"

    return "low"


def analyze_skill_gap(
    student_skills: List[str],
    job_required_skills: List[str],
    job_preferred_skills: List[str] = None,
    student_proficiency: Dict[str, str] = None
) -> Dict[str, Any]:
    """
    Analyze skill gap between student and job.

    Args:
        student_skills: Student's skill list
        job_required_skills: Job's required skills
        job_preferred_skills: Job's preferred skills
        student_proficiency: Student's proficiency level for each skill

    Returns:
        Gap analysis result with mastered, needs_improvement, not_learned
    """
    result = {
        "mastered": [],           # 已掌握
        "needs_improvement": [],  # 需强化
        "not_learned": [],        # 未掌握
        "priority_actions": []    # 优先行动项
    }

    if student_proficiency is None:
        student_proficiency = {}

    # Track matched required skills
    matched_required: Set[str] = set()
    unmatched_required: Set[str] = set()

    # Step 1: Categorize required skills
    for req_skill in job_required_skills:
        matched = False
        for stu_skill in student_skills:
            if check_skill_match(stu_skill, req_skill):
                matched = True
                matched_required.add(req_skill)

                # Check proficiency level
                proficiency = student_proficiency.get(normalize_skill_name(stu_skill), "intermediate")
                if proficiency in ["expert", "advanced"]:
                    result["mastered"].append(req_skill)
                else:
                    result["needs_improvement"].append(req_skill)
                break

        if not matched:
            unmatched_required.add(req_skill)

    # Step 2: Add unmatched required skills to not_learned
    for req_skill in unmatched_required:
        result["not_learned"].append(req_skill)

    # Step 3: Handle preferred skills
    if job_preferred_skills:
        for pref_skill in job_preferred_skills:
            # Skip if already categorized as required
            if pref_skill in matched_required or pref_skill in unmatched_required:
                continue

            matched = False
            for stu_skill in student_skills:
                if check_skill_match(stu_skill, pref_skill):
                    matched = True
                    proficiency = student_proficiency.get(normalize_skill_name(stu_skill), "intermediate")
                    if proficiency in ["expert", "advanced"]:
                        if pref_skill not in result["mastered"]:
                            result["mastered"].append(pref_skill)
                    else:
                        if pref_skill not in result["needs_improvement"]:
                            result["needs_improvement"].append(pref_skill)
                    break

            if not matched:
                # Preferred skills not learned go to a separate lower priority
                if pref_skill not in result["not_learned"]:
                    result["not_learned"].append(pref_skill)

    # Step 4: Generate priority actions
    for skill in result["needs_improvement"]:
        priority = determine_skill_priority(skill, job_required_skills, job_preferred_skills)
        reason = "岗位必备" if priority == "high" else ("优先考虑" if priority == "medium" else "加分项")
        result["priority_actions"].append({
            "skill": skill,
            "reason": reason,
            "priority": priority,
            "action_type": "strengthen"
        })

    for skill in result["not_learned"]:
        priority = determine_skill_priority(skill, job_required_skills, job_preferred_skills)
        reason = "岗位必备" if priority == "high" else ("优先考虑" if priority == "medium" else "加分项")
        result["priority_actions"].append({
            "skill": skill,
            "reason": reason,
            "priority": priority,
            "action_type": "learn"
        })

    # Step 5: Sort priority actions
    priority_order = {"high": 0, "medium": 1, "low": 2}
    action_type_order = {"learn": 0, "strengthen": 1}

    result["priority_actions"].sort(key=lambda x: (
        priority_order.get(x["priority"], 3),
        action_type_order.get(x["action_type"], 2)
    ))

    # Step 6: Remove duplicates while preserving order
    result["mastered"] = list(dict.fromkeys(result["mastered"]))
    result["needs_improvement"] = list(dict.fromkeys(result["needs_improvement"]))
    result["not_learned"] = list(dict.fromkeys(result["not_learned"]))

    return result


def validate_gap_result(gap_result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that the three lists have no intersection.

    Args:
        gap_result: Gap analysis result

    Returns:
        (is_valid, list of error messages)
    """
    errors = []

    mastered = set(gap_result.get("mastered", []))
    needs_improvement = set(gap_result.get("needs_improvement", []))
    not_learned = set(gap_result.get("not_learned", []))

    # Check intersections
    if mastered & needs_improvement:
        errors.append(f"mastered 和 needs_improvement 有交集：{mastered & needs_improvement}")

    if mastered & not_learned:
        errors.append(f"mastered 和 not_learned 有交集：{mastered & not_learned}")

    if needs_improvement & not_learned:
        errors.append(f"needs_improvement 和 not_learned 有交集：{needs_improvement & not_learned}")

    return len(errors) == 0, errors


def generate_learning_suggestions(
    gap_result: Dict[str, Any],
    job_description: str = None
) -> List[Dict[str, Any]]:
    """
    Generate specific learning suggestions based on gap analysis.

    Args:
        gap_result: Gap analysis result
        job_description: Optional job description for context

    Returns:
        List of learning suggestions
    """
    suggestions = []

    for action in gap_result.get("priority_actions", []):
        skill = action["skill"]
        priority = action["priority"]
        action_type = action["action_type"]

        suggestion = {
            "skill": skill,
            "priority": priority,
            "action_type": action_type,
            "suggestion": ""
        }

        if action_type == "learn":
            if priority == "high":
                suggestion["suggestion"] = f"建议优先学习 {skill}，这是岗位的必备技能"
                suggestion["estimated_hours"] = 40  # High priority skills need more time
            elif priority == "medium":
                suggestion["suggestion"] = f"建议学习 {skill}，这是岗位的优先考虑技能"
                suggestion["estimated_hours"] = 20
            else:
                suggestion["suggestion"] = f"有时间可以学习 {skill}，这是加分项"
                suggestion["estimated_hours"] = 10
        else:  # strengthen
            if priority == "high":
                suggestion["suggestion"] = f"建议强化 {skill} 的深入学习，这是岗位的核心要求"
                suggestion["estimated_hours"] = 20
            elif priority == "medium":
                suggestion["suggestion"] = f"建议进一步提升 {skill} 的熟练度"
                suggestion["estimated_hours"] = 10
            else:
                suggestion["suggestion"] = f"可以继续精进 {skill}"
                suggestion["estimated_hours"] = 5

        suggestions.append(suggestion)

    return suggestions


def full_gap_analysis(
    student_profile: Dict[str, Any],
    job_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Perform complete gap analysis between student and job.

    Args:
        student_profile: Student's complete profile
        job_profile: Job's complete profile

    Returns:
        Complete gap analysis result
    """
    # Extract skills
    student_skills = student_profile.get("mastered_skills", [])
    job_required_skills = job_profile.get("required_skills", [])
    job_preferred_skills = job_profile.get("preferred_skills", [])

    # Get proficiency from student's dimension details if available
    student_proficiency = {}
    skill_details = student_profile.get("dimensions", {}).get("skill", {}).get("details", {})
    # This could be extended based on how proficiency is stored

    # Analyze skill gap
    gap_result = analyze_skill_gap(
        student_skills,
        job_required_skills,
        job_preferred_skills,
        student_proficiency
    )

    # Validate result
    is_valid, errors = validate_gap_result(gap_result)
    gap_result["validation"] = {
        "is_valid": is_valid,
        "errors": errors
    }

    # Generate learning suggestions
    gap_result["learning_suggestions"] = generate_learning_suggestions(gap_result)

    # Add summary statistics
    gap_result["summary"] = {
        "total_required_skills": len(job_required_skills),
        "total_preferred_skills": len(job_preferred_skills) if job_preferred_skills else 0,
        "mastered_count": len(gap_result["mastered"]),
        "needs_improvement_count": len(gap_result["needs_improvement"]),
        "not_learned_count": len(gap_result["not_learned"]),
        # Match rate: (mastered + needs_improvement) / total required
        "match_rate": (len(gap_result["mastered"]) + len(gap_result["needs_improvement"])) / max(len(job_required_skills), 1)
    }

    return gap_result
