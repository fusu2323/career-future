# Phase 4: Job Graph - Research

**Researched:** 2026-03-30
**Domain:** Neo4j graph construction, career path Cypher patterns, LLM-assisted relationship generation
**Confidence:** MEDIUM-HIGH

## Summary

Phase 4 builds a career path graph in Neo4j from 12 job profiles (36 level-split nodes: 3 levels per job type). Promotion edges connect junior-mid-senior within the same job type. Transition edges connect cross-job-type pairs at the same level based on LLM-assessed skill overlap. The 200+ edge target requires dense cross-job-type connections (2+ per job type minimum).

**Primary recommendation:** Use `session.execute_write()` with `UNWIND` for batch node creation, LLM-driven transition analysis per job pair with batch API calls, and `MERGE` for idempotent edge creation.

---

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Neo4j URI `bolt://localhost:7687`, database `planer`, user `neo4j`, password `fusu2023yzcm`
- **D-02:** Single graph with `PROMOTES_TO` and `TRANSITIONS_TO` relationship types
- **D-03:** Full clear before rebuild: `MATCH (n) DETACH DELETE n`
- **D-04:** Level node splitting: `{job_type}_初级`, `{job_type}_中级`, `{job_type}_高级`
- **D-05:** LLM analysis + rule validation for path generation (not pure rule-based)
- **D-06:** Promotion edges within same job type with `salary_increase_pct`, `years_to_next_level`, `skill_delta`
- **D-07:** Transition edges with `shared_skills`, `gap_skills`, `difficulty` (1-5), `salary_change_pct`
- **D-08:** JobProfile node properties: job_type, level, professional_skills (JSON), 5 ability ratings (1-5), avg_salary_min/max, summary
- **D-09:** Edge property schemas as defined in D-06 and D-07

### Claude's Discretion
- How to batch LLM calls (sequential vs parallel)
- Exact transition edge count per job type (minimum 2)
- Skill overlap threshold for rule validation
- Salary change threshold for accepting a transition edge
- How to compute `skill_delta` for promotion edges
- Whether to use intermediate Skill nodes to inflate node count

### Deferred Ideas (OUT OF SCOPE)
- Frontend visualization (Phase 10)
- Student profile integration (Phase 6-7)

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| JOB-02 | 垂直晋升图谱 - promotion paths (junior→mid→senior per job type) | Cypher MERGE patterns for directed edges, edge property computation |
| JOB-03 | 换岗路径图谱 - cross-job-type transitions, ≥5 jobs, ≥2 paths per job | LLM skill-gap prompting, cross-level transition matrix |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `neo4j` (Python driver) | 6.1.0 | Neo4j database connectivity | Project constraint, Python driver for Neo4j |
| `deepseek` / `OpenAI` compatible | API | LLM analysis for transition paths | GLM-4 or DeepSeek (project constraint) |
| `tiktoken` | 0.12.0 | Token counting for LLM budget management | Reused from Phase 3 |
| `tqdm` | 4.67.1 | Progress bars for batch processing | Reused from Phase 3 |
| `pandas` | 2.3.3 | JSON loading and data manipulation | Reused from Phase 3 |

**Installation:**
```bash
pip install neo4j==6.1.0 tiktoken tqdm pandas
```

**Version verification:** `pip show neo4j` returns 6.1.0 (verified 2026-03-30).

---

## Architecture Patterns

### Recommended Project Structure
```
scripts/
├── build_job_profiles.py     # Phase 3 - reference only
├── build_job_graph.py        # Phase 4 - NEW: main graph builder
data/processed/
├── job_profiles.json          # Phase 3 output - input to Phase 4
├── job_graph_edges.json       # Phase 4 output - intermediate
```

### Pattern 1: Neo4j Python Driver 6.x Session Management

**What:** Use `GraphDatabase.driver()` + `driver.session()` + `session.execute_write()` for write transactions.

**When to use:** All write operations to Neo4j.

**Example:**
```python
# Verified from neo4j 6.1.0 API inspection
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "fusu2023yzcm")
)

def create_node tx:
    tx.run("""
        MERGE (j:JobProfile {job_type: $job_type, level: $level})
        SET j.professional_skills = $skills,
            j.avg_salary_min = $avg_min,
            j.avg_salary_max = $avg_max,
            j.innovation_ability = $innovation,
            j.learning_ability = $learning,
            j.stress_resistance = $stress,
            j.communication_ability = $comm,
            j.internship_importance = $internship,
            j.summary = $summary
    """, {
        "job_type": job_type,
        "level": level,
        "skills": json.dumps(skills),
        "avg_min": profile.get("avg_salary_min"),
        "avg_max": profile.get("avg_salary_max"),
        "innovation": profile.get("innovation_ability", 3),
        "learning": profile.get("learning_ability", 3),
        "stress": profile.get("stress_resistance", 3),
        "comm": profile.get("communication_ability", 3),
        "internship": profile.get("internship_importance", 3),
        "summary": profile.get("summary", "")
    })

with driver.session(database="planer") as session:
    session.execute_write(create_node)
```

