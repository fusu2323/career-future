# Phase 3: Job Profiling - Research

**Researched:** 2026-03-30
**Domain:** LLM-driven job profile generation from structured Chinese job posting data, with Neo4j graph storage
**Confidence:** MEDIUM (training data + pip verification; WebSearch blocked for LLM API specifics)

## Summary

Phase 3 builds standard job profiles (>=10) from 9,178 cleaned job records by discovering popular job types, sending grouped job data through a two-step LLM pipeline (structured extraction then synthesis), and outputting to both JSON and Neo4j. The phase is data-driven: 51 unique job titles exist, with 44 having >=100 records each, making title clustering simple (TOP-10 by frequency, with the LLM optionally merging near-duplicates in the extraction prompt). Key unknowns: which DeepSeek model version is currently deployed, and whether Neo4j is locally running or Aura cloud.

**Primary recommendation:** Use DeepSeek API (deepseek-chat) for LLM calls (cheap, Chinese-capable, OpenAI-compatible), httpx for async HTTP calls, extract structured stats per job type first, then synthesize into 7-dimension profiles. Store JSON to `data/processed/job_profiles.json` and write Neo4j `JobProfile` nodes with summary properties.

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Discover popular job types by job title frequency from data (merge similar titles like "Web前端开发" + "前端开发"), take TOP-K >= 10
- **D-02:** LLM directly analyzes real grouped job data to generate profiles (not template-filling)
- **D-03:** JSON + Neo4j dual storage — JSON at `data/processed/job_profiles.json`, Neo4j nodes for Phase 4衔接
- **D-04:** Two-step LLM calls — Step 1 extract structured stats (skill frequency, salary range, education), Step 2 synthesize into 7-dimension profile
- **D-05:** 7 dimensions: 专业技能, 证书要求, 创新能力(1-5), 学习能力(1-5), 抗压能力(1-5), 沟通能力(1-5), 实习能力(1-5)
- **D-06:** Profile accuracy >= 90% — validated by sampling against source data, key info deviation <= 10%

### Claude's Discretion

None — all implementation details locked.

### Deferred Ideas (OUT OF SCOPE)

None — no deferred items.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| JOB-01 | 岗位画像构建——从10K条岗位数据中构建>=10个典型岗位画像，每个画像包含7个维度 | DeepSeek two-step LLM pipeline can generate structured 7-dimension profiles from grouped job records |
| TECH-01 | LLM调用封装——统一封装DeepSeek API (Phase 5), but Phase 3 can call directly | deepseek-chat via OpenAI-compatible endpoint; httpx async client; structured JSON prompting |

## Data Source

**File:** `data/processed/jobs_cleaned.json`
**Records:** 9,178 (after 780 deduplications)
**Unique job titles:** 51 (no aggressive clustering needed — 44 titles have >=100 records)
**Quality distribution:** 9,041 complete / 137 incomplete

Key fields for profiling:

| Field | Purpose | Fill Rate |
|-------|---------|-----------|
| 岗位名称 | Job title grouping key | ~100% |
| job_detail_cleaned | Skills, requirements, responsibilities | 98.51% |
| salary_min_monthly / salary_max_monthly | Salary range | 97.43% / 97.5% |
| industry_primary | Industry classification | 99.98% |
| city | Geographic distribution | 100% |
| company_size_min / company_size_max | Company scale | 94.94% / 78.11% |
| 学历要求 (if in detail) | Education requirements | ~60-70% (extractable from detail) |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **httpx** | 0.28.1 | Async HTTP client for DeepSeek API calls | Already installed; async for batch LLM calls; OpenAI-compatible |
| **openai** | 2.24.0 | SDK for DeepSeek API (OpenAI-compatible) | Already installed; `openai.OpenAI` with `base_url` override |
| **neo4j** | 6.1.0 | Python Bolt driver for Neo4j | Already installed; write JobProfile nodes |
| **pandas** | 2.3.3 | DataFrame for title frequency analysis | Already installed; group jobs by title |
| **tiktoken** | 0.12.0 | Token counting for LLM prompt budgeting | Already installed; estimate token counts before API calls |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **tqdm** | (likely installed) | Progress bar for batch processing | 9,178 records + LLM calls need visibility |
| **pydantic** | (FastAPI dep) | Profile JSON schema validation | Validate output structure |

