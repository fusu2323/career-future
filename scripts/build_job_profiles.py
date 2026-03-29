"""
Build job profiles - Phase 3
Loads jobs_cleaned.json, discovers TOP-12 job types by frequency,
generates 7-dimension profiles via two-step DeepSeek LLM pipeline,
outputs to JSON + Neo4j dual storage.
"""
import json
import os
import sys
from collections import Counter

import pandas as pd
import tiktoken
from openai import OpenAI
from neo4j import GraphDatabase
from tqdm import tqdm

# Config
JOBS_PATH = "data/processed/jobs_cleaned.json"
PROFILES_PATH = "data/processed/job_profiles.json"
TARGET_JOB_TYPES = 12  # >=10 per D-01
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# LLM prompts
EXTRACTION_PROMPT = """你是一名HR数据分析师。从以下{job_type}岗位的招聘数据中，提取关键统计信息。

岗位数据（共{count}条）：
{job_details}

请以JSON格式输出：
{{
  "job_type": "{job_type}",
  "total_records": {count},
  "skill_frequency": {{"技能名": 出现次数, ...}},
  "avg_salary_min": 平均月薪下限,
  "avg_salary_max": 平均月薪上限,
  "education_requirements": {{"学历": 出现次数, ...}},
  "experience_years_range": "X-Y年",
  "top_companies": ["公司名", ...],
  "common_responsibilities": ["职责1", "职责2", ...],
  "certificates_mentioned": {{"证书名": 次数, ...}}
}}"""

SYNTHESIS_PROMPT = """你是一名职业规划专家。基于以下{job_type}岗位的招聘数据分析，生成标准7维画像。

分析数据：
{extracted_stats}

请以JSON格式输出7维画像：
{{
  "job_type": "{job_type}",
  "professional_skills": {{
    "core_skills": ["技能1", "技能2", ...],
    "soft_skills": ["技能A", "技能B", ...],
    "tools_frameworks": ["工具/框架1", ...]
  }},
  "certificate_requirements": {{
    "required": ["证书1", ...],
    "preferred": ["证书A", ...]
  }},
  "innovation_ability": 1-5,
  "learning_ability": 1-5,
  "stress_resistance": 1-5,
  "communication_ability": 1-5,
  "internship_importance": 1-5,
  "summary": "一句话概括该岗位的核心特征"
}}"""


def load_jobs(path):
    """Load cleaned job records from JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def discover_job_types(jobs, target_count):
    """Discover TOP-N job types by frequency."""
    df = pd.DataFrame(jobs)
    title_counts = df["岗位名称"].value_counts()
    top_types = title_counts.head(target_count)
    print(f"\nDiscovered {len(top_types)} job types:")
    for job_type, count in top_types.items():
        print(f"  - {job_type}: {count} records")
    return top_types.index.tolist()


def build_details_text(records):
    """Build truncated details text for each job record."""
    details = []
    for r in records:
        detail = (r.get("job_detail_cleaned") or "")[:400]
        salary_min = r.get("salary_min_monthly", 0) or 0
        salary_max = r.get("salary_max_monthly", 0) or 0
        city = r.get("city", "") or ""
        details.append(f"城市:{city}|薪资:{salary_min:.0f}-{salary_max:.0f}|详情:{detail}")
    return "\n".join(details)


def call_llm(client, prompt, temperature=0.1):
    """Call DeepSeek API with JSON output."""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def generate_profile_for_job_type(client, enc, job_type, records):
    """Generate 7-dimension profile for a single job type using two-step LLM."""
    # Build details text
    details_text = build_details_text(records)
    count = len(records)

    # Step 1: Extract structured stats
    extract_prompt = EXTRACTION_PROMPT.format(
        job_type=job_type,
        count=count,
        job_details=details_text
    )

    # Token budget check - truncate if too long
    token_count = len(enc.encode(extract_prompt))
    if token_count > 3500:
        # Truncate details to fit budget
        max_chars = int(3500 / token_count * len(details_text))
        details_text = details_text[:max_chars]
        extract_prompt = EXTRACTION_PROMPT.format(
            job_type=job_type,
            count=count,
            job_details=details_text
        )

    # Call LLM for extraction with retry
    stats = None
    for attempt in range(2):
        try:
            stats = call_llm(client, extract_prompt, temperature=0.1)
            break
        except (json.JSONDecodeError, KeyError) as e:
            if attempt == 0:
                print(f"    Retry due to parse error: {e}")
                continue
            else:
                raise

    # Step 2: Synthesize 7-dimension profile
    synthesis_prompt = SYNTHESIS_PROMPT.format(
        job_type=job_type,
        extracted_stats=json.dumps(stats, ensure_ascii=False)
    )

    profile = None
    for attempt in range(2):
        try:
            profile = call_llm(client, synthesis_prompt, temperature=0.2)
            break
        except (json.JSONDecodeError, KeyError) as e:
            if attempt == 0:
                print(f"    Retry due to parse error: {e}")
                continue
            else:
                raise

    # Add source metadata
    profile["source_record_count"] = count
    profile["avg_salary_min"] = stats.get("avg_salary_min")
    profile["avg_salary_max"] = stats.get("avg_salary_max")

    return profile


def write_json(profiles, path):
    """Save profiles to JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(profiles)} profiles to {path}")