### Pattern 2: UNWIND Batch Node Creation

**What:** Create multiple nodes in a single transaction using `UNWIND $batch AS row`.

**When to use:** Bulk inserting 36 level-split nodes in one transaction.

**Example:**
```python
def batch_create_nodes tx, nodes_batch):
    tx.run("""
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
            j.job_type_raw = row.job_type_raw
    """, {"batch": nodes_batch})
```

### Pattern 3: MERGE for Idempotent Edge Creation

**What:** Use `MERGE` instead of `CREATE` for edges to handle re-runs safely.

**When to use:** All edge creation (PROMOTES_TO, TRANSITIONS_TO).

**Example:**
```python
# Promotion edge - idempotent
tx.run("""
    MATCH (a:JobProfile {job_type: $job_type, level: $from_level})
    MATCH (b:JobProfile {job_type: $job_type, level: $to_level})
    MERGE (a)-[r:PROMOTES_TO]->(b)
    SET r.salary_increase_pct = $salary_increase,
        r.years_to_next_level = $years,
        r.skill_delta = $skill_delta
""", {
    "job_type": "Java",
    "from_level": "中级",
    "to_level": "高级",
    "salary_increase": 30.0,
    "years": 3,
    "skill_delta": json.dumps(["架构设计", "技术管理"])
})

# Transition edge - idempotent
tx.run("""
    MATCH (a:JobProfile {job_type: $from_job, level: $level})
    MATCH (b:JobProfile {job_type: $to_job, level: $level})
    MERGE (a)-[r:TRANSITIONS_TO]->(b)
    SET r.shared_skills = $shared,
        r.gap_skills = $gap,
        r.difficulty = $difficulty,
        r.salary_change_pct = $salary_change
""", {
    "from_job": "Java",
    "to_job": "前端开发",
    "level": "高级",
    "shared": json.dumps(["JavaScript", "SQL", "团队协作"]),
    "gap": json.dumps(["HTML", "CSS", "Vue", "React"]),
    "difficulty": 3,
    "salary_change": -10.0
})
```

### Pattern 4: Full Graph Clear Before Rebuild

**What:** Delete all existing nodes/relationships before building fresh graph.

**When to use:** Phase 4 initialization (D-03).

**Example:**
```python
def clear_graph tx):
    tx.run("MATCH (n) DETACH DELETE n")
```

### Pattern 5: LLM Skill-Gap Analysis for Transition Edges

**What:** Prompt LLM to analyze skill overlap between two job profiles and output structured transition metadata.

**When to use:** Generating TRANSITIONS_TO edge properties (D-07).

**Example prompt structure:**
```
你是一名职业规划专家。分析{job_type_a}和{job_type_b}之间的技能可迁移性。

{job_type_a}技能：{skills_a}
{job_type_b}技能：{skills_b}

请判断：
1. 两个岗位之间是否存在技能迁移路径？（是/否）
2. 如果存在，输出JSON：
{
  "has_transition": true/false,
  "shared_skills": ["重叠技能1", ...],
  "gap_skills": ["缺口技能1", ...],
  "difficulty": 1-5,
  "salary_change_pct": 数字（正数表示涨薪，负数表示降薪）,
  "transition_rationale": "简要说明"
}
```

### Pattern 6: Cross-Job-Type Transition Matrix

**What:** Generate transitions between all pairs of job types at matching levels, using LLM to filter out invalid pairs.

**When to use:** Building the transition graph (D-07).

**Rationale:** 12 job types at 3 levels = 36 nodes. Each pair at same level (初级/中级/高级) is evaluated. With 12 job types, there are C(12,2) = 66 pairs per level, 198 total pairs. LLM can batch these.

### Pattern 7: Promotion Path Property Estimation

**What:** Estimate salary increase, years to next level, and skill additions based on level delta.

**When to use:** Computing PROMOTES_TO edge properties (D-06).

