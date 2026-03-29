# Phase 2: Job Vector DB - Research

**Researched:** 2026-03-29
**Domain:** ChromaDB vector indexing + BGE-large-zh embedding for Chinese job postings
**Confidence:** MEDIUM (training data verified via pip index; WebSearch/WebFetch blocked by network policy)

## Summary

Phase 2 builds a ChromaDB vector index on 9,178 cleaned job records to enable semantic search with Top10 accuracy >=85%. The locked decisions specify BGE-large-zh embedding (FlagEmbedding), concatenated full-record text preparation, ChromaDB native metadata filtering, and HNSW ANN retrieval. This phase is a prerequisite for Phase 3 (job profiling) and Phase 8 (person-job matching).

Key implementation steps: (1) install chromadb 1.5.x and FlagEmbedding 1.3.x, (2) load jobs_cleaned.json, (3) build concatenated text per record, (4) encode with BGE-large-zh (~1024 dimensions), (5) create ChromaDB collection `job_postings` with metadata, (6) batch-insert 9,178 vectors, (7) validate Top10 recall via spot-check queries.

**Primary recommendation:** Use FlagEmbedding's BGEM3FlagModel with explicit `max_length=512` to control memory, batch encode all 9,178 records, persist ChromaDB to `data/vector_db/`.

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Embedding = BGE-large-zh (FlagEmbedding), ~1024 dimensions
- **D-02:** Text = concatenated full record: `{job_title} | {company_name} | {industry_tags} | {job_detail}`
- **D-03:** Metadata filtering = ChromaDB native `where` clause on city, salary range, industry
- **D-04:** Retrieval = Pure vector ANN with HNSW index (ChromaDB default)
- **D-05:** Collection name = `job_postings`; metadata fields: job_id, title, company_name, city, district, industry_primary, salary_min_monthly, salary_max_monthly, company_size_min, company_size_max; display text field: `text`
- **D-06:** Input = `data/processed/jobs_cleaned.json`; Output = `job_postings` collection (~9,178 vectors)

### Claude's Discretion

None — all implementation details are locked.

### Deferred Ideas (OUT OF SCOPE)

None — no deferred items.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TECH-02 | ChromaDB向量索引——将岗位详情、岗位画像、简历文本向量化，支持语义检索 | BGE-large-zh + ChromaDB HNSW provides semantic vector search on job_postings collection |
| ROADMAP-REQ | 向量召回Top10相关岗位准确率>=85% | BGE-large-zh is best-in-class for Chinese semantic matching; HNSW index provides high recall at 10K scale |
| ROADMAP-REQ | 支持按技能关键词/岗位名称/行业多维度检索 | ChromaDB metadata `where` clause enables city/industry/salary pre-filtering before vector search |

## Data Source

**File:** `data/processed/jobs_cleaned.json`
**Records:** 9,178 (after deduplication of 780 duplicate job codes)
**Quality:** 9,041 complete / 137 incomplete (missing job_detail_cleaned)

Key fields used for embedding:

| Field (Chinese) | Field (English in JSON) | Fill Rate |
|-----------------|------------------------|-----------|
| 岗位名称 | title (via 岗位名称) | ~100% |
| 公司名称 | company_name | ~100% |
| 行业标签 | industry_tags (list) | 99.98% |
| 岗位详情清洗 | job_detail_cleaned | 98.51% |
| 城市 | city | 100% |
| 区域 | district | 96.61% |
| 薪资下限 | salary_min_monthly | 97.43% |
| 薪资上限 | salary_max_monthly | 97.5% |
| 公司规模下限 | company_size_min | 94.94% |
| 公司规模上限 | company_size_max | 78.11% |
| 行业主分类 | industry_primary | 99.98% |
| 岗位编码 | (used as job_id) | ~100% |

**Text concatenation format (D-02):**
```
{岗位名称} | {公司名称} | {industry_tags joined by comma} | {job_detail_cleaned}
```
Example: `"前端开发 | 东莞市恒亚罗斯计算机科技有限公司 | 计算机软件,互联网,IT服务 | 1.负责公司项目web前端页面的设计和开发..."`

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **chromadb** | 1.5.5 (installed: 1.5.2) | Vector database with HNSW index | Project constraint per CLAUDE.md and CONTEXT; simple API, sufficient for <100K vectors |
| **FlagEmbedding** | 1.3.5 | BGE-large-zh embedding model | Best Chinese semantic matching per CONTEXT D-01; open-source,FlagOpen maintained |
| **sentence-transformers** | 5.3.0 (installed) | Model loading backend for FlagEmbedding | Required by FlagEmbedding; already installed |
| **numpy** | (dependency) | Array operations for embeddings | Required for vector manipulation |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **tqdm** | (common) | Progress bar for batch encoding | 9,178 records need progress visibility |
| **pandas** | (existing) | Load JSON and inspect data | Reuse from Phase 1 |

