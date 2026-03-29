# Architecture Patterns

**Domain:** AI Career Planning Agent
**Project:** 基于AI的大学生职业规划智能体
**Researched:** 2026-03-29
**Confidence:** MEDIUM (established patterns; web search unavailable for verification)

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI Career Planning Agent                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │   Student    │    │     Job      │    │   Career     │    │   Report   │ │
│  │   Profile    │    │    Profile   │    │    Path      │    │   Gen      │ │
│  │   Manager    │    │    Builder   │    │   Graph      │    │   Pipeline │ │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └─────┬──────┘ │
│         │                  │                   │                  │        │
│         └──────────────────┴───────────────────┴──────────────────┘        │
│                                    │                                         │
│                          ┌─────────▼─────────┐                              │
│                          │  Matching Engine  │                              │
│                          │  (4-Dimension)    │                              │
│                          └─────────┬─────────┘                              │
│                                    │                                         │
│                    ┌───────────────┼───────────────┐                        │
│                    │               │               │                        │
│              ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐                  │
│              │  ChromaDB │   │   Neo4j   │   │    LLM    │                  │
│              │  (Vector) │   │  (Graph)  │   │  (GLM-4)  │                  │
│              └───────────┘   └───────────┘   └───────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Boundaries

### 1. Student Profile Manager

**Responsibility:** Parse resumes, extract competencies, generate student ability profile.

**Boundary:** Accepts raw resume (PDF/DOCX) as input. Outputs structured student profile with 7 dimensions.

| Input | Output | External Calls |
|-------|--------|----------------|
| Resume file (PDF/DOCX) | StudentProfile (7-dim) | ResumeParser, LLM, ChromaDB (storage) |

**Key Operations:**
- `parse_resume(file) -> RawProfile`
- `enhance_profile(raw) -> StudentProfile` (LLM augmentation)
- `score_profile(profile) -> ProfileScores` (completeness, competitiveness)

### 2. Job Profile Builder

**Responsibility:** Process 10,000 job postings into structured job profiles.

**Boundary:** Accepts raw job data. Outputs job profiles indexed in ChromaDB with relationships in Neo4j.

| Input | Output | External Calls |
|-------|--------|----------------|
| Job postings (10K records) | JobProfile (7-dim) | LLM, ChromaDB, Neo4j |

**Key Operations:**
- `batch_process_jobs(jobs[]) -> JobProfiles[]`
- `extract_skills(job_desc) -> SkillVector`
- `index_job_profile(profile) -> void`

### 3. Career Path Graph (Neo4j)

**Responsibility:** Maintain career progression relationships between jobs.

**Boundary:** Stores job hierarchy, promotion paths, and transition paths. Query interface for path finding.

| Input | Output | External Calls |
|-------|--------|----------------|
| Job profiles | Graph relationships | Neo4j, LLM (for path suggestions) |

**Node Types:**
- `Job`: Represents a job profile
- `Skill`: Skill nodes for skill-based paths
- `Industry`: Industry classification

**Relationship Types:**
- `PROMOTES_TO`: Direct promotion path
- `TRANSITIONS_TO`: Cross-job transition path
- `REQUIRES_SKILL`: Skill requirement edge
- `SAME_TRACK`: Same career track

### 4. Matching Engine (4-Dimension)

**Responsibility:** Calculate compatibility between student profile and job profiles.

**Boundary:** Takes StudentProfile + JobProfile, returns MatchResult with 4-dimension scores.

| Input | Output | External Calls |
|-------|--------|----------------|
| StudentProfile, JobProfile | MatchResult (4-dim) | ChromaDB (similarity), LLM (semantic) |

**Four Dimensions:**
1. **基础要求 (Basic Requirements)**: Education, certificates, basic skills
2. **职业技能 (Professional Skills)**: Domain-specific competencies
3. **职业素养 (Professional Qualities)**: Communication, stress tolerance, teamwork
4. **发展潜力 (Development Potential)**: Learning ability, innovation, adaptability

**Formula:**
```
TotalScore = w1*Basic + w2*Professional + w3*Quality + w4*Potential
```
Dynamic weights configurable per student profile.

### 5. Report Generation Pipeline

**Responsibility:** Generate comprehensive career planning reports.

**Boundary:** Orchestrates multiple LLM calls into a structured report.

| Input | Output | External Calls |
|-------|--------|----------------|
| StudentProfile, JobProfile, MatchResult, CareerPath | CareerReport | LLM (multiple calls), Template engine |

**Pipeline Stages:**
1. **Target Setting**: LLM extracts career goals from match results
2. **Path Planning**: Query Neo4j for career paths
3. **Gap Analysis**: Compare student vs job requirements
4. **Plan Generation**: Create short/medium-term action plans
5. **Polishing**: Content review, completeness check, export

### 6. Data Storage Layer

**ChromaDB (Vector Storage):**
- Job profile embeddings (skill vectors, description vectors)
- Student profile embeddings (for similarity search)
- Query: `find_similar_jobs(student_vector, top_k)`

**Neo4j (Graph Storage):**
- Career path graph (job promotions, transitions)
- Skill graph (skill dependencies, prerequisite chains)
- Query: `find_career_paths(job_a, job_b)`, `find_transition_options(job)`

