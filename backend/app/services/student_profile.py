"""
Student Profile Generator Service

Generate student capability profile from resume data.
Maps resume information to four-dimensional capability model.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from app.models.student import (
    StudentProfile,
    StudentDimensions,
    DimensionScore,
    RadarChartData
)


# Skill category mappings
SKILL_CATEGORIES = {
    "programming_languages": [
        "java", "python", "go", "javascript", "typescript", "c++", "c", "rust",
        "sql", "html", "css", "vue", "react", "angular"
    ],
    "frameworks": [
        "spring boot", "spring cloud", "mybatis", "dubbo", "gin", "flask",
        "django", "fastapi", "express", "next.js"
    ],
    "databases": [
        "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "milvus",
        "chroma", "neo4j", "sqlite", "oracle"
    ],
    "tools_platforms": [
        "git", "docker", "kubernetes", "linux", "jenkins", "ci/cd", "aws",
        "azure", "gcp", "nginx", "kafka", "rabbitmq"
    ],
    "ai_llm": [
        "llm", "rag", "agent", "langchain", "dify", "glm", "openai", "embedding",
        "asr", "tts", "nlp", "machine learning", "deep learning"
    ]
}

# Soft skills keywords
SOFT_SKILLS_KEYWORDS = {
    "communication": ["沟通", "协调", "表达", "演讲", "写作"],
    "teamwork": ["团队协作", "团队配合", "跨部门", "PM", "项目管理"],
    "pressure_handling": ["抗压", "高强度", "加班", "紧急"],
    "leadership": ["领导", "负责人", "主导", "带领", "管理"],
    "learning": ["学习", "自学", "研究", "探索"],
    "innovation": ["创新", "优化", "改进", "重构"]
}


def categorize_skills(skills: List[str]) -> Dict[str, List[str]]:
    """Categorize skills into different groups"""
    categorized = {
        "programming_languages": [],
        "frameworks": [],
        "databases": [],
        "tools_platforms": [],
        "ai_llm": [],
        "other": []
    }

    for skill in skills or []:
        skill_lower = skill.lower()
        matched = False
        for category, keywords in SKILL_CATEGORIES.items():
            for keyword in keywords:
                if keyword in skill_lower:
                    categorized[category].append(skill)
                    matched = True
                    break
            if matched:
                break
        if not matched:
            categorized["other"].append(skill)

    return categorized


def calculate_skill_score(skills: List[str]) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate skill dimension score based on skills list

    Scoring criteria:
    - Base score: 40 points
    - +5 points per skill (max 10 skills = 50 points)
    - +10 points for frameworks knowledge
    - +10 points for database knowledge
    - +10 points for tools/platforms knowledge
    - +10 points for AI/LLM knowledge (bonus)
    """
    score = 40.0  # Base score
    categorized = categorize_skills(skills)

    details = {
        "total_skills": len(skills or []),
        "programming_languages": len(categorized["programming_languages"]),
        "frameworks": len(categorized["frameworks"]),
        "databases": len(categorized["databases"]),
        "tools_platforms": len(categorized["tools_platforms"]),
        "ai_llm": len(categorized["ai_llm"]),
        "other": len(categorized["other"])
    }

    # Add points for number of skills (max 50 points for 10+ skills)
    skill_count_bonus = min(len(skills or []) * 5, 50)
    score += skill_count_bonus * 0.3  # 30% weight

    # Add points for category diversity
    category_bonus = 0
    if details["frameworks"] > 0:
        category_bonus += 10
    if details["databases"] > 0:
        category_bonus += 10
    if details["tools_platforms"] > 0:
        category_bonus += 10
    if details["ai_llm"] > 0:
        category_bonus += 10

    score += category_bonus * 0.3  # 30% weight

    # Normalize to 0-100
    score = min(max(score, 0), 100)

    details["score_breakdown"] = {
        "base": 40,
        "skill_count_bonus": round(skill_count_bonus * 0.3, 2),
        "category_diversity_bonus": round(category_bonus * 0.3, 2)
    }

    return round(score, 2), details