**Installation:**
```bash
pip install chromadb==1.5.5 FlagEmbedding==1.3.5
# sentence-transformers already installed (5.3.0)
```

**Version verification:**
- chromadb latest: 1.5.5 (installed 1.5.2 — upgrade recommended)
- FlagEmbedding latest: 1.3.5 (not installed — install required)
- sentence-transformers: 5.3.0 (already installed)

## Architecture Patterns

### Recommended Project Structure

```
scripts/
├── build_job_vector_db.py   # Main indexing script (Phase 2 output)
data/
├── processed/
│   ├── jobs_cleaned.json    # Input from Phase 1
│   └── cleaning_report.json
└── vector_db/               # ChromaDB persist directory
    └── chroma.sqlite        # SQLite-backed ChromaDB
src/                         # (future Phase 5+ FastAPI integration)
```

### Pattern 1: Batch Embedding with Progress

**What:** Encode job records in batches with a progress bar to handle memory constraints.
**When to use:** 9,178 records x BGE-large-zh (~1024 dims) requires batch processing.
**Example:**
```python
# Source: FlagEmbedding best practice (training knowledge)
from FlagEmbedding import BGEM3FlagModel
import tqdm

model = BGEM3FlagModel("BAAI/bge-large-zh-v1.5", use_fp16=True)

BATCH_SIZE = 32  # Balance memory vs. speed
embeddings = []
for i in tqdm(range(0, len(texts), BATCH_SIZE)):
    batch = texts[i:i+BATCH_SIZE]
    # max_length=512 to control memory; longer docs are truncated
    encoded = model.encode(batch, max_length=512, batch_size=len(batch))
    embeddings.extend(encoded["dense_vecs"])
```

### Pattern 2: ChromaDB Collection Creation with Metadata

**What:** Create a ChromaDB collection with specific metadata schema, persist to disk.
**When to use:** Initial index build and any re-indexing.
**Example:**
```python
# Source: ChromaDB 1.x API (training knowledge)
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(path="data/vector_db")

collection = client.create_collection(
    name="job_postings",
    metadata={"hnsw:space": "cosine"}  # cosine similarity for semantic search
)

# Add records
collection.add(
    ids=[record["job_id"] for record in records],
    embeddings=embeddings,  # list of lists, shape (9178, 1024)
    documents=[record["text"] for record in records],  # concatenated display text
    metadatas=[{
        "job_id": record["job_id"],
        "title": record["title"],
        "company_name": record["company_name"],
        "city": record["city"],
        "district": record.get("district"),
        "industry_primary": record["industry_primary"],
        "salary_min_monthly": record.get("salary_min_monthly"),
        "salary_max_monthly": record.get("salary_max_monthly"),
        "company_size_min": record.get("company_size_min"),
        "company_size_max": record.get("company_size_max"),
    } for record in records]
)
```

### Pattern 3: Vector Query with Metadata Pre-filtering

**What:** Query vectors with optional metadata filtering using ChromaDB's `where` clause.
**When to use:** Semantic search with city/industry/salary constraints.
**Example:**
```python
# Source: ChromaDB 1.x API (training knowledge)
results = collection.query(
    query_embeddings=[query_vector],
    n_results=10,
    where={"city": "广州", "industry_primary": "计算机软件"},  # optional pre-filter
    include=["distances", "metadatas", "documents"]
)
```

### Pattern 4: Text Concatenation for Full-Record Embedding

**What:** Concatenate title, company, industry tags, and job detail into a single text string.
**When to use:** Every record during index build.
**Example:**
```python
def build_job_text(record):
    """Concatenate full record per D-02."""
    title = record.get("岗位名称", "")
    company = record.get("公司名称", "")
    industries = ",".join(record.get("industry_tags", []))
    detail = record.get("job_detail_cleaned", "")
    return f"{title} | {company} | {industries} | {detail}"
```

