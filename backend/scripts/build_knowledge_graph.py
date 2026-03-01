"""
Knowledge Graph Builder for Career Paths

Builds Neo4j graph with:
- Vertical promotion paths (初级->高级->专家)
- Horizontal transition paths (数据分析师->算法工程师)
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.neo4j_db import get_neo4j_driver, init_neo4j_database
from app.services.chroma_db import get_chroma_client

# Job category hierarchy for vertical promotion
PROMOTION_PATHS = {
    "前端开发": ["初级前端工程师", "前端工程师", "高级前端工程师", "前端专家/架构师", "技术总监"],
    "后端开发": ["初级后端工程师", "后端工程师", "高级后端工程师", "后端专家/架构师", "技术总监"],
    "全栈开发": ["初级全栈工程师", "全栈工程师", "高级全栈工程师", "全栈架构师", "技术总监"],
    "移动开发": ["初级移动端工程师", "移动端工程师", "高级移动端工程师", "移动技术专家", "技术总监"],
    "测试工程师": ["初级测试工程师", "测试工程师", "高级测试工程师", "测试专家/QA 经理", "质量总监"],
    "产品经理": ["产品助理", "产品经理", "高级产品经理", "产品专家/产品总监", "首席产品官"],
    "ui/ux 设计": ["初级 UI 设计师", "UI 设计师", "高级 UI 设计师", "设计专家/设计总监", "创意总监"],
    "数据分析": ["数据分析师助理", "数据分析师", "高级数据分析师", "数据科学专家", "数据总监"],
    "算法/ai": ["算法工程师助理", "算法工程师", "高级算法工程师", "算法专家", "AI 实验室主任"],
    "运维工程师": ["初级运维工程师", "运维工程师", "高级运维工程师", "运维专家/SRE 架构师", "运维总监"],
    "项目管理": ["项目助理", "项目经理", "高级项目经理", "项目总监/PMO 负责人", "运营副总"],
    "架构师": ["初级架构师", "系统架构师", "高级架构师", "首席架构师", "技术副总裁"],
    "互联网技术": ["初级工程师", "工程师", "高级工程师", "技术专家", "技术总监"],
    "其他": ["初级员工", "专员", "高级专员", "资深专家", "总监"],
}

# Horizontal transition paths (skill-based transitions)
TRANSITION_PATHS = {
    "前端开发": [
        {"target": "全栈开发", "required_skills": ["后端语言", "数据库", "服务器基础"]},
        {"target": "UI/UX 设计", "required_skills": ["设计工具", "用户体验理论", "交互设计"]},
        {"target": "产品经理", "required_skills": ["需求分析", "产品设计", "项目管理"]},
    ],
    "后端开发": [
        {"target": "全栈开发", "required_skills": ["前端框架", "HTML/CSS/JS", "UI 基础"]},
        {"target": "架构师", "required_skills": ["系统设计", "分布式架构", "技术选型"]},
        {"target": "运维工程师", "required_skills": ["Linux", "Docker/K8s", "CI/CD"]},
    ],
    "全栈开发": [
        {"target": "架构师", "required_skills": ["系统设计", "技术规划", "团队管理"]},
        {"target": "技术经理", "required_skills": ["项目管理", "团队建设", "产品思维"]},
    ],
    "移动开发": [
        {"target": "全栈开发", "required_skills": ["后端开发", "Web 开发", "跨平台技术"]},
        {"target": "产品经理", "required_skills": ["产品思维", "用户体验", "市场分析"]},
    ],
    "测试工程师": [
        {"target": "产品经理", "required_skills": ["需求分析", "用户体验理解", "沟通协调能力"]},
        {"target": "运维工程师", "required_skills": ["自动化脚本", "CI/CD", "监控工具"]},
    ],
    "产品经理": [
        {"target": "项目管理", "required_skills": ["项目管理方法论", "敏捷开发", "风险管理"]},
        {"target": "运营总监", "required_skills": ["用户运营", "数据分析", "商业思维"]},
    ],
    "ui/ux 设计": [
        {"target": "前端开发", "required_skills": ["HTML/CSS", "前端框架", "交互实现"]},
        {"target": "产品经理", "required_skills": ["产品思维", "需求分析", "商业理解"]},
    ],
    "数据分析": [
        {"target": "算法/AI", "required_skills": ["机器学习", "深度学习", "Python 编程"]},
        {"target": "产品经理", "required_skills": ["产品思维", "业务理解", "决策能力"]},
    ],
    "算法/ai": [
        {"target": "数据分析", "required_skills": ["统计分析", "数据可视化", "业务分析"]},
        {"target": "架构师", "required_skills": ["系统设计", "工程化能力", "技术规划"]},
    ],
    "运维工程师": [
        {"target": "后端开发", "required_skills": ["编程语言", "数据库", "API 开发"]},
        {"target": "架构师", "required_skills": ["系统架构", "高可用设计", "云原生技术"]},
    ],
    "项目管理": [
        {"target": "产品经理", "required_skills": ["产品规划", "需求管理", "用户体验"]},
        {"target": "运营总监", "required_skills": ["团队管理", "业务流程", "数据分析"]},
    ],
    "架构师": [
        {"target": "技术总监", "required_skills": ["团队管理", "技术战略", "商业思维"]},
        {"target": "全栈开发", "required_skills": ["全栈技能", "快速原型", "技术广度"]},
    ],
}


def create_job_nodes(driver, profiles: List[Dict[str, Any]]):
    """Create job nodes in Neo4j"""
    with driver.session() as session:
        # Aggregate by category
        category_jobs = {}
        for profile in profiles:
            cat = profile.get('job_category', '其他')
            if cat not in category_jobs:
                category_jobs[cat] = {
                    'skills': [],
                    'count': 0,
                    'avg_salary': [],
                    'cities': []
                }
            data = category_jobs[cat]
            data['skills'].extend(profile.get('requirements', {}).get('skills', []))
            data['count'] += 1
            if profile.get('salary', {}).get('min', 0) > 0:
                data['avg_salary'].extend([
                    profile['salary']['min'],
                    profile['salary']['max']
                ])
            data['cities'].append(profile.get('city', ''))

        # Create category nodes
        for cat, data in category_jobs.items():
            from collections import Counter
            skill_counts = Counter(data['skills'])
            city_counts = Counter(data['cities'])
            avg_salary = sum(data['avg_salary']) / len(data['avg_salary']) if data['avg_salary'] else 0

            session.run("""
                MERGE (c:JobCategory {name: $name})
                SET c.job_count = $job_count,
                    c.top_skills = $top_skills,
                    c.avg_salary = $avg_salary,
                    c.top_cities = $top_cities
            """, {
                'name': cat,
                'job_count': data['count'],
                'top_skills': [s for s, _ in skill_counts.most_common(10)],
                'avg_salary': avg_salary,
                'top_cities': [c for c, _ in city_counts.most_common(5)]
            })

        print(f"Created {len(category_jobs)} job category nodes")


def create_promotion_relationships(driver):
    """Create vertical promotion relationships"""
    with driver.session() as session:
        count = 0
        for category, levels in PROMOTION_PATHS.items():
            # Find or create category node
            session.run("""
                MATCH (c:JobCategory {name: $category})
                RETURN c
            """, {'category': category})

            # Create promotion chain
            prev_level = None
            for i, level in enumerate(levels):
                session.run("""
                    MERGE (j:JobLevel {name: $name, level: $level, category: $category})
                """, {'name': level, 'level': i, 'category': category})

                if prev_level:
                    session.run("""
                        MATCH (prev:JobLevel {name: $prev})
                        MATCH (curr:JobLevel {name: $curr})
                        MERGE (prev)-[:PROMOTE_TO]->(curr)
                    """, {'prev': prev_level, 'curr': level})
                    count += 1

                prev_level = level

        print(f"Created {count} promotion relationships")


def create_transition_relationships(driver):
    """Create horizontal transition relationships"""
    with driver.session() as session:
        count = 0
        for source, transitions in TRANSITION_PATHS.items():
            for transition in transitions:
                target = transition['target']
                required_skills = transition['required_skills']

                session.run("""
                    MATCH (src:JobCategory {name: $source})
                    MATCH (tgt:JobCategory {name: $target})
                    MERGE (src)-[r:TRANSITION_TO]->(tgt)
                    SET r.required_skills = $skills
                """, {
                    'source': source,
                    'target': target,
                    'skills': required_skills
                })
                count += 1

        print(f"Created {count} transition relationships")


def store_in_chroma(profiles: List[Dict[str, Any]]):
    """Store job profiles in Chroma for RAG"""
    client = get_chroma_client()

    # Get or create collection
    collection = client.get_or_create_collection(
        name="job_profiles",
        metadata={"description": "Job profiles for career planning"}
    )

    # Prepare documents and embeddings
    documents = []
    ids = []
    metadatas = []

    for i, profile in enumerate(profiles):
        doc = f"""
