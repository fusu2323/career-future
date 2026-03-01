"""
Job Profile Generator - Rule-based

Generates structured job profiles using keyword matching and rules.
This avoids encoding issues with the cleaned data.
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter

# Skill keyword patterns by category
SKILL_PATTERNS = {
    # Programming Languages
    "Java": ["java", "spring", "springboot", "spring boot", "mybatis", "hibernate"],
    "Python": ["python", "django", "flask", "fastapi", "pandas", "numpy", "scikit-learn"],
    "JavaScript": ["javascript", "js", "es6", "typescript", "ts"],
    "Go": ["golang", "go 语言"],
    "C++": ["c++", "qt", "mfc"],
    "C#": ["c#", ".net", "asp.net", "winform"],
    "PHP": ["php", "laravel", "thinkphp"],
    "SQL": ["sql", "mysql", "postgresql", "oracle", "sqlserver"],

    # Frontend
    "Vue": ["vue", "vuex", "vuejs", "uni-app"],
    "React": ["react", "redux", "reactjs", "next.js"],
    "Angular": ["angular", "angularjs"],
    "HTML/CSS": ["html", "html5", "css", "css3", "sass", "less"],

    # Backend/Infrastructure
    "Linux": ["linux", "ubuntu", "centos", "shell", "bash"],
    "Docker": ["docker", "kubernetes", "k8s", "容器"],
    "Cloud": ["aws", "azure", "阿里云", "腾讯云", "云计算"],
    "Nginx": ["nginx", "apache"],

    # Data/AI
    "Data Analysis": ["数据分析", "data", "statistics", "bi"],
    "Machine Learning": ["机器学习", "ml", "tensorflow", "pytorch", "深度学习"],
    "Big Data": ["hadoop", "spark", "hive", "kafka", "大数据"],

    # DevOps
    "CI/CD": ["jenkins", "gitlab", "ci/cd", "devops"],
    "Git": ["git", "svn", "版本控制"],

    # Product/Design
    "Product Management": ["产品", "product", "prd", "原型"],
    "UI/UX": ["ui", "ux", "figma", "sketch", "ps", "photoshop", "设计"],

    # Testing
    "QA": ["测试", "test", "qa", "selenium", "jmeter"],

    # Project Management
    "Project Management": ["项目经理", "pmp", "scrum", "敏捷", "jira"],

    # Mobile
    "iOS": ["ios", "swift", "objective-c"],
    "Android": ["android", "kotlin"],
}

# Certificate patterns
CERT_PATTERNS = {
    "软考": ["软考", "计算机技术与软件专业"],
    "PMP": ["pmp", "项目管理专业人士"],
    "Oracle": ["oracle", "oca", "ocp"],
    "AWS": ["aws", "amazon web services"],
    "Cisco": ["ccna", "ccnp", "cisco"],
    "华为": ["华为", "hcip", "hcip"],
    "阿里云": ["阿里云", "ace", "acp"],
    "英语": ["cet-4", "cet-6", "四级", "六级", "ielts", "toefl"],
}

# Education keywords
EDU_KEYWORDS = {
    "本科": ["本科", "学士", "统招本科", "985", "211"],
    "大专": ["大专", "专科", "高职"],
    "硕士": ["硕士", "研究生", "博士"],
    "高中": ["高中", "中专", "中技"],
}

# Experience keywords
EXP_KEYWORDS = {
    "应届生": ["应届", "在校", "实习", "无经验"],
    "1-3 年": ["1-3 年", "1 年以上", "2 年经验"],
    "3-5 年": ["3-5 年", "3 年以上", "4 年经验", "5 年经验"],
    "5-10 年": ["5-10 年", "5 年以上", "8 年经验", "10 年经验"],
    "10 年以上": ["10 年以上", "资深", "专家"],
}


def extract_skills(text: str) -> List[str]:
    """Extract skills from text using keyword matching"""
    if not text:
        return []
    text = str(text)
    text_lower = text.lower()
    skills = []

    for skill, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in text_lower or pattern in text:
                skills.append(skill)
                break

    return list(set(skills))


def extract_certificates(text: str) -> List[str]:
    """Extract certificates from text"""
    if not text:
        return []
    text = str(text)
    text_lower = text.lower()
    certs = []

    for cert, patterns in CERT_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in text_lower or pattern in text:
                certs.append(cert)
                break

    return list(set(certs))


def extract_education(text: str) -> str:
    """Extract education requirement from text"""
    if not text:
        return "不限"
    text = str(text)

    for edu, keywords in EDU_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return edu

    return "不限"


def extract_experience(text: str) -> str:
    """Extract experience requirement from text"""
    if not text:
        return "不限"
    text = str(text)

    for exp, keywords in EXP_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return exp

    return "不限"

    return "不限"


def categorize_job(job_name: str, description: str, industry: str) -> str:
    """Categorize job based on name and description"""
    # Handle None/NaN values
    job_name = str(job_name) if job_name else ""
    description = str(description) if description else ""
    industry = str(industry) if industry else ""

    text = (job_name + " " + description + " " + industry).lower()

    # Priority categories based on job name
    name_lower = job_name.lower() if job_name else ""

    if any(kw in name_lower for kw in ["前端", "front", "vue", "react", "ui"]):
        return "前端开发"
    elif any(kw in name_lower for kw in ["后端", "back", "java", "python", "go", "php", "c#", ".net"]):
        return "后端开发"
    elif any(kw in name_lower for kw in ["全栈", "fullstack", "full-stack"]):
        return "全栈开发"
    elif any(kw in name_lower for kw in ["移动", "android", "ios", "小程序"]):
        return "移动开发"
    elif any(kw in name_lower for kw in ["测试", "qa", "test"]):
        return "测试工程师"
    elif any(kw in name_lower for kw in ["产品", "product"]):
        return "产品经理"
    elif any(kw in name_lower for kw in ["ui", "ux", "设计", "design"]):
        return "UI/UX 设计"
    elif any(kw in name_lower for kw in ["数据", "data", "分析", "analyst"]):
        return "数据分析"
    elif any(kw in name_lower for kw in ["算法", "algorithm", "ai", "ml", "机器", "深度"]):
        return "算法/AI"
    elif any(kw in name_lower for kw in ["运维", "devops", "sre", "系统"]):
        return "运维工程师"
    elif any(kw in name_lower for kw in ["项目", "project", "scrum", "敏捷"]):
        return "项目管理"
    elif any(kw in name_lower for kw in ["架构", "architect"]):
        return "架构师"
    elif any(kw in name_lower for kw in ["实习", "intern", "应届"]):
        return "实习生"

    # Fallback to industry-based categorization
    if "互联网" in industry or "it" in industry.lower():
        return "互联网技术"

    return "其他"


def calculate_soft_skills(description: str, job_category: str) -> Dict[str, float]:
    """Calculate soft skill requirements based on job type"""
    # Handle None/NaN values
    description = str(description) if description else ""
    desc_lower = description.lower()

    # Base scores by category
    base_scores = {
        "产品经理": {"communication": 0.9, "teamwork": 0.8, "pressure_tolerance": 0.7, "learning_ability": 0.8},
        "项目管理": {"communication": 0.9, "teamwork": 0.8, "pressure_tolerance": 0.8, "learning_ability": 0.7},
        "前端开发": {"communication": 0.6, "teamwork": 0.7, "pressure_tolerance": 0.6, "learning_ability": 0.8},
        "后端开发": {"communication": 0.5, "teamwork": 0.7, "pressure_tolerance": 0.6, "learning_ability": 0.7},
        "测试工程师": {"communication": 0.6, "teamwork": 0.7, "pressure_tolerance": 0.5, "learning_ability": 0.6},
        "ui/ux 设计": {"communication": 0.7, "teamwork": 0.6, "pressure_tolerance": 0.6, "learning_ability": 0.7},
        "数据分析": {"communication": 0.6, "teamwork": 0.6, "pressure_tolerance": 0.5, "learning_ability": 0.8},
        "算法/ai": {"communication": 0.5, "teamwork": 0.6, "pressure_tolerance": 0.6, "learning_ability": 0.9},
    }

    scores = base_scores.get(job_category, {
        "communication": 0.6,
        "teamwork": 0.7,
        "pressure_tolerance": 0.5,
        "learning_ability": 0.6
    })

    # Adjust based on keywords in description
    desc_lower = description.lower() if description else ""
    if "沟通" in desc_lower or "协调" in desc_lower:
        scores["communication"] = min(1.0, scores["communication"] + 0.1)
    if "抗压" in desc_lower or "压力" in desc_lower:
        scores["pressure_tolerance"] = min(1.0, scores["pressure_tolerance"] + 0.1)
    if "学习" in desc_lower or "快速" in desc_lower:
        scores["learning_ability"] = min(1.0, scores["learning_ability"] + 0.1)

    return scores


def generate_profiles(jobs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate profiles for all jobs"""
    profiles = []

    for i, job in enumerate(jobs_data):
        if i % 1000 == 0:
            print(f"  Processing job {i+1}/{len(jobs_data)}...")

        # Get text fields (handle both Chinese and English keys)
        job_name = job.get('job_name', '') or job.get('职位名称', '') or ''
        description = job.get('job_description', '') or job.get('职位描述', '') or ''
        company = job.get('company', '') or job.get('公司全称', '') or ''
        industry = job.get('industry', '') or job.get('所属行业', '') or ''
        company_size = job.get('company_size', '') or job.get('公司规模', '') or ''
        city = job.get('city', '') or job.get('地址', '') or ''
        salary_min = job.get('salary_min', 0) or job.get('salary_min', 0)
        salary_max = job.get('salary_max', 0) or job.get('salary_max', 0)

        # Combine text for analysis
        combined_text = f"{job_name} {description} {industry} {company_size}"

        # Extract requirements
        skills = extract_skills(combined_text)
        certificates = extract_certificates(combined_text)
        education = extract_education(combined_text)
        experience = extract_experience(combined_text)
        job_category = categorize_job(job_name, description, industry)
        soft_skills = calculate_soft_skills(description, job_category)

        profile = {
            "job_name": job_name,
            "company": company,
            "city": city,
            "industry": industry,
            "job_category": job_category,
            "salary": {
                "min": salary_min,
                "max": salary_max,
                "period": job.get('salary_period', 'month')
            },
            "requirements": {
                "skills": skills,
                "certificates": certificates,
                "education": education,
                "experience_years": experience,
            },
            "soft_skills": soft_skills,
            "company_size": company_size,
        }

        profiles.append(profile)

    return profiles


