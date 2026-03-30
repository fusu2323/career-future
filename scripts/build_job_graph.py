#!/usr/bin/env python3
"""
Phase 4 Plan 1: Build career progression graph in Neo4j.

Reads job_profiles.json (12 job types), creates level-split nodes (36 JobProfile nodes),
Skill nodes, promotion edges, and LLM-validated transition edges.

Neo4j: bolt://localhost:7687, database=planer, user=neo4j, password=fusu2023yzcm
LLM: DashScope (Qwen) via DASHSCOPE_API_KEY
"""

import json
import os
import time
from itertools import combinations
from collections import defaultdict

import pandas as pd
from neo4j import GraphDatabase
import tiktoken

# ─── Configuration ─────────────────────────────────────────────────────────────
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "fusu2023yzcm")
NEO4J_DB = "planer"

PROFILES_PATH = "data/processed/job_profiles.json"
EDGE_OUT_PATH = "data/processed/job_graph_edges.json"

LEVELS = ["初级", "中级", "高级"]
LEVEL_PAIRS = [("初级", "中级"), ("中级", "高级")]

PROMOTION_DEFAULTS = {
    ("初级", "中级"): {"salary_increase_pct": 25.0, "years_to_next_level": 2,
                       "skill_delta": ["系统设计", "架构思维"]},
    ("中级", "高级"): {"salary_increase_pct": 40.0, "years_to_next_level": 3,
                       "skill_delta": ["技术管理", "团队指导", "架构设计"]},
}

# LLM batch settings
PAIRS_PER_BATCH = 10  # 10 pairs per LLM call
SKILL_OVERLAP_THRESHOLD = 0.20  # 20% skill overlap minimum for transition

# ─── Neo4j Driver ──────────────────────────────────────────────────────────────
def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

