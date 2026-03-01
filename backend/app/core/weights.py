"""
Weight Configuration for Matching Algorithm

Dynamic weights for different job types.
"""

# Default weights (for most jobs)
DEFAULT_WEIGHTS = {
    "base": 0.25,      # 基础要求 (education, degree, city)
    "skill": 0.35,     # 专业技能 (programming languages, frameworks, tools)
    "soft": 0.20,      # 职业素养 (communication, teamwork, leadership)
    "potential": 0.20  # 发展潜力 (learning ability, innovation)
}

# Weights for specific job categories
JOB_TYPE_WEIGHTS = {
    # Technical roles - higher skill weight
    "算法工程师": {
        "base": 0.20,
        "skill": 0.50,  # Higher weight for technical skills
        "soft": 0.15,
        "potential": 0.15
    },
    "后端开发": {
        "base": 0.20,
        "skill": 0.45,
        "soft": 0.20,
        "potential": 0.15
    },
    "前端开发": {
        "base": 0.20,
        "skill": 0.45,
        "soft": 0.20,
        "potential": 0.15
    },
    "全栈开发": {
        "base": 0.20,
        "skill": 0.45,
        "soft": 0.20,
        "potential": 0.15
    },

    # Management roles - higher soft skill weight
    "项目经理": {
        "base": 0.20,
        "skill": 0.25,
        "soft": 0.40,  # Higher weight for soft skills
        "potential": 0.15
    },
    "产品总监": {
        "base": 0.25,
        "skill": 0.25,
        "soft": 0.35,
        "potential": 0.15
    },
    "技术总监": {
        "base": 0.25,
        "skill": 0.30,
        "soft": 0.30,
        "potential": 0.15
    },

    # Research roles - higher potential weight
    "研究员": {
        "base": 0.30,
        "skill": 0.30,
        "soft": 0.15,
        "potential": 0.25  # Higher weight for potential
    },
    "数据分析师": {
        "base": 0.25,
        "skill": 0.40,
        "soft": 0.20,
        "potential": 0.15
    },

    # Entry level - balanced with slight skill focus
    "初级工程师": {
        "base": 0.25,
        "skill": 0.35,
        "soft": 0.20,
        "potential": 0.20  # Higher potential for growth
    }
}


def get_weights_for_job(job_category: str, job_level: str = None) -> dict:
    """
    Get weight configuration for a specific job.

    Args:
        job_category: Job category (e.g., "算法工程师", "后端开发")
        job_level: Job level (e.g., "初级", "高级", "专家")

    Returns:
        Dict with weights for base, skill, soft, potential
    """
    # Try exact match first
    if job_category in JOB_TYPE_WEIGHTS:
        return JOB_TYPE_WEIGHTS[job_category]

    # Try partial match
    for key in JOB_TYPE_WEIGHTS:
        if key in job_category or job_category in key:
            return JOB_TYPE_WEIGHTS[key]

    # Check job level adjustments
    if job_level:
        if "初级" in job_level:
            return {
                "base": 0.25,
                "skill": 0.35,
                "soft": 0.20,
                "potential": 0.20
            }
        elif "高级" in job_level or "专家" in job_level:
            return {
                "base": 0.20,
                "skill": 0.45,
                "soft": 0.20,
                "potential": 0.15
            }
        elif "总监" in job_level or "经理" in job_level:
            return {
                "base": 0.25,
                "skill": 0.25,
                "soft": 0.35,
                "potential": 0.15
            }

    # Default weights
    return DEFAULT_WEIGHTS


def validate_weights(weights: dict) -> bool:
    """Validate that weights sum to 1.0"""
    total = sum(weights.values())
    return abs(total - 1.0) < 0.01


# Validate all weight configurations
for job_type, weights in JOB_TYPE_WEIGHTS.items():
    assert validate_weights(weights), f"Weights for {job_type} do not sum to 1.0"
assert validate_weights(DEFAULT_WEIGHTS), "Default weights do not sum to 1.0"