def aggregate_by_category(profiles: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Aggregate profiles by job category"""
    category_data = {}

    for profile in profiles:
        cat = profile['job_category']
        if cat not in category_data:
            category_data[cat] = {
                "category": cat,
                "all_skills": [],
                "all_certificates": [],
                "educations": [],
                "experiences": [],
                "soft_skill_scores": {
                    "communication": [],
                    "teamwork": [],
                    "pressure_tolerance": [],
                    "learning_ability": []
                },
                "salary_data": [],
                "cities": [],
                "job_count": 0
            }

        data = category_data[cat]
        data["all_skills"].extend(profile["requirements"]["skills"])
        data["all_certificates"].extend(profile["requirements"]["certificates"])
        data["educations"].append(profile["requirements"]["education"])
        data["experiences"].append(profile["requirements"]["experience_years"])

        for key in data["soft_skill_scores"]:
            data["soft_skill_scores"][key].append(
                profile["soft_skills"].get(key, 0.5)
            )

        if profile["salary"]["min"] > 0:
            data["salary_data"].append({
                "min": profile["salary"]["min"],
                "max": profile["salary"]["max"]
            })

        data["cities"].append(profile["city"])
        data["job_count"] += 1

    # Aggregate results
    aggregated = {}
    for cat, data in category_data.items():
        skill_counts = Counter(data["all_skills"])
        cert_counts = Counter(data["all_certificates"])
        edu_counts = Counter(data["educations"])
        exp_counts = Counter(data["experiences"])
        city_counts = Counter(data["cities"])

        # Calculate averages
        avg_salary = []
        for s in data["salary_data"]:
            avg_salary.extend([s["min"], s["max"]])
        avg_salary_val = sum(avg_salary) / len(avg_salary) if avg_salary else 0

        aggregated[cat] = {
            "category": cat,
            "job_count": data["job_count"],
            "top_skills": [skill for skill, _ in skill_counts.most_common(15)],
            "top_certificates": [cert for cert, _ in cert_counts.most_common(5)],
            "most_common_education": edu_counts.most_common(1)[0][0] if edu_counts else "不限",
            "most_common_experience": exp_counts.most_common(1)[0][0] if exp_counts else "不限",
            "top_cities": [city for city, _ in city_counts.most_common(5)],
            "avg_salary": round(avg_salary_val, 0),
            "soft_skills": {
                key: round(sum(scores) / len(scores), 2) if scores else 0.5
                for key, scores in data["soft_skill_scores"].items()
            }
        }

    return aggregated


def main():
    print("=" * 50)
    print("Job Profile Generator (Rule-based)")
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

    # Generate profiles
    print("\nGenerating profiles...")
    profiles = generate_profiles(jobs_data)

    # Save individual profiles
    output_profiles_path = Path(r"C:\Users\Administrator\Desktop\职引未来\data\processed\job_profiles.json")
    with open(output_profiles_path, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(profiles)} profiles to: {output_profiles_path}")

    # Aggregate by category
    print("\nAggregating by category...")
    aggregated = aggregate_by_category(profiles)

    # Save aggregated profiles
    output_aggregated_path = Path(r"C:\Users\Administrator\Desktop\职引未来\data\processed\job_categories.json")
    with open(output_aggregated_path, 'w', encoding='utf-8') as f:
        json.dump(aggregated, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(aggregated)} category profiles to: {output_aggregated_path}")

    # Show summary
    print("\n" + "=" * 50)
    print("Profile Summary (Top 15 Categories):")
    print("=" * 50)
    sorted_cats = sorted(aggregated.items(), key=lambda x: -x[1]['job_count'])[:15]

    for cat, profile in sorted_cats:
        print(f"\n{cat} ({profile['job_count']} jobs):")
        print(f"  Top skills: {', '.join(profile['top_skills'][:5])}")
        print(f"  Education: {profile['most_common_education']}")
        print(f"  Experience: {profile['most_common_experience']}")
        print(f"  Avg Salary: RMB {profile['avg_salary']:,.0f}")
        print(f"  Top Cities: {', '.join(profile['top_cities'][:3])}")

    print("\n" + "=" * 50)
    print("Profile generation completed!")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    exit(main())