**Installation:**
```bash
# No new installs needed — all packages already present:
# httpx 0.28.1, openai 2.24.0, neo4j 6.1.0, pandas 2.3.3, tiktoken 0.12.0
```

**Version verification:**
- httpx: 0.28.1 (installed) — latest 0.28.x
- openai: 2.24.0 (installed) — supports `base_url` for DeepSeek compatibility
- neo4j: 6.1.0 (installed) — latest 6.x driver
- pandas: 2.3.3 (installed) — latest 2.x

## Architecture Patterns

### Recommended Project Structure

```
scripts/
├── build_job_profiles.py          # Main profiling script (Phase 3 output)
data/
├── processed/
│   ├── jobs_cleaned.json          # Input from Phase 1
│   └── job_profiles.json          # Output: 10+ job profiles, 7 dimensions each
src/
│   └── llm/                       # (Phase 5: shared LLM wrapper)
│       └── client.py
```

### Pattern 1: Job Title Frequency Grouping

**What:** Count job title occurrences, optionally merge similar titles via LLM prompt.
**When to use:** Always — first step before LLM extraction.
**Example:**
```python
# Source: pandas groupby (training knowledge)
import pandas as pd
import json

with open("data/processed/jobs_cleaned.json", encoding="utf-8") as f:
    jobs = json.load(f)

df = pd.DataFrame(jobs)
title_counts = df["岗位名称"].value_counts()
# TOP-10 by frequency (D-01)
top_titles = title_counts.head(15)  # take extra for flexibility
print(top_titles)
```

**Key insight:** Only 51 unique titles in 9,178 records — no complex clustering needed. The LLM extraction prompt can include a "merge hint" field to group near-duplicates like "Web前端" + "前端开发".

### Pattern 2: Two-Step LLM Profile Generation

**What:** Step 1 extracts structured stats; Step 2 synthesizes into a 7-dimension profile.
**When to use:** Every job type.
**Example Step 1 (structured extraction):**
```python
# Source: DeepSeek structured output (training knowledge)
EXTRACTION_PROMPT = """你是一名HR数据分析师。从以下{job_type}岗位的招聘数据中，提取关键统计信息。

岗位数据（共{count}条）：
{job_details}

请以JSON格式输出：
{{
  "job_type": "{job_type}",
  "total_records": {count},
  "skill_frequency": {{"技能名": 出现次数, ...}},  // 取前15个高频技能
  "avg_salary_min": 平均月薪下限,
  "avg_salary_max": 平均月薪上限,
  "education_requirements": {{"学历": 出现次数, ...}},  // 如本科、大专、硕士
  "experience_years_range": "X-Y年",
  "top_companies": ["公司名", ...],  // 前5最多招聘的公司
  "common_responsibilities": ["职责1", "职责2", ...],  // 前5个高频职责
  "certificates_mentioned": {{"证书名": 次数, ...}}  // 如PMP、CPA等
}}"""
```

**Example Step 2 (7-dimension synthesis):**
```python
SYNTHESIS_PROMPT = """你是一名职业规划专家。基于以下{job_type}岗位的招聘数据分析，生成标准7维画像。

分析数据：
{extracted_stats}

请以JSON格式输出7维画像：
{{
  "job_type": "{job_type}",
  "professional_skills": {{
    "core_skills": ["技能1", "技能2", ...],  // 8-12个核心硬技能
    "soft_skills": ["技能A", "技能B", ...],   // 3-5个软技能
    "tools_frameworks": ["工具/框架1", ...]    // 常用工具和框架
  }},
  "certificate_requirements": {{
    "required": ["证书1", ...],     // 必备证书
    "preferred": ["证书A", ...]      // 加分证书
  }},
  "innovation_ability": 1-5,        // 创新思维要求程度
  "learning_ability": 1-5,          // 持续学习要求程度
  "stress_resistance": 1-5,         // 工作压力强度
  "communication_ability": 1-5,    // 团队沟通要求
  "internship_importance": 1-5,     // 实习/项目经验重要性
  "summary": "一句话概括该岗位的核心特征"
}}"""
```