## Data Flow

### Resume to Profile Flow

```
Resume (PDF)
    │
    ▼
┌─────────────────┐
│  Resume Parser  │  (extract text, structure)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Profiler   │  (generate 7-dim profile)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ChromaDB│ │ Student│ (in-memory)
│(vector)│ │ Profile│
└────────┘ └────────┘
```

### Job Matching Flow

```
Student Profile
    │
    ├──────────────────────────────────────┐
    │                                      │
    ▼                                      ▼
┌─────────────────┐              ┌─────────────────┐
│  ChromaDB       │              │  Neo4j          │
│  (vector search)│              │  (path query)   │
│  Top-K jobs     │              │  career paths   │
└────────┬────────┘              └────────┬────────┘
         │                                │
         └────────────┬───────────────────┘
                       ▼
              ┌─────────────────┐
              │  Matching Engine│
              │  4-dimension    │
              │  calculation    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Match Results │
              │  (ranked jobs) │
              └─────────────────┘
```

### Report Generation Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Student    │────▶│   Gap        │────▶│   Career     │
│   Profile    │     │   Analysis   │     │   Path       │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                │
┌──────────────┐     ┌──────────────┐           │
│   Match      │────▶│   Plan       │◀──────────┘
│   Results    │     │   Generation │
└──────────────┘     └──────┬───────┘
                            │
                            ▼
                   ┌──────────────┐
                   │   Report     │
                   │   Polishing  │
                   └──────────────┘
```

## Build Order Recommendations

### Phase 1: Foundation (Data Layer)

**Goal:** Establish data storage for jobs and career paths.

1. **Job Profile Builder** first
   - Process 10,000 jobs into structured profiles
   - Index into ChromaDB for vector search
   - Build promotion/transition graph in Neo4j

2. **Why first:** All downstream components depend on job data. Matching needs job vectors. Report generation needs career paths.

**Dependencies:** None (greenfield)

### Phase 2: Student Profile (Input Layer)

**Goal:** Enable student data input and profiling.

1. **Resume Parser**
   - Extract text from PDF/DOCX
   - Basic structure extraction

2. **Student Profile Manager**
   - 7-dimension profile generation via LLM
   - Profile scoring

**Dependencies:** Requires LLM integration, ChromaDB

### Phase 3: Matching Engine (Core Logic)

**Goal:** Calculate match scores between students and jobs.

1. **ChromaDB similarity search** (vector search baseline)
2. **4-dimension scoring engine**
3. **Dynamic weight configuration**

**Dependencies:** Job profiles indexed, student profiles available

### Phase 4: Report Generation (Output Layer)

**Goal:** Generate actionable career planning reports.

1. **Gap Analysis Service**
2. **Career Path Query** (Neo4j integration)
3. **LLM Report Generation**
4. **Polish and Export**

**Dependencies:** Matching engine, career paths, student profiles

## Scalability Considerations

| Scale | Jobs | Students | Recommendation |
|-------|------|----------|----------------|
| Current | 10,000 | ~100 concurrent | ChromaDB + Neo4j single instance |
| Growth | 100K+ | 1000+ concurrent | ChromaDB collection sharding, Neo4j causal clusters |

## Integration with Existing Tech

### ChromaDB Usage

```python
# Job profile vector store
collection = chroma_client.get_or_create_collection("jobs")
collection.add(
    ids=[job_id],
    embeddings=[job_embedding],  # Skills + description vector
    documents=[job_profile_json]
)

# Student profile for similarity
student_vector = embed(student_profile)
results = collection.query(query_embeddings=[student_vector], n_results=10)
```

### Neo4j Usage

```cypher
// Career path query
MATCH path = (a:Job {title: "软件工程师"})-[r:PROMOTES_TO*1..3]-(b:Job {title: "技术总监"})
RETURN path

// Transition options
MATCH (current:Job {title: "前端开发"})-[TRANSITIONS_TO]->(next:Job)
RETURN next.title, next.avg_salary
```

### FastAPI Integration

```python
# API layer exposes:
POST /api/resume/upload        # Student profile creation
POST /api/jobs/batch          # Admin: job ingestion
POST /api/matching/analyze     # Match student to jobs
GET  /api/career-paths/{job}   # Career path for job
POST /api/report/generate      # Full report generation
```

## Anti-Patterns to Avoid

1. **Monolithic LLM calls**: Don't try to generate entire report in single LLM call. Pipeline breaks down analysis.
2. **Ignoring vector/graph separation**: ChromaDB for similarity, Neo4j for relationships. Don't conflate.
3. **Hardcoded matching weights**: Student profiles vary. Use dynamic weights based on profile completeness.
4. **No caching on job embeddings**: Job profiles are static. Embed once, cache aggressively.

## Sources

- **Context7:** Not available (web search tools non-functional)
- **Official Docs:** Unable to verify (network restrictions)
- **Confidence:** MEDIUM - Based on established RAG/agent architecture patterns, not project-specific verification

**Note:** This architecture relies on established patterns for AI agents with vector retrieval (ChromaDB) and knowledge graphs (Neo4j). Web search was unavailable for verification of current best practices. Recommend phase 1 research spike to validate ChromaDB/Neo4j integration patterns before full implementation.