# ─── Data Loading ──────────────────────────────────────────────────────────────
def load_profiles(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def flatten_skills(profile):
    """Return all skills as a flat list."""
    skills = profile.get("professional_skills", {})
    all_skills = []
    for cat in ["core_skills", "soft_skills", "tools_frameworks"]:
        all_skills.extend(skills.get(cat, []))
    return all_skills

def get_core_skills(profile):
    """Return only core_skills for transition analysis."""
    return profile.get("professional_skills", {}).get("core_skills", [])

# ─── LLM: DashScope Qwen ──────────────────────────────────────────────────────
import httpx

DASHSCOPE_API = "https://dashscope.aliyuncs.com/compatible-mode/v1"

def get_dashscope_client():
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY not set")
    return api_key

def call_qwen_batch(client, pairs_batch, level_label):
    """
    Send a batch of job-pair transition analyses to Qwen/DashScope.
    pairs_batch: list of dicts with {from_job, to_job, level, skills_a, skills_b}
    level_label: Chinese level string (初级/中级/高级) - used in prompt
    Returns: list of result dicts with has_transition, shared_skills, gap_skills, difficulty, salary_change_pct, rationale
    """
    import openai  # DashScope is OpenAI-compatible

    # Build pair descriptions - include level in prompt
    pair_lines = []
    for i, p in enumerate(pairs_batch):
        pair_lines.append(
            f"岗位对{i+1}: {p['from_job']} → {p['to_job']}\n"
            f"  职级: {p['level']}\n"
            f"  {p['from_job']}核心技能: {', '.join(p['skills_a'][:10])}\n"
            f"  {p['to_job']}核心技能: {', '.join(p['skills_b'][:10])}"
        )

    prompt = (
        f"你是一名职业规划专家。请分析以下{level_label}级别的多个岗位对之间的技能可迁移性。\n"
        "判断规则：技能重叠≥20%则存在迁移路径。\n\n"
        + "\n\n".join(pair_lines) +
        "\n\n请以JSON格式输出，包含一个pairs数组，每个元素包含：\n"
        "  from_job: 源岗位名称\n"
        "  to_job: 目标岗位名称\n"
        "  level: 职级（必须是" + level_label + "）\n"
        "  has_transition: true或false（技能重叠≥20%则为true）\n"
        "  shared_skills: 共享技能列表\n"
        "  gap_skills: 缺口技能列表（从源转到目标需要补充的技能）\n"
        "  difficulty: 1-5（1=很容易，5=极难）\n"
        "  salary_change_pct: 薪资变化百分比（正数涨薪，负数降薪）\n"
        "  rationale: 简要迁移逻辑说明\n\n"
        "输出格式：{\"pairs\": [...]}"
    )

    # Estimate tokens
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        token_count = len(enc.encode(prompt))
        print(f"    [LLM] Prompt tokens: ~{token_count}, {len(pairs_batch)} pairs")
    except Exception:
        pass

    # Call DashScope
    client_gpt = openai.OpenAI(
        api_key=client,
        base_url=DASHSCOPE_API,
    )

    response = client_gpt.chat.completions.create(
        model="qwen-plus",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
        return data.get("pairs", [])
    except json.JSONDecodeError as e:
        print(f"    [LLM] JSON parse error: {e}, raw: {raw[:200]}")
        return []

def analyze_all_transitions(profiles):
    """
    Analyze all cross-job-type transitions at each level using LLM.
    Returns list of transition edge dicts.
    """
    api_key = get_dashscope_client()
    job_types = [p["job_type"] for p in profiles]

    # Process each level separately so batches are level-consistent
    all_transitions = []
    for level in LEVELS:
        level_pairs = []
        for job_a, job_b in combinations(job_types, 2):
            prof_a = next(p for p in profiles if p["job_type"] == job_a)
            prof_b = next(p for p in profiles if p["job_type"] == job_b)
            skills_a = get_core_skills(prof_a)
            skills_b = get_core_skills(prof_b)
            level_pairs.append({
                "from_job": job_a,
                "to_job": job_b,
                "level": level,
                "skills_a": skills_a,
                "skills_b": skills_b,
            })

        # Build a map from (from_job, to_job) -> pair for later lookup
        pair_map = {(p["from_job"], p["to_job"]): p for p in level_pairs}

        num_batches = (len(level_pairs) + PAIRS_PER_BATCH - 1) // PAIRS_PER_BATCH
        print(f"[LLM] Level={level}: {len(level_pairs)} pairs, {num_batches} batches")

        for i in range(0, len(level_pairs), PAIRS_PER_BATCH):
            batch = level_pairs[i:i + PAIRS_PER_BATCH]
            batch_num = i // PAIRS_PER_BATCH + 1
            print(f"  [LLM] Batch {batch_num}/{num_batches} ({len(batch)} pairs)...")
            try:
                results = call_qwen_batch(api_key, batch, level)
                for r in results:
                    if r.get("has_transition", False):
                        # Always use the Chinese level from the loop variable,
                        # not the LLM-echoed value (LLM may return English).
                        all_transitions.append({
                            "from_job": r.get("from_job"),
                            "to_job": r.get("to_job"),
                            "level": level,  # Always use Chinese level from loop var
                            "shared_skills": r.get("shared_skills", []),
                            "gap_skills": r.get("gap_skills", []),
                            "difficulty": r.get("difficulty", 3),
                            "salary_change_pct": r.get("salary_change_pct", 0.0),
                            "rationale": r.get("rationale", ""),
                        })
                print(f"    Valid transitions so far: {len(all_transitions)}")
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"    [LLM] Batch error: {e}")
                continue

    print(f"[LLM] Total valid transitions: {len(all_transitions)}")
    return all_transitions

# ─── Neo4j Operations ──────────────────────────────────────────────────────────
def clear_graph(driver):
    """Full clear before rebuild."""
    with driver.session(database=NEO4J_DB) as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("[Neo4j] Graph cleared.")

def create_jobprofile_nodes(driver, profiles):
    """Create 36 level-split JobProfile nodes (12 jobs × 3 levels)."""
    nodes_batch = []
    for p in profiles:
        job_type = p["job_type"]
        skills = p.get("professional_skills", {})
        for level in LEVELS:
            nodes_batch.append({
                "job_type": job_type,
                "level": level,
                "skills": json.dumps(skills, ensure_ascii=False),
                "avg_min": p.get("avg_salary_min"),
                "avg_max": p.get("avg_salary_max"),
                "innovation": p.get("innovation_ability", 3),
                "learning": p.get("learning_ability", 3),
                "stress": p.get("stress_resistance", 3),
                "comm": p.get("communication_ability", 3),
                "internship": p.get("internship_importance", 3),
                "summary": p.get("summary", ""),
                "record_count": p.get("source_record_count", 0),
            })

    cypher = """
    UNWIND $batch AS row
    MERGE (j:JobProfile {job_type: row.job_type, level: row.level})
    SET j.professional_skills = row.skills,
        j.avg_salary_min = row.avg_min,
        j.avg_salary_max = row.avg_max,
        j.innovation_ability = row.innovation,
        j.learning_ability = row.learning,
        j.stress_resistance = row.stress,
        j.communication_ability = row.comm,
        j.internship_importance = row.internship,
        j.summary = row.summary,
        j.source_record_count = row.record_count
    """

    with driver.session(database=NEO4J_DB) as session:
        session.run(cypher, {"batch": nodes_batch})

    print(f"[Neo4j] Created {len(nodes_batch)} JobProfile nodes.")

def create_skill_nodes(driver, profiles):
    """Create Skill nodes for all unique skills, linked via REQUIRES edges."""
    # Collect all unique skills
    all_skills = set()
    for p in profiles:
        for skill in flatten_skills(p):
            all_skills.add(skill)

    skill_nodes = [{"name": s} for s in sorted(all_skills)]

    # Create Skill nodes
    skill_cypher = """
    UNWIND $batch AS row
    MERGE (s:Skill {name: row.name})
    """
    with driver.session(database=NEO4J_DB) as session:
        session.run(skill_cypher, {"batch": skill_nodes})

    print(f"[Neo4j] Created {len(skill_nodes)} Skill nodes.")

    # Create REQUIRES edges: each JobProfile → its required Skills
    requires_batch = []
    for p in profiles:
        job_type = p["job_type"]
        for level in LEVELS:
            for skill in flatten_skills(p):
                requires_batch.append({
                    "job_type": job_type,
                    "level": level,
                    "skill": skill,
                })

    requires_cypher = """
    UNWIND $batch AS row
    MATCH (j:JobProfile {job_type: row.job_type, level: row.level})
    MATCH (s:Skill {name: row.skill})
    MERGE (j)-[r:REQUIRES]->(s)
    """
    with driver.session(database=NEO4J_DB) as session:
        session.run(requires_cypher, {"batch": requires_batch})

    print(f"[Neo4j] Created {len(requires_batch)} REQUIRES edges.")

def create_promotion_edges(driver, profiles):
    """Create PROMOTES_TO edges for each job type at each level transition."""
    for p in profiles:
        job_type = p["job_type"]
        for (from_level, to_level), props in PROMOTION_DEFAULTS.items():
            cypher = """
            MATCH (a:JobProfile {job_type: $jt, level: $fl})
            MATCH (b:JobProfile {job_type: $jt, level: $tl})
            MERGE (a)-[r:PROMOTES_TO]->(b)
            SET r.salary_increase_pct = $sip,
                r.years_to_next_level = $ytn,
                r.skill_delta = $sd
            """
            with driver.session(database=NEO4J_DB) as session:
                session.run(cypher, {
                    "jt": job_type,
                    "fl": from_level,
                    "tl": to_level,
                    "sip": props["salary_increase_pct"],
                    "ytn": props["years_to_next_level"],
                    "sd": json.dumps(props["skill_delta"], ensure_ascii=False),
                })

    print(f"[Neo4j] Created PROMOTES_TO edges for {len(profiles)} job types.")

def create_transition_edges(driver, transition_edges):
    """Create TRANSITIONS_TO edges from LLM-analyzed results."""
    if not transition_edges:
        print("[Neo4j] No transition edges to create.")
        return

    edge_batch = []
    for e in transition_edges:
        edge_batch.append({
            "from_job": e["from_job"],
            "to_job": e["to_job"],
            "level": e["level"],
            "shared": json.dumps(e.get("shared_skills", []), ensure_ascii=False),
            "gap": json.dumps(e.get("gap_skills", []), ensure_ascii=False),
            "diff": e.get("difficulty", 3),
            "sal_change": e.get("salary_change_pct", 0.0),
            "rationale": e.get("rationale", ""),
        })

    cypher = """
    UNWIND $batch AS row
    MATCH (a:JobProfile {job_type: row.from_job, level: row.level})
    MATCH (b:JobProfile {job_type: row.to_job, level: row.level})
    MERGE (a)-[r:TRANSITIONS_TO]->(b)
    SET r.shared_skills = row.shared,
        r.gap_skills = row.gap,
        r.difficulty = row.diff,
        r.salary_change_pct = row.sal_change,
        r.rationale = row.rationale
    """

    with driver.session(database=NEO4J_DB) as session:
        summary = session.execute_write(lambda tx: tx.run(cypher, {"batch": edge_batch}).consume())
        print(f"[Neo4j] Created {summary.counters.relationships_created} TRANSITIONS_TO edges.")

def verify_graph(driver):
    """Verify graph statistics."""
    queries = {
        "job_nodes": "MATCH (n:JobProfile) RETURN count(n) AS cnt",
        "skill_nodes": "MATCH (n:Skill) RETURN count(n) AS cnt",
        "total_nodes": "MATCH (n) RETURN count(n) AS cnt",
        "promotion_edges": "MATCH ()-[r:PROMOTES_TO]->() RETURN count(r) AS cnt",
        "transition_edges": "MATCH ()-[r:TRANSITIONS_TO]->() RETURN count(r) AS cnt",
        "requires_edges": "MATCH ()-[r:REQUIRES]->() RETURN count(r) AS cnt",
        "total_edges": "MATCH ()-[r]->() RETURN count(r) AS cnt",
    }

    results = {}
    with driver.session(database=NEO4J_DB) as session:
        for name, qry in queries.items():
            r = session.run(qry).single()
            results[name] = r["cnt"] if r else 0

    print("\n=== Graph Verification ===")
    for k, v in results.items():
        print(f"  {k}: {v}")

    # Check success criteria
    success = (
        results["total_nodes"] >= 100 and
        results["total_edges"] >= 200 and
        results["promotion_edges"] == 24 and
        results["transition_edges"] >= 50
    )

    # Jobs with 2+ transitions
    qry = """
    MATCH (a:JobProfile)-[r:TRANSITIONS_TO]->(:JobProfile)
    WITH a.job_type as jt, count(r) as cnt
    WHERE cnt >= 2
    RETURN collect(jt) AS jobs
    """
    with driver.session(database=NEO4J_DB) as session:
        r = session.run(qry).single()
        jobs_2plus = r["jobs"] if r else []

    print(f"  jobs_with_2plus_transitions: {len(jobs_2plus)} ({jobs_2plus})")

    # Query performance test
    start = time.time()
    with driver.session(database=NEO4J_DB) as session:
        session.run("""
        PROFILE MATCH (a:JobProfile)-[:PROMOTES_TO*1..3]->(b:JobProfile)
        RETURN a.job_type, b.job_type
        LIMIT 10
        """).consume()
    elapsed_ms = (time.time() - start) * 1000
    print(f"  query_time_ms: {elapsed_ms:.1f}ms")

    print(f"\n  SUCCESS: {success}")
    return results, success, jobs_2plus

# ─── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Phase 4 Plan 1: Job Graph Builder")
    print("=" * 60)

    # Load profiles
    print(f"\n[Step 1] Loading profiles from {PROFILES_PATH}...")
    profiles = load_profiles(PROFILES_PATH)
    print(f"  Loaded {len(profiles)} job types")

    # Connect to Neo4j
    driver = get_driver()
    print(f"\n[Step 2] Connecting to Neo4j {NEO4J_URI}/{NEO4J_DB}...")

    # Clear graph
    print("\n[Step 3] Clearing existing graph...")
    clear_graph(driver)

    # Create JobProfile nodes
    print("\n[Step 4] Creating JobProfile nodes (36 nodes: 12 jobs × 3 levels)...")
    create_jobprofile_nodes(driver, profiles)

    # Create Skill nodes and REQUIRES edges
    print("\n[Step 5] Creating Skill nodes and REQUIRES edges...")
    create_skill_nodes(driver, profiles)

    # Create promotion edges
    print("\n[Step 6] Creating PROMOTES_TO edges (24 edges: 12 jobs × 2 transitions)...")
    create_promotion_edges(driver, profiles)

    # LLM transition analysis
    print("\n[Step 7] Running LLM transition analysis...")
    print(f"  (Using DashScope/Qwen API, {PAIRS_PER_BATCH} pairs/batch)")
    transition_edges = analyze_all_transitions(profiles)

    # Save intermediate edge data
    with open(EDGE_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"transitions": transition_edges, "count": len(transition_edges)},
                  f, ensure_ascii=False, indent=2)
    print(f"  Saved to {EDGE_OUT_PATH}")

    # Create transition edges
    print("\n[Step 8] Creating TRANSITIONS_TO edges...")
    create_transition_edges(driver, transition_edges)

    # Verification
    print("\n[Step 9] Verifying graph...")
    results, success, jobs_2plus = verify_graph(driver)

    driver.close()

    print("\n" + "=" * 60)
    if success:
        print("BUILD COMPLETE - Success criteria met!")
    else:
        print("BUILD COMPLETE - Some criteria not met (see above)")
    print("=" * 60)

    return results, success, jobs_2plus

if __name__ == "__main__":
    main()