def calculate_base_score(
    education: List[Dict],
    degree: Optional[str] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate base dimension score based on education

    Scoring criteria:
    - Degree: 专科 60, 本科 70, 硕士 85, 博士 95
    - School tier (estimated): +0-15 points
    """
    score = 50.0

    if not education:
        details = {
            "degree": "未知",
            "school": "未知",
            "graduation_year": "未知",
            "score_breakdown": {"degree": 50, "school_tier": 0}
        }
        return score, details

    edu = education[0] if education else {}

    # Degree scoring
    degree = edu.get("degree", "")
    degree_scores = {
        "专科": 60,
        "大专": 60,
        "本科": 70,
        "学士": 70,
        "硕士": 85,
        "研究生": 85,
        "博士": 95
    }
    degree_score = degree_scores.get(degree, 60)

    # School tier bonus (simplified - would need school database in production)
    school = edu.get("school", "")
    school_bonus = 0
    if any(keyword in school for keyword in ["985", "211", "双一流", "大学"]):
        school_bonus = 15
    elif "学院" in school:
        school_bonus = 5

    score = degree_score * 0.7 + (60 + school_bonus) * 0.3

    details = {
        "degree": degree,
        "school": school,
        "graduation_year": edu.get("end_date", "未知"),
        "score_breakdown": {
            "degree_score": degree_score,
            "school_tier_bonus": school_bonus
        }
    }

    return round(min(score, 100), 2), details


def calculate_soft_score(
    self_evaluation: Optional[str] = None,
    internships: Optional[List[Dict]] = None,
    projects: Optional[List[Dict]] = None,
    awards: Optional[List[str]] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate soft skills score based on self-evaluation and experiences

    Scoring criteria:
    - Self-evaluation keywords analysis: 40 points
    - Internship experience: 30 points
    - Project leadership: 20 points
    - Awards: 10 points
    """
    score = 40.0  # Base score
    details = {
        "communication": 0,
        "teamwork": 0,
        "pressure_handling": 0,
        "leadership": 0,
        "learning": 0,
        "innovation": 0
    }

    # Analyze self-evaluation
    text = (self_evaluation or "").lower()
    for soft_skill, keywords in SOFT_SKILLS_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw.lower() in text)
        details[soft_skill] = min(count * 2, 15)  # Max 15 per skill

    self_eval_score = sum(details.values()) * 2  # Max 40 points
    score += self_eval_score

    # Internship bonus (max 20 points)
    internship_count = len(internships or [])
    internship_bonus = min(internship_count * 10, 20)
    score += internship_bonus
    details["internship_count"] = internship_count

    # Project leadership bonus (max 20 points)
    leadership_count = 0
    for proj in (projects or []):
        role = proj.get("role", "").lower()
        if any(kw in role for kw in ["负责人", "主导", "lead", "manager"]):
            leadership_count += 1
    leadership_bonus = min(leadership_count * 10, 20)
    score += leadership_bonus
    details["leadership_projects"] = leadership_count

    # Awards bonus (max 20 points)
    award_count = len(awards or [])
    award_bonus = min(award_count * 5, 20)
    score += award_bonus
    details["award_count"] = award_count

    # Normalize to 0-100
    score = min(max(score, 0), 100)

    details["score_breakdown"] = {
        "self_evaluation": round(self_eval_score, 2),
        "internship_bonus": internship_bonus,
        "leadership_bonus": leadership_bonus,
        "award_bonus": award_bonus
    }

    return round(score, 2), details