**Default rules (when LLM not called):**
- Junior→Mid: salary +20-30%, years 2-3, skill_delta = ["系统设计", "架构思维"]
- Mid→Senior: salary +30-50%, years 3-5, skill_delta = ["技术管理", "团队指导"]

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|------------|-------------|-----|
| Neo4j connectivity | Raw bolt protocol | `neo4j.GraphDatabase.driver` | Official driver handles connection pooling, auth, retry |
| Batch inserts | Loop with individual `session.run()` | `UNWIND $batch` | Single round-trip for many nodes/edges |
| LLM JSON parsing | Regex or string splitting | `response_format={"type": "json_object"}` | Guarantees valid JSON response from DeepSeek API |
| Edge deduplication | `CREATE` edges on re-run | `MERGE` edges | MERGE is idempotent; re-runs don't create duplicates |
| Transaction management | Auto-commit individual statements | `execute_write` with explicit transaction | Atomic operations, better error handling |

---

## Common Pitfalls

### Pitfall 1: Nodes Not Reaching 100+ Target
**What goes wrong:** 12 jobs x 3 levels = 36 nodes, falling short of 100+ node requirement.
**Why it happens:** The decision mentions "12岗位×3职级×3个属性节点" but this doesn't automatically create additional nodes.
**How to avoid:** Create intermediate nodes (e.g., Skill nodes linked to JobProfile) OR add more JobProfile nodes per level (e.g., 2 sub-types per level). Also verify edge count calculation: promotion edges (24) + transition edges (24 min) = 48 min, need more for 200+ edges.
**Warning signs:** Node count query returns <100 after build.

### Pitfall 2: Transition Edge Count Below 200
**What goes wrong:** 12 jobs x 2 transitions = 24 edges, far short of 200+.
**Why it happens:** Only 2 transitions per job type is the minimum. 200+ requires ~17 transitions per job type on average.
**How to avoid:** Generate transitions at ALL levels (初级, 中级, 高级) between job types. Java初级→前端开发初级, Java中级→前端开发中级, Java高级→前端开发高级 all count separately. With 12 jobs at 3 levels: 66 pairs x 3 levels = 198 candidate pairs. LLM filters invalid ones.
**Warning signs:** Edge count query returns <150 after build.

### Pitfall 3: Neo4j Session Not Closed
**What goes wrong:** Connection leaks, eventual "No longer has access to session" errors.
**Why it happens:** Using `driver.session()` without `with` statement or explicit `close()`.
**How to avoid:** Always use `with driver.session(database="planer") as session:` context manager.

### Pitfall 4: Missing Level Labels on Nodes
**What goes wrong:** `MATCH (a:JobProfile {job_type: "Java"})` returns all 3 Java level nodes, causing duplicate/unintended edges.
**Why it happens:** Node merge key only includes job_type without level.
**How to avoid:** Use composite merge key `{job_type: $job_type, level: $level}` as in D-08. Always match both job_type AND level when creating edges.

### Pitfall 5: LLM Cost Blowout
**What goes wrong:** 12 jobs x 12 jobs x 3 levels = 432 LLM calls.
**Why it happens:** Naive pair-by-pair prompting.
**How to avoid:** Batch pairs in single LLM call (up to 10 pairs per call), use token budget truncation.

---

## Code Examples

### Neo4j 6.x Recommended Write Pattern (Verified API)
```python
# Source: neo4j-python-driver 6.1.0 API inspection
from neo4j import GraphDatabase
import json

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "fusu2023yzcm")

def build_graph(profiles):
    driver = GraphDatabase.driver(URI, auth=AUTH)

    # Step 1: Clear existing graph
    with driver.session(database="planer") as session:
        session.execute_write(lambda tx: tx.run("MATCH (n) DETACH DELETE n"))

    # Step 2: Create level-split nodes
    nodes_batch = []
    for p in profiles:
        job_type = p["job_type"]
        skills = p.get("professional_skills", {})
        core_skills = skills.get("core_skills", [])
        soft_skills = skills.get("soft_skills", [])
        tools = skills.get("tools_frameworks", [])

        for level, level_suffix in [("初级", "junior"), ("中级", "mid"), ("高级", "senior")]:
            nodes_batch.append({
                "job_type": job_type,
                "job_type_raw": job_type,
                "level": level,
                "skills": json.dumps(skills, ensure_ascii=False),
                "avg_min": p.get("avg_salary_min"),
                "avg_max": p.get("avg_salary_max"),
                "innovation": p.get("innovation_ability", 3),
                "learning": p.get("learning_ability", 3),
                "stress": p.get("stress_resistance", 3),
                "comm": p.get("communication_ability", 3),
                "internship": p.get("internship_importance", 3),
                "summary": p.get("summary", "")
            })

    with driver.session(database="planer") as session:
        session.execute_write(lambda tx: tx.run("""
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
                j.summary = row.summary
        """, {"batch": nodes_batch}))

    # Step 3: Create promotion edges (same job type, adjacent levels)
    with driver.session(database="planer") as session:
        for p in profiles:
            job_type = p["job_type"]
            for from_level, to_level, years, salary_pct, skill_add in [
                ("初级", "中级", 2, 25.0, json.dumps(["系统设计"], ensure_ascii=False)),
                ("中级", "高级", 3, 40.0, json.dumps(["技术管理", "架构设计"], ensure_ascii=False))
            ]:
                session.execute_write(lambda tx: tx.run("""
                    MATCH (a:JobProfile {job_type: $jt, level: $fl})
                    MATCH (b:JobProfile {job_type: $jt, level: $tl})
                    MERGE (a)-[r:PROMOTES_TO]->(b)
                    SET r.salary_increase_pct = $sip,
                        r.years_to_next_level = $ytn,
                        r.skill_delta = $sd
                """, {"jt": job_type, "fl": from_level, "tl": to_level,
                      "sip": salary_pct, "ytn": years, "sd": skill_add}))

    driver.close()
```

