"""
Career Report Generator Service

Generates structured career planning reports using LLM (GLM-5).
Report sections include:
- Self-awareness analysis
- Career exploration and job matching
- Career goal setting
- Career path planning
- Short/medium/long-term action plans
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from app.services.glm_client import generate_with_json, chat_completion


# Report section templates
REPORT_SECTIONS = [
    {
        "id": "self_awareness",
        "title": "自我认知分析",
        "prompt": """基于以下学生信息，生成自我认知分析：
- 教育背景：{education}
- 掌握技能：{skills}
- 能力维度评分：{dimensions}
- 个人特点：{characteristics}

请分析学生的优势、劣势、兴趣和价值观，字数 300-400 字。"""
    },
    {
        "id": "career_exploration",
        "title": "职业探索与岗位匹配",
        "prompt": """基于以下信息，生成职业探索分析：
- 目标岗位：{target_jobs}
- 匹配岗位列表：{matched_jobs}
- 人岗匹配分数：{match_scores}
- 技能差距：{skill_gaps}

请分析职业方向选择、岗位匹配度和发展空间，字数 300-400 字。"""
    },
    {
        "id": "career_goal",
        "title": "职业目标设定",
        "prompt": """基于以下信息，生成职业目标设定建议：
- 期望城市：{target_city}
- 期望年薪：{target_salary}
- 短期目标（1 年）：{short_term_goal}
- 中期目标（3-5 年）：{mid_term_goal}
- 长期目标（5-10 年）：{long_term_goal}

请设定 SMART 原则的职业目标，字数 250-350 字。"""
    },
    {
        "id": "career_path",
        "title": "职业路径规划",
        "prompt": """基于以下信息，规划职业发展路径：
- 当前岗位：{current_job}
- 目标岗位：{target_job}
- 晋升路径：{promotion_path}
- 换岗可能性：{transition_options}

请设计垂直晋升和横向发展的职业路径，字数 250-350 字。"""
    },
    {
        "id": "action_plan",
        "title": "行动计划",
        "prompt": """基于以下信息，生成具体行动计划：
- 技能差距：{skill_gaps}
- 需要学习的技能：{skills_to_learn}
- 需要强化的技能：{skills_to_strengthen}
- 时间规划：{timeline}

请制定短期（3-6 月）、中期（6-12 月）、长期（1-2 年）的行动计划，字数 300-400 字。"""
    }
]

# Career path generation prompt
CAREER_PATH_PROMPT = """基于以下信息，生成职业发展路径建议：
- 当前专业/技能：{{current_background}}
- 目标职业方向：{{target_direction}}
- 行业趋势：{{industry_trends}}

请返回 JSON 格式：
{{
    "vertical_path": ["初级岗位", "中级岗位", "高级岗位", "专家/管理岗位"],
    "horizontal_options": [
        {{"from": "当前岗位", "to": "可换岗岗位 1", "required_skills": ["技能 1", "技能 2"]}},
        {{"from": "当前岗位", "to": "可换岗岗位 2", "required_skills": ["技能 3", "技能 4"]}}
    ],
    "timeline": {{
        "short_term": "1-2 年：达成 XX 目标",
        "mid_term": "3-5 年：达成 XX 目标",
        "long_term": "5-10 年：达成 XX 目标"
    }}
}}"""

# Action plan generation prompt
ACTION_PLAN_PROMPT = """基于以下信息，生成详细行动计划：
- 已掌握技能：{{mastered_skills}}
- 需强化技能：{{needs_improvement}}
- 未掌握技能：{{not_learned}}
- 目标岗位：{{target_job}}
- 可用时间：{{available_time}}