def calculate_potential_score(
    skills: List[str],
    projects: Optional[List[Dict]] = None,
    education: Optional[List[Dict]] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate potential score based on learning ability indicators

    Scoring criteria:
    - AI/LLM skills (emerging tech): 30 points
    - Project diversity: 30 points
    - Recent graduation (learning curve): 20 points
    - Continuous learning indicators: 20 points
    """
    score = 40.0  # Base score

    # AI/LLM skills bonus
    ai_keywords = ["llm", "rag", "agent", "langchain", "dify", "glm", "openai",
                   "nlp", "machine learning", "deep learning", "ai"]
    ai_skill_count = sum(1 for s in skills if any(kw in s.lower() for kw in ai_keywords))
    ai_bonus = min(ai_skill_count * 10, 30)
    score += ai_bonus

    # Project diversity
    project_count = len(projects or [])
    project_bonus = min(project_count * 8, 30)
    score += project_bonus

    # Recent graduation bonus (assuming current year 2026)
    current_year = 2026
    if education:
        grad_year_str = education[0].get("end_date", "")
        try:
            grad_year = int(grad_year_str[:4]) if grad_year_str else current_year
            years_since_grad = current_year - grad_year
            if 0 <= years_since_grad <= 2:
                score += 20  # Recent grad, high learning curve
            elif years_since_grad <= 5:
                score += 10
        except:
            pass

    # Normalize
    score = min(max(score, 0), 100)

    details = {
        "ai_skills_count": ai_skill_count,
        "project_count": project_count,
        "years_since_graduation": years_since_grad if education else "未知",
        "score_breakdown": {
            "ai_llm_bonus": ai_bonus,
            "project_diversity_bonus": project_bonus,
            "learning_curve_bonus": min(20, score - 40 - ai_bonus - project_bonus)
        }
    }

    return round(score, 2), details


def calculate_completeness(resume_data: Dict[str, Any]) -> float:
    """
    Calculate profile completeness score (0-1)

    Weights:
    - Basic info (name, phone, email): 20%
    - Education: 20%
    - Skills: 20%
    - Experience (internships + projects): 25%
    - Additional (certificates + awards + self_eval): 15%
    """
    completeness = 0.0

    # Basic info (20%)
    basic_count = sum([
        1 if resume_data.get("name") else 0,
        1 if resume_data.get("phone") else 0,
        1 if resume_data.get("email") else 0
    ])
    completeness += (basic_count / 3) * 0.20

    # Education (20%)
    education_count = len(resume_data.get("education") or [])
    completeness += min(education_count / 2, 1) * 0.20

    # Skills (20%)
    skills_count = len(resume_data.get("skills") or [])
    completeness += min(skills_count / 15, 1) * 0.20

    # Experience (25%)
    internship_count = len(resume_data.get("internships") or [])
    project_count = len(resume_data.get("projects") or [])
    exp_score = min((internship_count + project_count) / 4, 1)
    completeness += exp_score * 0.25

    # Additional (15%)
    certificates_count = len(resume_data.get("certificates") or [])
    awards_count = len(resume_data.get("awards") or [])
    has_self_eval = 1 if resume_data.get("self_evaluation") else 0
    additional_score = min((certificates_count + awards_count) / 5, 1) * 0.5 + has_self_eval * 0.5
    completeness += additional_score * 0.15

    return round(min(completeness, 1), 2)


def calculate_competitiveness_rank(
    total_score: float,
    skills_count: int
) -> str:
    """
    Calculate competitiveness rank based on simulated peer pool

    Returns rank like "前 10%", "前 30%", etc.
    """
    # Simulated percentile based on score
    if total_score >= 90:
        return "前 5%"
    elif total_score >= 85:
        return "前 10%"
    elif total_score >= 80:
        return "前 20%"
    elif total_score >= 75:
        return "前 30%"
    elif total_score >= 70:
        return "前 40%"
    elif total_score >= 65:
        return "前 50%"
    elif total_score >= 60:
        return "前 60%"
    else:
        return "前 70%"


def generate_radar_chart_data(
    dimensions: StudentDimensions
) -> List[RadarChartData]:
    """
    Generate radar chart data for ECharts visualization

    5 dimensions: 基础能力，专业技能，职业素养，发展潜力，综合能力
    """
    base_val = dimensions.base.score
    skill_val = dimensions.skill.score
    soft_val = dimensions.soft.score
    potential_val = dimensions.potential.score
    total_val = (base_val + skill_val + soft_val + potential_val) / 4

    return [
        RadarChartData(name="基础能力", value=round(base_val, 2)),
        RadarChartData(name="专业技能", value=round(skill_val, 2)),
        RadarChartData(name="职业素养", value=round(soft_val, 2)),
        RadarChartData(name="发展潜力", value=round(potential_val, 2)),
        RadarChartData(name="综合能力", value=round(total_val, 2))
    ]


def generate_student_profile(resume_data: Dict[str, Any]) -> StudentProfile:
    """
    Generate complete student profile from resume data

    Args:
        resume_data: Parsed resume data from resume_parser

    Returns:
        StudentProfile object with all dimensions and scores
    """
    # Extract data
    name = resume_data.get("name")
    phone = resume_data.get("phone")
    email = resume_data.get("email")
    education = resume_data.get("education", [])
    skills = resume_data.get("skills", [])
    internships = resume_data.get("internships", [])
    projects = resume_data.get("projects", [])
    certificates = resume_data.get("certificates", [])
    awards = resume_data.get("awards", [])
    self_evaluation = resume_data.get("self_evaluation", "")

    # Calculate dimension scores
    base_score, base_details = calculate_base_score(education)
    skill_score, skill_details = calculate_skill_score(skills)
    soft_score, soft_details = calculate_soft_score(
        self_evaluation, internships, projects, awards
    )
    potential_score, potential_details = calculate_potential_score(
        skills, projects, education
    )

    # Create dimensions object
    dimensions = StudentDimensions(
        base=DimensionScore(score=base_score, details=base_details),
        skill=DimensionScore(score=skill_score, details=skill_details),
        soft=DimensionScore(score=soft_score, details=soft_details),
        potential=DimensionScore(score=potential_score, details=potential_details)
    )

    # Calculate total score (weighted average)
    total_score = (
        base_score * 0.25 +
        skill_score * 0.35 +
        soft_score * 0.20 +
        potential_score * 0.20
    )

    # Calculate completeness
    completeness = calculate_completeness(resume_data)

    # Calculate competitiveness rank
    competitiveness_rank = calculate_competitiveness_rank(total_score, len(skills))

    # Generate radar chart data
    radar_chart_data = generate_radar_chart_data(dimensions)

    # Identify mastered vs skills to improve
    categorized = categorize_skills(skills)
    mastered_skills = (
        categorized["programming_languages"][:5] +
        categorized["frameworks"][:3] +
        categorized["databases"][:3]
    )
    skills_to_improve = categorized["other"][:5] if categorized["other"] else []

    # Create profile
    profile = StudentProfile(
        student_id=str(uuid.uuid4()),
        name=name,
        email=email,
        phone=phone,
        dimensions=dimensions,
        completeness=completeness,
        competitiveness_rank=competitiveness_rank,
        total_score=round(total_score, 2),
        radar_chart_data=radar_chart_data,
        mastered_skills=mastered_skills,
        skills_to_improve=skills_to_improve
    )

    return profile


def get_profile_json(resume_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate student profile and return as JSON-serializable dict

    Args:
        resume_data: Parsed resume data

    Returns:
        Dict representation of StudentProfile
    """
    profile = generate_student_profile(resume_data)
    return profile.model_dump()