def write_neo4j(profiles, uri, user, password):
    """Write JobProfile nodes to Neo4j."""
    try:
        with GraphDatabase.driver(uri, auth=(user, password)) as driver:
            with driver.session() as session:
                for p in profiles:
                    session.run("""
                        MERGE (j:JobProfile {job_type: $job_type})
                        SET j.professional_skills = $skills,
                            j.certificate_requirements = $certificates,
                            j.innovation_ability = $innovation,
                            j.learning_ability = $learning,
                            j.stress_resistance = $stress,
                            j.communication_ability = $comm,
                            j.internship_importance = $internship,
                            j.summary = $summary,
                            j.skill_count = $skill_count,
                            j.avg_salary_min = $avg_min,
                            j.avg_salary_max = $avg_max,
                            j.source_record_count = $record_count
                    """, {
                        "job_type": p["job_type"],
                        "skills": json.dumps(p.get("professional_skills", {})),
                        "certificates": json.dumps(p.get("certificate_requirements", {})),
                        "innovation": p.get("innovation_ability", 3),
                        "learning": p.get("learning_ability", 3),
                        "stress": p.get("stress_resistance", 3),
                        "comm": p.get("communication_ability", 3),
                        "internship": p.get("internship_importance", 3),
                        "summary": p.get("summary", ""),
                        "skill_count": len(p.get("professional_skills", {}).get("core_skills", [])),
                        "avg_min": p.get("avg_salary_min"),
                        "avg_max": p.get("avg_salary_max"),
                        "record_count": p.get("source_record_count", 0)
                    })
        print(f"Wrote {len(profiles)} nodes to Neo4j")
        return True
    except Exception as e:
        print(f"WARNING: Neo4j write failed ({e})")
        return False


def main():
    # Check API key
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY environment variable is not set. Please set it before running this script.")

    # Load data
    print(f"Loading jobs from {JOBS_PATH}...")
    jobs = load_jobs(JOBS_PATH)
    print(f"Loaded {len(jobs)} job records")

    # Discover job types
    job_types = discover_job_types(jobs, TARGET_JOB_TYPES)

    # Initialize LLM client
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )

    # Initialize tokenizer
    enc = tiktoken.get_encoding("cl100k_base")

    # Generate profiles
    profiles = []
    print(f"\nGenerating profiles for {len(job_types)} job types...")
    for job_type in tqdm(job_types, desc="Generating profiles"):
        try:
            records = [j for j in jobs if j.get("岗位名称") == job_type]
            profile = generate_profile_for_job_type(client, enc, job_type, records)
            profiles.append(profile)
            print(f"  Generated: {job_type}")
        except Exception as e:
            print(f"  ERROR for {job_type}: {e}")
            continue

    print(f"\nSuccessfully generated {len(profiles)} profiles")

    # Save JSON
    write_json(profiles, PROFILES_PATH)

    # Write to Neo4j (optional)
    print(f"\nAttempting Neo4j write...")
    neo4j_success = write_neo4j(profiles, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    if not neo4j_success:
        print("Neo4j write failed, but JSON saved successfully.")

    # Summary
    print("\n" + "="*60)
    print("PROFILING COMPLETE")
    print("="*60)
    print(f"Profiles generated: {len(profiles)}")
    print(f"Output: {PROFILES_PATH}")
    print(f"Neo4j: {'Success' if neo4j_success else 'Failed (JSON only)'}")


if __name__ == "__main__":
    main()