请返回 JSON 格式：
{{
    "phases": [
        {{
            "name": "短期（1-3 个月）",
            "focus": "学习重点",
            "tasks": ["任务 1", "任务 2", "任务 3"],
            "milestones": ["里程碑 1", "里程碑 2"]
        }},
        {{
            "name": "中期（3-6 个月）",
            "focus": "学习重点",
            "tasks": ["任务 1", "任务 2"],
            "milestones": ["里程碑 1"]
        }},
        {{
            "name": "长期（6-12 个月）",
            "focus": "学习重点",
            "tasks": ["任务 1", "任务 2"],
            "milestones": ["里程碑 1"]
        }}
    ],
    "recommended_resources": [
        {{"type": "课程", "name": "推荐课程", "url": "链接"}},
        {{"type": "证书", "name": "推荐证书"}}
    ]
}}"""


def generate_self_awareness_section(student_profile: Dict[str, Any]) -> str:
    """
    Generate self-awareness analysis section.

    Args:
        student_profile: Student's complete profile

    Returns:
        Generated section content
    """
    # Extract education info
    education_list = student_profile.get("education", [])
    education_str = "; ".join([
        f"{edu.get('school', '')} {edu.get('major', '')} {edu.get('degree', '')}"
        for edu in education_list
    ])

    # Extract skills
    skills = student_profile.get("mastered_skills", [])
    skills_str = ", ".join(skills) if skills else "暂未填写"

    # Extract dimensions
    dimensions = student_profile.get("dimensions", {})
    dimensions_str = ", ".join([
        f"{k}: {v.get('score', 0)}分"
        for k, v in dimensions.items()
    ])

    # Extract characteristics (from soft skills)
    soft_skills = dimensions.get("soft", {}).get("details", {})
    characteristics = ", ".join([
        f"{k}: {v}"
        for k, v in soft_skills.items()
    ]) if soft_skills else "暂未评估"

    prompt = REPORT_SECTIONS[0]["prompt"].format(
        education=education_str,
        skills=skills_str,
        dimensions=dimensions_str,
        characteristics=characteristics
    )

    system_prompt = "你是一位专业的职业规划师。请基于学生信息生成自我认知分析，内容要具体、有针对性，避免空话套话。字数 300-400 字。"

    try:
        content = chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return content.strip()
    except Exception as e:
        return f"生成失败：{str(e)}"


def generate_career_exploration_section(
    student_profile: Dict[str, Any],
    matched_jobs: List[Dict[str, Any]]
) -> str:
    """
    Generate career exploration and job matching section.

    Args:
        student_profile: Student's profile
        matched_jobs: List of matched job recommendations

    Returns:
        Generated section content
    """
    # Extract target jobs
    target_jobs = student_profile.get("target_jobs", [])
    if not target_jobs and matched_jobs:
        target_jobs = [job.get("job_name", "") for job in matched_jobs[:3]]

    # Format matched jobs
    matched_jobs_str = ", ".join([
        f"{job.get('job_name', '')} ({job.get('company', '')})"
        for job in matched_jobs[:5]
    ]) if matched_jobs else "暂无匹配岗位"

    # Format match scores
    match_scores_str = ", ".join([
        f"{job.get('job_name', '')}: {job.get('match_score', 0)}分"
        for job in matched_jobs[:5]
    ]) if matched_jobs else "暂无数据"

    # Extract skill gaps (from gap analysis if available)
    skill_gaps = student_profile.get("skill_gaps", {})
    skill_gaps_str = f"已掌握：{', '.join(skill_gaps.get('mastered', []))}; " \
                    f"需强化：{', '.join(skill_gaps.get('needs_improvement', []))}; " \
                    f"未掌握：{', '.join(skill_gaps.get('not_learned', []))}"

    prompt = f"""基于以下信息，生成职业探索分析：
- 目标岗位：{', '.join(target_jobs) if target_jobs else '暂未确定'}
- 匹配岗位：{matched_jobs_str}
- 匹配分数：{match_scores_str}
- 技能差距：{skill_gaps_str}

请分析职业方向选择、岗位匹配度和发展空间，字数 300-400 字。"""

    system_prompt = "你是一位专业的职业规划师。请分析学生的职业探索情况，给出有针对性的建议。字数 300-400 字。"

    try:
        content = chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return content.strip()
    except Exception as e:
        return f"生成失败：{str(e)}"


def generate_career_goal_section(
    student_profile: Dict[str, Any],
    target_city: str = None,
    target_salary: float = None
) -> str:
    """
    Generate career goal setting section.

    Args:
        student_profile: Student's profile
        target_city: Target city
        target_salary: Target annual salary

    Returns:
        Generated section content
    """
    city = target_city or student_profile.get("target_city", "未指定")
    salary = target_salary or student_profile.get("target_salary", 150000)

    # Extract goals if available
    goals = student_profile.get("career_goals", {})
    short_term = goals.get("short_term", "1 年内找到合适工作")
    mid_term = goals.get("mid_term", "3-5 年成为业务骨干")
    long_term = goals.get("long_term", "5-10 年成为专家或管理者")

    prompt = f"""基于以下信息，生成职业目标设定建议：