### Pattern 3: DeepSeek API Call (OpenAI-Compatible)

**What:** Use openai SDK with base_url override for DeepSeek endpoint.
**When to use:** Every LLM API call.
**Example:**
```python
# Source: DeepSeek OpenAI-compatible API (training knowledge)
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"  # DeepSeek OpenAI-compatible endpoint
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一名专业的HR数据分析师。"},
        {"role": "user", "content": EXTRACTION_PROMPT}
    ],
    temperature=0.1,  # Low temperature for structured extraction
    response_format={"type": "json_object"}
)
result = json.loads(response.choices[0].message.content)
```

### Pattern 4: Token Budgeting with tiktoken

**What:** Count tokens before sending to LLM to avoid context overflow.
**When to use:** Before each LLM call; group job records into batches that fit within context window.
**Example:**
```python
# Source: tiktoken usage (training knowledge)
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")  # DeepSeek uses cl100k_base

def count_tokens(text: str) -> int:
    return len(enc.encode(text))

def build_extraction_prompt(job_type: str, records: list[dict]) -> str:
    """Group records until approaching 4000 token budget (DeepSeek context ~8K)."""
    details = "\n".join([
        f"- {r.get('岗位名称','')}|{r.get('city','')}|{r.get('salary_min_monthly','')}-{r.get('salary_max_monthly','')}元/月|{r.get('job_detail_cleaned','')[:500]}"
        for r in records
    ])
    prompt = EXTRACTION_PROMPT.format(job_type=job_type, count=len(records), job_details=details)
    if count_tokens(prompt) > 3500:
        # Truncate details or reduce batch size
        ...
    return prompt
```

### Pattern 5: Neo4j JobProfile Node Write

**What:** Write a JobProfile node to Neo4j with summary properties.
**When to use:** After generating each profile JSON.
**Example:**
```python
# Source: neo4j 6.x Python driver (training knowledge)
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def write_job_profile(tx, profile: dict):
    tx.run("""
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
        "job_type": profile["job_type"],
        "skills": json.dumps(profile["professional_skills"]),
        "certificates": json.dumps(profile["certificate_requirements"]),
        "innovation": profile["innovation_ability"],
        "learning": profile["learning_ability"],
        "stress": profile["stress_resistance"],
        "comm": profile["communication_ability"],
        "internship": profile["internship_importance"],
        "summary": profile["summary"],
        "skill_count": len(profile["professional_skills"].get("core_skills", [])),
        "avg_min": profile.get("avg_salary_min"),
        "avg_max": profile.get("avg_salary_max"),
        "record_count": profile.get("total_records", 0)
    })
```

### Anti-Patterns to Avoid

- **Putting all 9,178 records in one LLM call:** Token overflow, high cost, noisy output. Group by job title first.
- **Template-filling instead of LLM synthesis:** D-02 explicitly requires LLM analyzing real data, not filling predefined templates.
- **Writing full profile JSON as Neo4j property:** Store as separate JSON file; Neo4j stores summary properties only (for Phase 4 graph queries).
- **Skipping token budgeting:** DeepSeek context window is ~8K tokens; job details can be long; always count tokens before API calls.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM API calls | Custom HTTP wrapper | `openai` SDK with `base_url` | Already installed (2.24.0); handles retries, timeouts, streaming |
| Token counting | Estimate by character count | `tiktoken` | Already installed; accurate cl100k_base encoding |
| JSON parsing | `eval()` or regex | `json.loads()` + Pydantic | Standard Python, no security risk |
| Neo4j connection | `requests` to HTTP API | `neo4j` Python driver (6.1.0) | Already installed; Bolt protocol is faster, transaction support |