### Anti-Patterns to Avoid

- **Embedding each field separately:** Complexity without benefit at 10K scale (per D-02 decision)
- **Using IVF-PQ index:** Over-engineered for 9,178 vectors; HNSW default is sufficient
- **Storing full company_details in vector text:** Way too long, would dominate semantic signal; use job_detail_cleaned only
- **Loading all 9,178 vectors into memory at once:** Risk OOM with BGE-large-zh; use batch encoding

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Chinese text embedding | Custom tokenizer + model | FlagEmbedding BGE-large-zh | Best-in-class Chinese semantic matching, open-source, maintained |
| Vector index | Custom ANN implementation | ChromaDB HNSW | Project constraint; sufficient for 10K scale; production-ready |
| Batch encoding | Manual loop | FlagModel.encode() with batch_size | Memory-efficient, faster, built-in progress |

**Key insight:** The stack is fully specified by locked decisions. No alternatives should be explored.

## Common Pitfalls

### Pitfall 1: BGE-large-zh OOM on Full Corpus
**What goes wrong:** Encoding all 9,178 records in a single call exhausts GPU/CPU memory.
**Why it happens:** BGE-large-zh-v1.5 produces 1024-dim vectors; large batch without max_length control uses excessive memory.
**How to avoid:** Use `max_length=512` truncation + batch_size=32. If OOM persists, reduce to batch_size=16.
**Warning signs:** `CUDA out of memory` or `MemoryError` during encoding.

### Pitfall 2: ChromaDB Client Path Not Created
**What goes wrong:** `chromadb.PersistentClient(path=...)` fails if parent directories don't exist.
**Why it happens:** ChromaDB does not auto-create parent directories.
**How to avoid:** Use `Path("data/vector_db").mkdir(parents=True, exist_ok=True)` before creating client.
**Warning signs:** `InvalidDirError` or `FileNotFoundError` on client creation.

### Pitfall 3: Duplicate IDs on Re-run
**What goes wrong:** Re-running the script attempts to insert records with the same IDs, causing ChromaDB to reject duplicates.
**Why it happens:** ChromaDB requires unique IDs; re-running without clearing the collection fails.
**How to avoid:** Either `client.delete_collection("job_postings")` before re-building, or check if collection exists and skip/confirm.
**Warning signs:** `UniqueConstraintError` or `id already exists` exception.

### Pitfall 4: Missing Metadata Fields Cause Type Errors
**What goes wrong:** Passing `None` for metadata fields (e.g., `district=null`) causes ChromaDB to reject the record.
**Why it happens:** ChromaDB metadata does not accept null values in the 1.x client.
**How to avoid:** Omit fields that are None from the metadata dict rather than including `None` values. Use `if value is not None` guard.
**Warning signs:** `MetadataException` or `Expected metadata value to be non-null` error.

### Pitfall 5: Low Recall Due to Short Queries
**What goes wrong:** Very short queries (e.g., single keyword "Java") return poor results because cosine similarity on truncated short text is noisy.
**Why it happens:** BGE-large-zh is optimized for sentences/paragraphs; single words lack context.
**How to avoid:** Pad short queries with context (e.g., "Java开发工程师") before embedding. Document this in API usage notes.
**Warning signs:** Spot-check queries returning obviously irrelevant jobs.

## Code Examples

### Complete Index Build Pipeline