- 期望城市：{city}
- 期望年薪：{salary/10000:.1f}万
- 短期目标（1 年）：{short_term}
- 中期目标（3-5 年）：{mid_term}
- 长期目标（5-10 年）：{long_term}

请设定 SMART 原则的职业目标，字数 250-350 字。"""

    system_prompt = "你是一位专业的职业规划师。请基于 SMART 原则帮助学生设定职业目标。字数 250-350 字。"

    try:
        content = chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return content.strip()
    except Exception as e:
        return f"生成失败：{str(e)}"


def generate_career_path_section(
    student_profile: Dict[str, Any],
    current_job: str = None,
    target_job: str = None
) -> Dict[str, Any]:
    """
    Generate career path planning section.

    Args:
        student_profile: Student's profile
        current_job: Current/entry job title
        target_job: Target job title

    Returns:
        Generated career path with vertical and horizontal options
    """
    # Extract background
    skills = student_profile.get("mastered_skills", [])
    education = student_profile.get("education", [])
    major = education[0].get("major", "") if education else ""

    current_background = f"专业：{major}, 技能：{', '.join(skills[:5])}"
    target_direction = target_job or student_profile.get("target_job", "技术岗位")

    prompt = CAREER_PATH_PROMPT.format(
        current_background=current_background,
        target_direction=target_direction,
        industry_trends="互联网行业持续发展，AI 技术广泛应用"
    )

    system_prompt = "你是一位专业的职业规划师。请返回 JSON 格式的职业发展路径建议。"

    try:
        result = generate_with_json(prompt, system_prompt)
        return {
            "vertical_path": result.get("vertical_path", []),
            "horizontal_options": result.get("horizontal_options", []),
            "timeline": result.get("timeline", {})
        }
    except Exception as e:
        # Fallback to default path
        return {
            "vertical_path": ["初级工程师", "中级工程师", "高级工程师", "技术专家/技术经理"],
            "horizontal_options": [
                {"from": current_job or "开发工程师", "to": "产品经理", "required_skills": ["需求分析", "产品设计"]},
                {"from": current_job or "开发工程师", "to": "项目经理", "required_skills": ["项目管理", "团队协作"]}
            ],
            "timeline": {
                "short_term": "1-2 年：掌握核心技术，成为独立开发者",
                "mid_term": "3-5 年：成为技术骨干或团队负责人",
                "long_term": "5-10 年：成为技术专家或高层管理者"
            }
        }


def generate_action_plan_section(
    student_profile: Dict[str, Any],
    gap_analysis: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate action plan section.

    Args:
        student_profile: Student's profile
        gap_analysis: Skill gap analysis result

    Returns:
        Generated action plan with phases and tasks
    """
    # Extract skills from gap analysis or profile
    if gap_analysis:
        mastered = gap_analysis.get("mastered", [])
        needs_improvement = gap_analysis.get("needs_improvement", [])
        not_learned = gap_analysis.get("not_learned", [])
    else:
        mastered = student_profile.get("mastered_skills", [])
        needs_improvement = []
        not_learned = []

    target_job = student_profile.get("target_job", "技术岗位")

    prompt = ACTION_PLAN_PROMPT.format(
        mastered_skills=", ".join(mastered[:5]) if mastered else "暂未填写",
        needs_improvement=", ".join(needs_improvement) if needs_improvement else "暂无",
        not_learned=", ".join(not_learned[:5]) if not_learned else "暂无",
        target_job=target_job,
        available_time="每周 10-15 小时"
    )

    system_prompt = "你是一位专业的职业规划师。请返回 JSON 格式的详细行动计划。"

    try:
        result = generate_with_json(prompt, system_prompt)
        return {
            "phases": result.get("phases", []),
            "recommended_resources": result.get("recommended_resources", [])
        }
    except Exception as e:
        # Fallback to default action plan
        return {
            "phases": [
                {
                    "name": "短期（1-3 个月）",
                    "focus": "巩固基础，学习核心技能",
                    "tasks": ["完成在线课程学习", "参与实际项目练习", "建立技术博客"],
                    "milestones": ["掌握核心技能", "完成 1 个个人项目"]
                },
                {
                    "name": "中期（3-6 个月）",
                    "focus": "深化专业技能，准备求职",
                    "tasks": ["参与开源项目", "准备面试", "优化简历"],
                    "milestones": ["获得实习机会", "完成 2-3 个高质量项目"]
                },
                {
                    "name": "长期（6-12 个月）",
                    "focus": "职业发展与持续提升",
                    "tasks": ["入职目标公司", "持续学习新技术", "建立职业网络"],
                    "milestones": ["成功入职", "获得转正机会"]
                }
            ],
            "recommended_resources": []
        }