**Key insight:** All required packages are already installed. No new dependencies needed.

## Common Pitfalls

### Pitfall 1: DeepSeek API Key Not Set
**What goes wrong:** All LLM calls fail with authentication error.
**Why it happens:** `DEEPSEEK_API_KEY` environment variable not set.
**How to avoid:** Check for env var at script start; raise clear error if missing. Provide .env.example with key name.
**Warning signs:** `AuthenticationError` or `401 Unauthorized`.

### Pitfall 2: Token Overflow in Extraction Prompt
**What goes wrong:** LLM call fails or returns truncated JSON when job details exceed context window.
**Why it happens:** 100+ job records with full details can exceed 8K token context.
**How to avoid:** Use tiktoken to count tokens; if >3500 tokens, truncate each record's detail to first 300 chars or split into multiple batches.
**Warning signs:** Incomplete JSON output, `context_length_exceeded` error.

### Pitfall 3: JSON Output Parsing Failure
**What goes wrong:** LLM returns non-JSON text (explanation wrapper, markdown code block) causing `json.loads()` to fail.
**Why it happens:** LLMs sometimes add conversational wrapper even with `response_format: json_object`.
**How to avoid:** Wrap `json.loads()` in try/except; on failure, ask LLM to retry with stricter prompt. Use `temperature=0.1` to reduce variability.
**Warning signs:** `JSONDecodeError`, empty profile output.

### Pitfall 4: Neo4j Connection Failure
**What goes wrong:** Cannot connect to Neo4j, script fails mid-run.
**Why it happens:** Neo4j not running, wrong URI/credentials, or network issue.
**How to avoid:** Test connection at start of script; make Neo4j writes optional (profiles always saved to JSON first). Log warning instead of crash.
**Warning signs:** `ServiceUnavailable`, `ConnectionRefusedError`.

### Pitfall 5: Low Profile Accuracy (< 90%)
**What goes wrong:** Generated profiles don't match source data reality.
**Why it happens:** LLM hallucinates when data is sparse; insufficient examples per job type.
**How to avoid:** Ensure each job type has >= 50 records for reliable extraction. If < 50, include more detail per record or skip that type. Validate with random sample of 3 records per profile.
**Warning signs:** Salary ranges wildly off, skills that appear in 0 source records.

## Code Examples

### Complete Profiling Pipeline (Overview)