```python
"""
Build job vector index - Phase 2
Loads jobs_cleaned.json, embeds with BGE-large-zh, stores in ChromaDB.
"""
import json
from pathlib import Path
from FlagEmbedding import BGEM3FlagModel
import chromadb

# Config
JOBS_CLEANED_PATH = "data/processed/jobs_cleaned.json"
VECTOR_DB_PATH = "data/vector_db"
COLLECTION_NAME = "job_postings"
BATCH_SIZE = 32
MAX_LENGTH = 512


def load_jobs(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_job_text(record):
    """Concatenate full record per D-02."""
    title = record.get("岗位名称", "")
    company = record.get("公司名称", "")
    industries = ",".join(record.get("industry_tags", []) or [])
    detail = record.get("job_detail_cleaned", "") or ""
    return f"{title} | {company} | {industries} | {detail}"


def build_metadata(record):
    """Build metadata dict, omitting None values (ChromaDB requirement)."""
    meta = {
        k: v for k, v in {
            "job_id": record.get("岗位编码"),
            "title": record.get("岗位名称"),
            "company_name": record.get("公司名称"),
            "city": record.get("city"),
            "district": record.get("district"),
            "industry_primary": record.get("industry_primary"),
            "salary_min_monthly": record.get("salary_min_monthly"),
            "salary_max_monthly": record.get("salary_max_monthly"),
            "company_size_min": record.get("company_size_min"),
            "company_size_max": record.get("company_size_max"),
        }.items() if v is not None
    }
    return meta


def main():
    # Load data
    jobs = load_jobs(JOBS_CLEANED_PATH)
    print(f"Loaded {len(jobs)} job records")

    # Build texts
    texts = [build_job_text(j) for j in jobs]
    job_ids = [j.get("岗位编码") for j in jobs]
    metadatas = [build_metadata(j) for j in jobs]

    # Encode in batches
    print("Loading BGE-large-zh model...")
    model = BGEM3FlagModel("BAAI/bge-large-zh-v1.5", use_fp16=True)

    print("Encoding job texts...")
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        encoded = model.encode(batch, max_length=MAX_LENGTH, batch_size=len(batch))
        all_embeddings.extend(encoded["dense_vecs"])
        print(f"  Encoded {min(i + BATCH_SIZE, len(texts))}/{len(texts)}")

    # Persist ChromaDB
    Path(VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

    # Delete existing collection if present (safe re-run)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    print("Inserting vectors into ChromaDB...")
    collection.add(
        ids=job_ids,
        embeddings=all_embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    print(f"Indexed {collection.count()} records in collection '{COLLECTION_NAME}'")


if __name__ == "__main__":
    main()
```

### Spot-Check Validation Query