def generate_full_report(
    student_profile: Dict[str, Any],
    matched_jobs: List[Dict[str, Any]] = None,
    gap_analysis: Dict[str, Any] = None,
    target_city: str = None,
    target_salary: float = None
) -> Dict[str, Any]:
    """
    Generate complete career planning report.

    Args:
        student_profile: Student's complete profile
        matched_jobs: List of matched job recommendations
        gap_analysis: Skill gap analysis result
        target_city: Target city (override)
        target_salary: Target annual salary (override)

    Returns:
        Complete report with all sections
    """
    matched_jobs = matched_jobs or []

    # Generate each section
    sections = []

    # 1. Self-awareness
    self_awareness = generate_self_awareness_section(student_profile)
    sections.append({
        "id": "self_awareness",
        "title": "自我认知分析",
        "content": self_awareness
    })

    # 2. Career exploration
    career_exploration = generate_career_exploration_section(student_profile, matched_jobs)
    sections.append({
        "id": "career_exploration",
        "title": "职业探索与岗位匹配",
        "content": career_exploration
    })

    # 3. Career goal
    career_goal = generate_career_goal_section(student_profile, target_city, target_salary)
    sections.append({
        "id": "career_goal",
        "title": "职业目标设定",
        "content": career_goal
    })

    # 4. Career path
    career_path = generate_career_path_section(student_profile)
    sections.append({
        "id": "career_path",
        "title": "职业路径规划",
        "content": "",  # Will be formatted separately
        "data": career_path
    })

    # 5. Action plan
    action_plan = generate_action_plan_section(student_profile, gap_analysis)
    sections.append({
        "id": "action_plan",
        "title": "行动计划",
        "content": "",  # Will be formatted separately
        "data": action_plan
    })

    # Calculate total word count
    total_words = sum(len(s["content"]) for s in sections if s["content"])

    return {
        "student_id": student_profile.get("id", student_profile.get("student_id", "")),
        "student_name": student_profile.get("name", ""),
        "generated_at": datetime.now().isoformat(),
        "sections": sections,
        "career_path": career_path.get("vertical_path", []),
        "action_plan": action_plan.get("phases", []),
        "metadata": {
            "total_words": total_words,
            "matched_jobs_count": len(matched_jobs),
            "target_city": target_city or student_profile.get("target_city", ""),
            "target_salary": target_salary or student_profile.get("target_salary", 0)
        }
    }


def regenerate_section(
    student_profile: Dict[str, Any],
    section_id: str,
    additional_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Regenerate a specific report section.

    Args:
        student_profile: Student's profile
        section_id: Section to regenerate (self_awareness, career_exploration, etc.)
        additional_context: Additional context for regeneration

    Returns:
        Regenerated section
    """
    additional_context = additional_context or {}

    if section_id == "self_awareness":
        content = generate_self_awareness_section(student_profile)
    elif section_id == "career_exploration":
        content = generate_career_exploration_section(
            student_profile,
            additional_context.get("matched_jobs", [])
        )
    elif section_id == "career_goal":
        content = generate_career_goal_section(
            student_profile,
            additional_context.get("target_city"),
            additional_context.get("target_salary")
        )
    elif section_id == "career_path":
        data = generate_career_path_section(student_profile)
        return {
            "id": section_id,
            "title": "职业路径规划",
            "content": "",
            "data": data
        }
    elif section_id == "action_plan":
        data = generate_action_plan_section(
            student_profile,
            additional_context.get("gap_analysis")
        )
        return {
            "id": section_id,
            "title": "行动计划",
            "content": "",
            "data": data
        }
    else:
        return {
            "error": f"Unknown section_id: {section_id}"
        }

    return {
        "id": section_id,
        "title": next((s["title"] for s in REPORT_SECTIONS if s["id"] == section_id), section_id),
        "content": content
    }