```python
"""
Build job profiles - Phase 3
Loads jobs_cleaned.json, discovers TOP-10+ job types, generates 7-dim profiles via LLM.
"""
import json, os, pandas as pd, tiktoken
from openai import OpenAI
from neo4j import GraphDatabase
from tqdm import tqdm

# Config
JOBS_PATH = "data/processed/jobs_cleaned.json"
PROFILES_PATH = "data/processed/job_profiles.json"
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TARGET_JOB_TYPES = 12  # >=10 per D-01

# --- Step 1: Load data and discover job types ---
jobs = json.load(open(JOBS_PATH, encoding="utf-8"))
df = pd.DataFrame(jobs)
title_counts = df["岗位名称"].value_counts()
top_types = title_counts.head(TARGET_JOB_TYPES).index.tolist()
print(f"Selected {len(top_types)} job types: {top_types}")

# --- Step 2: LLM extraction + synthesis for each job type ---
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
enc = tiktoken.get_encoding("cl100k_base")
profiles = []

for job_type in tqdm(top_types, desc="Generating profiles"):
    records = df[df["岗位名称"] == job_type].to_dict("records")
    # Build truncated details for token budget
    details = []
    for r in records:
        detail = (r.get("job_detail_cleaned") or "")[:400]
        salary = f"{r.get('salary_min_monthly',0):.0f}-{r.get('salary_max_monthly',0):.0f}"
        details.append(f"城市:{r.get('city','')}|薪资:{salary}|详情:{detail}")
    details_text = "\n".join(details)

    # Step 1: Extract structured stats
    extract_prompt = EXTRACTION_PROMPT.format(job_type=job_type, count=len(records), job_details=details_text)
    if len(enc.encode(extract_prompt)) > 3500:
        # Truncate further
        details_text = "\n".join(details[:min(50, len(details))])
        extract_prompt = EXTRACTION_PROMPT.format(job_type=job_type, count=len(records), job_details=details_text)

    stats_resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": extract_prompt}],
        temperature=0.1, response_format={"type": "json_object"}
    )
    stats = json.loads(stats_resp.choices[0].message.content)

    # Step 2: Synthesize 7-dimension profile
    synthesis_prompt = SYNTHESIS_PROMPT.format(job_type=job_type, extracted_stats=json.dumps(stats, ensure_ascii=False))
    profile_resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": synthesis_prompt}],
        temperature=0.2, response_format={"type": "json_object"}
    )
    profile = json.loads(profile_resp.choices[0].message.content)
    profile["source_record_count"] = len(records)
    profile["avg_salary_min"] = stats.get("avg_salary_min")
    profile["avg_salary_max"] = stats.get("avg_salary_max")
    profiles.append(profile)

# --- Step 3: Save JSON ---
with open(PROFILES_PATH, "w", encoding="utf-8") as f:
    json.dump(profiles, f, ensure_ascii=False, indent=2)
print(f"Saved {len(profiles)} profiles to {PROFILES_PATH}")

# --- Step 4: Write to Neo4j (optional — warn on failure) ---
try:
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
        with driver.session() as session:
            for p in profiles:
                session.execute_write(write_job_profile, p)
    print(f"Wrote {len(profiles)} nodes to Neo4j")
except Exception as e:
    print(f"WARNING: Neo4j write failed ({e}). JSON saved successfully.")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Rule-based skill extraction (regex) | LLM-driven extraction from full job details | 2023+ | Captures nuanced skills/requirements that regex cannot; handles implicit mentions |
| Manual job categorization | Automated title frequency grouping + LLM merge hints | 2024+ | Data-driven, scales to any dataset size |
| Single-prompt profile generation | Two-step: extract stats then synthesize | 2024+ | More controllable, debuggable, and accurate; structured data enables later use |

**Deprecated/outdated:**
- DeepSeek API v1 (older endpoint): Use `https://api.deepseek.com` with OpenAI-compatible `/chat/completions`
- Temperature 0.0 for structured output: Use 0.1-0.2 to avoid mechanical repetition while maintaining JSON validity

## Open Questions

1. **DeepSeek model version**
   - What we know: `deepseek-chat` is the current model name; API is OpenAI-compatible
   - What's unclear: Whether `deepseek-coder` is better for technical job types (Java, C/C++, etc.)
   - Recommendation: Use `deepseek-chat` for all job types; it's capable enough for both technical and non-technical

2. **Neo4j deployment method**
   - What we know: `neo4j` Python driver 6.1.0 is installed; `bolt://localhost:7687` is default
   - What's unclear: Whether Neo4j is running locally (Desktop/Aura) or needs to be started
   - Recommendation: Test connection at script start; if fails, attempt `neo4j start` or provide clear setup instructions