```python
"""Spot-check Top10 recall accuracy."""
model = BGEM3FlagModel("BAAI/bge-large-zh-v1.5", use_fp16=True)
client = chromadb.PersistentClient(path="data/vector_db")
collection = client.get_collection("job_postings")

# Known relevant queries (human-judged)
test_queries = [
    ("前端开发 JavaScript React", ["前端开发", "Web前端", "前端工程师"]),
    ("Java后端开发 Spring微服务", ["Java", "后端开发", "Java开发"]),
    ("产品经理 Axure 需求分析", ["产品经理", "PM"]),
    ("数据分析 Python SQL pandas", ["数据分析", "数据分析师", "BI"]),
]

correct = 0
total = 0
for query, expected_keywords in test_queries:
    q_vec = model.encode([query], max_length=512)["dense_vecs"][0]
    results = collection.query(query_embeddings=[q_vec], n_results=10)
    titles = [m["title"] for m in results["metadatas"][0]]
    # Count how many Top10 results contain any expected keyword
    hits = sum(1 for t in titles if any(kw in t for kw in expected_keywords))
    recall = hits / 10
    correct += hits
    total += 10
    print(f"Query: '{query}' -> Recall@10: {recall:.0%} (hits={hits})")

print(f"\nOverall spot-check recall: {correct}/{total} = {correct/total:.1%}")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| BM25 keyword search | Dense vector semantic search (BGE-large-zh) | 2023+ | Captures semantic similarity beyond keyword matching; critical for Chinese job matching |
| Separate field embedding | Concatenated full-record embedding | 2024+ | Simpler pipeline, sufficient for 10K scale; avoids complex multi-vector fusion |
| IVF-PQ quantization | HNSW (ChromaDB default) | 2020+ | HNSW offers better recall/precision trade-off at this scale; no quantization loss |

**Deprecated/outdated:**
- ChromaDB 0.4.x client API: `chroma.Client()` → use `chromadb.PersistentClient`
- FlagEmbedding 1.0.x `FlagModel` class → use `BGEM3FlagModel` (1.2+)

## Open Questions

1. **BGE-large-zh model variant selection**
   - What we know: `BAAI/bge-large-zh-v1.5` is current best; variants include `bge-large-zh` (v1.0) and `bge-multilingual`
   - What's unclear: Whether v1.5 is available on HuggingFace (should verify before coding)
   - Recommendation: Use v1.5 as specified; add fallback to v1.0 if model not found

2. **HNSW index parameters**
   - What we know: ChromaDB defaults (M=16, efConstruction=200) work well at 10K scale
   - What's unclear: Whether any tuning needed for better Top10 recall
   - Recommendation: Use defaults for now; if recall < 85%, tune `ef` (search) parameter

3. **CPU vs GPU encoding**
   - What we know: BGE-large-zh supports both; `use_fp16=True` requires CUDA for speed
   - What's unclear: Whether GPU is available on target machine
   - Recommendation: Code with `use_fp16=True` (auto-falls back to CPU if no CUDA); add flag to override

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | YES | 3.13.12 | — |
| pip | Package install | YES | 26.0.1 | — |
| chromadb | Vector DB | **NO** (1.5.2 installed, need 1.5.5) | 1.5.2 (outdated) | — |
| FlagEmbedding | BGE-large-zh | **NO** (not installed) | — | — |
| sentence-transformers | FlagEmbedding backend | YES | 5.3.0 | — |
| CUDA/GPU | Fast encoding | Unknown | — | CPU fallback |

**Missing dependencies with no fallback:**
- `chromadb>=1.5.5` — required for latest HNSW improvements; upgrade pip install
- `FlagEmbedding==1.3.5` — required for BGE-large-zh; fresh install

**Missing dependencies with fallback:**
- CUDA GPU — FlagEmbedding `use_fp16=True` auto-falls back to CPU if no GPU; encoding will be slower but functional

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (not yet installed) |
| Config file | none — see Wave 0 |
| Quick run command | `pytest tests/test_vector_db.py -x` |
| Full suite command | `pytest tests/` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TECH-02 | ChromaDB collection `job_postings` exists with 9,178 vectors | unit | `pytest tests/test_vector_db.py::test_collection_exists -x` | NO — Wave 0 |
| TECH-02 | Query returns Top10 results with valid metadata | unit | `pytest tests/test_vector_db.py::test_query_returns_results -x` | NO — Wave 0 |
| ROADMAP | Top10 recall accuracy >= 85% (spot-check) | smoke | `pytest tests/test_vector_db.py::test_recall_spot_check -x` | NO — Wave 0 |
| TECH-02 | Metadata filtering works (city, industry) | unit | `pytest tests/test_vector_db.py::test_metadata_filter -x` | NO — Wave 0 |

### Sampling Rate
- **Per task commit:** N/A (single script task)
- **Per wave merge:** Full suite — `pytest tests/`
- **Phase gate:** Spot-check recall manually validated + full suite green

### Wave 0 Gaps
- [ ] `tests/test_vector_db.py` — covers TECH-02 and ROADMAP recall requirements
- [ ] `tests/conftest.py` — shared fixtures (jobs_cleaned_path, vector_db_path, collection)
- [ ] Framework install: `pip install pytest` — if not detected

*(No existing test infrastructure — this is a greenfield project with no tests yet)*

## Sources

### Primary (HIGH confidence — pip index verified)
- chromadb 1.5.5: `pip index versions chromadb` — confirmed 1.5.5 is latest
- FlagEmbedding 1.3.5: `pip index versions FlagEmbedding` — confirmed 1.3.5 is latest
- sentence-transformers 5.3.0: `pip index versions sentence-transformers` — confirmed 5.3.0 installed

### Secondary (MEDIUM confidence — training data, network blocked for verification)
- ChromaDB Python client API: Training knowledge of `chromadb.PersistentClient`, `create_collection`, `add`, `query` patterns
- FlagEmbedding BGE-large-zh usage: Training knowledge of `BGEM3FlagModel` API and `BAAI/bge-large-zh-v1.5` model name
- HNSW parameters: Training knowledge; defaults (M=16, ef=100) well-established

### Tertiary (LOW confidence — needs validation)
- BGE-large-zh-v1.5 HuggingFace availability: Needs verification (`AutoModel` loading)
- Exact ChromaDB metadata type constraints: Null handling confirmed from experience, but check version-specific behavior
- Recall accuracy claim of >=85%: Based on BGE-large-zh Chinese benchmark reputation, not measured on this dataset

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — chromadb and FlagEmbedding versions verified via pip
- Architecture: MEDIUM — ChromaDB API from training data, not verified via docs (WebFetch blocked)
- Pitfalls: MEDIUM — common patterns from training data, not exhaustively verified

**Research date:** 2026-03-29
**Valid until:** 2026-04-28 (30 days — stable domain, versions unlikely to break)