### Transition Analysis LLM Prompt
```python
TRANSITION_PROMPT = """你是一名职业规划专家。分析以下两个岗位之间的技能可迁移性。

目标岗位A: {job_a}
技能: {skills_a}

目标岗位B: {job_b}
技能: {skills_b}

两个岗位都在{level}级别。请分析：
1. 两个岗位之间是否存在技能迁移路径？
2. 如果存在迁移，共享技能有哪些？
3. 从A转到B需要补充哪些技能？
4. 迁移难度（1-5，1=很容易，5=极难）？
5. 薪资变化百分比（正数=涨薪，负数=降薪）？

请以JSON格式输出：
{{
  "has_transition": true或false,
  "shared_skills": ["技能1", "技能2"],
  "gap_skills": ["缺口技能1", "技能2"],
  "difficulty": 1-5,
  "salary_change_pct": 数字,
  "rationale": "简要说明迁移逻辑"
}}

如果两个岗位技能重叠少于30%，返回has_transition: false。"""

def analyze_transition(client, job_a, skills_a, job_b, skills_b, level="高级"):
    prompt = TRANSITION_PROMPT.format(
        job_a=job_a, skills_a=json.dumps(skills_a, ensure_ascii=False),
        job_b=job_b, skills_b=json.dumps(skills_b, ensure_ascii=False),
        level=level
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)
```

### Graph Statistics Query
```cypher
// Node count by level
MATCH (n:JobProfile) RETURN n.level, count(n) AS count ORDER BY n.level

// Edge count by type
MATCH ()-[r:PROMOTES_TO]->() RETURN count(r) AS promotion_edges
MATCH ()-[r:TRANSITIONS_TO]->() RETURN count(r) AS transition_edges

// Verify total counts
MATCH (n:JobProfile) RETURN count(n) AS total_nodes
MATCH ()-[r]->() RETURN count(r) AS total_edges
```

---

## Runtime State Inventory

> Skip this section (no rename/refactor/migration detected for this phase).

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|-------------|------------------|--------------|--------|
| Phase 3 wrote raw JobProfile nodes to Neo4j | Phase 4 creates level-split nodes (3 per job type) | Phase 4 | 36 nodes instead of 12, enables level-aware path queries |
| Single MERGE on job_type only | MERGE on composite {job_type, level} | Phase 4 | Prevents level ambiguity in queries |
| No edge properties in Phase 3 | Rich edge properties (salary, difficulty, skills) | Phase 4 | Phase 8 matching engine can use edge weights |

**Deprecated/outdated:**
- `session.write_transaction()` - deprecated in Neo4j 5.x, replaced by `session.execute_write()`
- `session.read_transaction()` - deprecated, replaced by `session.execute_read()`

---

## Open Questions

1. **Node count gap:** 12 jobs x 3 levels = 36 nodes, well short of 100+. What additional node types should be created?
   - What we know: D-04 says "12岗位×3职级×3个属性节点" suggesting 3 property nodes per level-node.
   - What's unclear: Are these inline property nodes (separate Skill/Company/City nodes linked via relationships)? Or attribute expansions within each node?
   - Recommendation: Create Skill nodes (one per unique core_skill across all profiles) linked to JobProfile nodes. With ~9 core skills per job x 12 jobs, ~50 unique skills creates 50 additional nodes, reaching ~86 total. Add intermediate "JobTitle" nodes per level for 36 more nodes.