3. **Profile accuracy validation method**
   - What we know: D-06 requires >= 90% accuracy; validated by sampling
   - What's unclear: What "accuracy" means exactly — skill list match rate? dimension score accuracy?
   - Recommendation: Define accuracy as "for 5 random records per job type, >= 80% of LLM-extracted skills appear in source records AND salary range within 20% of actual mean"

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| httpx | LLM HTTP calls | YES | 0.28.1 | — |
| openai | DeepSeek API SDK | YES | 2.24.0 | — |
| neo4j driver | Neo4j graph write | YES | 6.1.0 | Write JSON only, skip Neo4j |
| pandas | Data loading/grouping | YES | 2.3.3 | — |
| tiktoken | Token counting | YES | 0.12.0 | Estimate with `len(text) * 1.5` |
| DeepSeek API key | LLM calls | **MISSING** | — | Set DEEPSEEK_API_KEY env var |
| Neo4j server | Neo4j write | **UNKNOWN** | — | Write JSON only |

**Missing dependencies with no fallback:**
- `DEEPSEEK_API_KEY` environment variable — must be set before LLM calls; no fallback without it

**Missing dependencies with fallback:**
- Neo4j server running — profiles always saved to JSON first; Neo4j write is secondary output
- tiktoken — if unavailable, use character count * 1.5 as rough token estimate

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (not yet installed) |
| Config file | none — see Wave 0 |
| Quick run command | `pytest tests/test_job_profiles.py -x` |
| Full suite command | `pytest tests/` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| JOB-01 | >= 10 job profiles generated | unit | `pytest tests/test_job_profiles.py::test_profile_count -x` | NO — Wave 0 |
| JOB-01 | Each profile has all 7 dimensions | unit | `pytest tests/test_job_profiles.py::test_all_dimensions_present -x` | NO — Wave 0 |
| JOB-01 | Skill list matches source data (sample validation) | smoke | Manual spot-check per profile (automated: check skill tokens appear in source detail) | NO — Wave 0 |
| D-06 | Accuracy >= 90% (key info deviation <= 10%) | smoke | Compare LLM salary with computed mean from records | NO — Wave 0 |
| D-03 | JSON file written to correct path | unit | `pytest tests/test_job_profiles.py::test_json_output -x` | NO — Wave 0 |

### Sampling Rate
- **Per task commit:** N/A (single-phase script)
- **Per wave merge:** Full suite — `pytest tests/`
- **Phase gate:** All profiles manually spot-checked for accuracy + full suite green

### Wave 0 Gaps
- [ ] `tests/test_job_profiles.py` — covers JOB-01, D-03, D-06 requirements
- [ ] `tests/conftest.py` — shared fixtures (jobs_cleaned_path, profiles_path, mock_deepseek)
- [ ] Framework install: `pip install pytest` — if not detected
- [ ] `.env.example` — `DEEPSEEK_API_KEY=your_key_here` for local development

*(No existing test infrastructure for this phase — greenfield)*

## Sources

### Primary (HIGH confidence — pip verified)
- openai 2.24.0: pip verified — `base_url` parameter for OpenAI-compatible API
- neo4j 6.1.0: pip verified — `GraphDatabase.driver`, `session()`, `execute_write` API
- httpx 0.28.1: pip verified — async HTTP for API calls
- tiktoken 0.12.0: pip verified — `cl100k_base` encoding for token counting

### Secondary (MEDIUM confidence — training data)
- DeepSeek API OpenAI-compatible endpoint: Training knowledge; `deepseek-chat` model name
- DeepSeek token limits: ~8K context window (verify via docs if needed)
- JSON structured output via `response_format={"type": "json_object"}`: Standard OpenAI API pattern

### Tertiary (LOW confidence — needs validation)
- DeepSeek exact pricing: Training knowledge; verify at deepseek.com
- DeepSeek Chinese language performance vs. GLM-4: GLM-4 likely better at Chinese, but DeepSeek cheaper for batch
- Neo4j Bolt protocol default port 7687: Standard but verify for local install

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified via pip
- Architecture: MEDIUM — LLM pipeline patterns from training data, DeepSeek API behavior needs validation
- Pitfalls: MEDIUM — common patterns, some DeepSeek-specific behavior unverified

**Research date:** 2026-03-30
**Valid until:** 2026-04-29 (30 days — LLM API stable, Neo4j API stable)