职位类别：{profile.get('job_category', '其他')}
技能要求：{', '.join(profile.get('requirements', {}).get('skills', []))}
证书要求：{', '.join(profile.get('requirements', {}).get('certificates', []))}
学历要求：{profile.get('requirements', {}).get('education', '不限')}
经验要求：{profile.get('requirements', {}).get('experience_years', '不限')}
软技能：沟通能力{profile.get('soft_skills', {}).get('communication', 0.5):.1f},
       团队协作{profile.get('soft_skills', {}).get('teamwork', 0.5):.1f},
       抗压能力{profile.get('soft_skills', {}).get('pressure_tolerance', 0.5):.1f},
       学习能力{profile.get('soft_skills', {}).get('learning_ability', 0.5):.1f}
平均薪资：RMB {profile.get('salary', {}).get('min', 0):,.0f} - {profile.get('salary', {}).get('max', 0):,.0f}
        """.strip()

        documents.append(doc)
        ids.append(f"profile_{i}")
        metadatas.append({
            'category': profile.get('job_category', '其他'),
            'skills': ','.join(profile.get('requirements', {}).get('skills', [])),
        })

    # Add to collection (batch to avoid limits)
    batch_size = 500
    for i in range(0, len(documents), batch_size):
        end = min(i + batch_size, len(documents))
        collection.upsert(
            documents=documents[i:end],
            ids=ids[i:end],
            metadatas=metadatas[i:end]
        )

    print(f"Stored {len(documents)} profiles in Chroma")


def main():
    print("=" * 50)
    print("Knowledge Graph Builder")
    print("=" * 50)

    # Load job profiles
    input_path = Path(r"C:\Users\Administrator\Desktop\职引未来\data\processed\job_profiles.json")

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    print(f"Loading profiles from: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        profiles = json.load(f)

    print(f"Loaded {len(profiles)} profiles")

    # Initialize Neo4j
    print("\nInitializing Neo4j...")
    init_neo4j_database()
    driver = get_neo4j_driver()

    try:
        # Create job nodes
        print("\nCreating job category nodes...")
        create_job_nodes(driver, profiles)

        # Create promotion relationships
        print("\nCreating promotion relationships...")
        create_promotion_relationships(driver)

        # Create transition relationships
        print("\nCreating transition relationships...")
        create_transition_relationships(driver)

        # Store in Chroma
        print("\nStoring profiles in Chroma...")
        store_in_chroma(profiles)

        print("\n" + "=" * 50)
        print("Knowledge graph built successfully!")
        print("=" * 50)

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        driver.close()

    return 0


if __name__ == "__main__":
    exit(main())
