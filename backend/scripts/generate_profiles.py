"""
Job Profile Generator using GLM-5 LLM

Generates structured job profiles from job descriptions.
"""
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.glm_client import generate_with_json


def extract_job_profile(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured job profile from job data using LLM.

    Returns profile with:
    - skills: list of required skills
    - certificates: required certifications
    - soft_skills: communication, teamwork, etc.
    - experience: years of experience required
    - education: education requirements
    """
    job_name = job.get('job_name', '') or job.get('职位名称', '')
    job_desc = job.get('job_description', '') or job.get('职位描述', '')
    company_intro = job.get('company_intro', '') or job.get('公司简介', '')

    # Combine text for analysis
    text = f"""
职位名称：{job_name}
职位描述：{job_desc}
公司简介：{company_intro[:500] if company_intro else ''}
"""

    prompt = f"""请分析以下招聘岗位信息，提取结构化的人才画像要求。

{text}

请以 JSON 格式返回以下字段：
{{
    "skills": ["技能 1", "技能 2", ...],  // 专业技能，最多 10 个
    "certificates": ["证书 1", ...],  // 证书要求，可为空
    "education": "学历要求",  // 如：本科、大专、不限
    "experience_years": "经验年限",  // 如：1-3 年、3-5 年、不限
    "soft_skills": {{
        "communication": 0.5,  // 沟通能力要求 0-1
        "teamwork": 0.5,  // 团队协作 0-1
        "pressure_tolerance": 0.5,  // 抗压能力 0-1
        "learning_ability": 0.5  // 学习能力 0-1
    }},
    "industry": "所属行业",
    "job_category": "岗位类别"  // 如：前端开发、数据分析、产品经理
}}
"""

    try:
        result = generate_with_json(
            prompt=prompt,
            system_prompt="你是专业的招聘需求分析 AI。请准确提取岗位要求信息，以 JSON 格式返回。",
            model="glm-4-flash"
        )
        return result
    except Exception as e:
        print(f"Error extracting profile: {e}")
        return {
            "skills": [],
            "certificates": [],
            "education": "不限",
            "experience_years": "不限",
            "soft_skills": {
                "communication": 0.5,
                "teamwork": 0.5,
                "pressure_tolerance": 0.5,
                "learning_ability": 0.5
            },
            "industry": "",
            "job_category": job_name
        }


def cluster_job_categories(jobs: List[Dict[str, Any]], profiles: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    """
    Cluster jobs by category for profile generation.
    Returns dict mapping category to list of job indices.
    """
    categories = {}
    for i, profile in enumerate(profiles):
        cat = profile.get('job_category', '其他')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(i)
    return categories


def generate_core_profiles(jobs_data: List[Dict[str, Any]], sample_size: int = 100) -> List[Dict[str, Any]]:
    """
    Generate core job profiles by analyzing a sample of jobs.
    """
    print(f"Generating profiles from {len(jobs_data)} jobs...")

    # Sample jobs for profile extraction
    import random
    sampled_indices = random.sample(range(len(jobs_data)), min(sample_size, len(jobs_data)))
    sampled_jobs = [jobs_data[i] for i in sampled_indices]

    profiles = []
    for i, job in enumerate(sampled_jobs):
        if i % 10 == 0:
            print(f"  Processing job {i+1}/{len(sampled_jobs)}...")

        profile = extract_job_profile(job)
        profile['source_job'] = {
            'job_name': job.get('job_name', job.get('职位名称', '')),
            'company': job.get('company', job.get('公司全称', '')),
            'city': job.get('city', job.get('地址', ''))
        }
        profiles.append(profile)

    return profiles


def aggregate_profiles(profiles: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate profiles by job category.
    Returns consolidated profiles per category.
    """
    from collections import defaultdict

    category_profiles = defaultdict(list)
    for profile in profiles:
        cat = profile.get('job_category', '其他')
        category_profiles[cat].append(profile)

    # Aggregate skills and requirements per category
    aggregated = {}
    for category, cat_profiles in category_profiles.items():
        all_skills = []
        all_certs = []
        educations = []
        experiences = []
        soft_skill_scores = {
            'communication': [],
            'teamwork': [],
            'pressure_tolerance': [],
            'learning_ability': []
        }

        for p in cat_profiles:
            all_skills.extend(p.get('skills', []))
            all_certs.extend(p.get('certificates', []))
            if p.get('education'):
                educations.append(p['education'])
            if p.get('experience_years'):
                experiences.append(p['experience_years'])
            ss = p.get('soft_skills', {})
            for key in soft_skill_scores:
                if key in ss:
                    soft_skill_scores[key].append(ss[key])

        # Count skill frequency
        from collections import Counter
        skill_counts = Counter(all_skills)
        cert_counts = Counter(all_certs)

        # Get most common requirements
        top_skills = [skill for skill, count in skill_counts.most_common(15)]
        top_certs = [cert for cert, count in cert_counts.most_common(5)]

        # Most common education/experience
        edu_counter = Counter(educations)
        exp_counter = Counter(experiences)
        common_edu = edu_counter.most_common(1)[0][0] if edu_counter else '不限'
        common_exp = exp_counter.most_common(1)[0][0] if exp_counter else '不限'

        # Average soft skill scores
        avg_soft_skills = {
            key: sum(scores) / len(scores) if scores else 0.5
            for key, scores in soft_skill_scores.items()
        }

        aggregated[category] = {
            'category': category,
            'skills': top_skills,
            'certificates': top_certs,
            'education': common_edu,
            'experience_years': common_exp,
            'soft_skills': avg_soft_skills,
            'sample_count': len(cat_profiles)
        }

    return aggregated


def main():
    print("=" * 50)
    print("Job Profile Generator")
    print("=" * 50)

    # Load cleaned job data
    input_path = Path(r"C:\Users\Administrator\Desktop\职引未来\data\processed\jobs.json")

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    print(f"Loading data from: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        jobs_data = json.load(f)

    print(f"Loaded {len(jobs_data)} jobs")

    # Generate profiles from sample
    print("\nExtracting profiles using LLM...")
    profiles = generate_core_profiles(jobs_data, sample_size=50)

    # Save individual profiles
    output_profiles_path = Path(r"C:\Users\Administrator\Desktop\职引未来\data\processed\job_profiles_sample.json")
    with open(output_profiles_path, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(profiles)} profiles to: {output_profiles_path}")

    # Aggregate by category
    print("\nAggregating profiles by category...")
    aggregated = aggregate_profiles(profiles)

    # Save aggregated profiles
    output_aggregated_path = Path(r"C:\Users\Administrator\Desktop\职引未来\data\processed\job_profiles_aggregated.json")
    with open(output_aggregated_path, 'w', encoding='utf-8') as f:
        json.dump(aggregated, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(aggregated)} category profiles to: {output_aggregated_path}")

    # Show summary
    print("\n" + "=" * 50)
    print("Profile Summary:")
    print("=" * 50)
    for cat, profile in sorted(aggregated.items(), key=lambda x: -x[1]['sample_count'])[:15]:
        print(f"\n{cat} ({profile['sample_count']} samples):")
        print(f"  Top skills: {', '.join(profile['skills'][:5])}")
        print(f"  Education: {profile['education']}")
        print(f"  Experience: {profile['experience_years']}")

    print("\n" + "=" * 50)
    print("Profile generation completed!")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    exit(main())