2. **Edge count target:** 200+ edges requires dense transition graph. 24 promotion edges + ~176 transition edges needed.
   - What we know: Minimum 2 transitions per job type = 24. With 12 jobs x 3 levels, potential 198 cross-pairs.
   - What's unclear: How many of the 198 pairs will LLM validate as valid transitions?
   - Recommendation: Use LLM batch analysis (10 pairs per call) for all 198 pairs at each level, let LLM filter to valid transitions.

3. **LLM batch strategy:** 198 pairs at 3 levels = 594 potential pairs. Too many for sequential single-pair calls.
   - What we know: DeepSeek API supports batch, Phase 3 used tiktoken for budget.
   - What's unclear: Optimal batch size balancing cost and accuracy.
   - Recommendation: 10 pairs per LLM call = ~60 calls total (20 per level). Within budget for competition project.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Neo4j Python driver | Neo4j connectivity | Yes | 6.1.0 | N/A |
| Python | Script execution | Yes | 3.13.12 | N/A |
| DeepSeek API | LLM analysis | Yes (env var) | API | GLM-4 (if DeepSeek unavailable) |
| neo4j database server | Graph storage | Unknown | - | Check with `bolt://localhost:7687` |
| tiktoken | LLM token counting | Yes | 0.12.0 | N/A |
| pandas | JSON loading | Yes | 2.3.3 | N/A |

**Missing dependencies with no fallback:**
- Neo4j database server - if not running, Phase 4 cannot write graph. Must start Neo4j before execution.

**Missing dependencies with fallback:**
- None identified.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None - manual verification via Cypher queries |
| Config file | N/A |
| Quick run command | `python scripts/build_job_graph.py` (then `cypher-shell` queries) |
| Full suite command | N/A - manual graph verification |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| JOB-02 | Promotion paths exist for all 12 job types (3 levels each) | Manual Cypher | `MATCH (a:JobProfile)-[r:PROMOTES_TO]->(b:JobProfile) RETURN a.job_type, a.level, b.level, r.salary_increase_pct` | N/A |
| JOB-02 | Each promotion path has valid edge properties | Manual Cypher | `MATCH ()-[r:PROMOTES_TO]->() WHERE r.salary_increase_pct IS NULL RETURN count(r)` | N/A |
| JOB-03 | At least 5 job types have >=2 transition paths | Manual Cypher | `MATCH (a:JobProfile)-[r:TRANSITIONS_TO]->(:JobProfile) WITH a.job_type, count(r) as cnt WHERE cnt >= 2 RETURN collect(a.job_type) as jobs_with_2plus` | N/A |
| JOB-03 | All transition edges have required properties | Manual Cypher | `MATCH ()-[r:TRANSITIONS_TO]->() WHERE r.difficulty IS NULL OR r.shared_skills IS NULL RETURN count(r)` | N/A |
| Graph stats | Total nodes >= 100 | Manual Cypher | `MATCH (n) RETURN count(n) as total_nodes` | N/A |
| Graph stats | Total edges >= 200 | Manual Cypher | `MATCH ()-[r]->() RETURN count(r) as total_edges` | N/A |

### Sampling Rate
- **Per task commit:** N/A (manual verification)
- **Per wave merge:** Full graph verification queries
- **Phase gate:** Manual Cypher verification that counts meet targets

### Wave 0 Gaps
- [ ] `scripts/build_job_graph.py` - main graph builder script
- [ ] `data/processed/job_graph_edges.json` - intermediate edge data (optional output)
- None - existing Phase 3 test infrastructure not applicable; graph verification is manual Cypher queries.

---

## Sources

### Primary (HIGH confidence - verified via API inspection)
- `neo4j` Python driver 6.1.0 - `GraphDatabase.driver()`, `session.execute_write()`, `UNWIND` batch operations (verified via `python -c "from neo4j import GraphDatabase; ..."`)
- Context decisions (D-01 through D-09) from `04-CONTEXT.md` - locked decisions

### Secondary (MEDIUM confidence)
- Phase 3 `build_job_profiles.py` - existing Neo4j write patterns (lines 184-223)
- `job_profiles.json` - 12 job profiles with skill data structure
- Cypher patterns - standard MERGE, MATCH, UNWIND syntax (Neo4j universal patterns)

### Tertiary (LOW confidence - needs validation)
- Transition edge count estimate of 198 potential pairs (actual count depends on LLM filtering)
- Node count strategy using Skill nodes and intermediate JobTitle nodes

---

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH - neo4j 6.1.0 verified, all dependencies confirmed
- Architecture: MEDIUM - patterns well-established but node count strategy needs validation
- Pitfalls: MEDIUM - identified gaps (node count, edge count) require empirical validation

**Research date:** 2026-03-30
**Valid until:** 2026-04-29 (30 days - Neo4j driver API stable)
