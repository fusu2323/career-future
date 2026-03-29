# Technology Stack

**Project:** AI职业规划智能体 (AI Career Planning Agent)
**Research Mode:** Stack Recommendation
**Researched:** 2026-03-29
**Confidence:** MEDIUM-LOW (external verification unavailable - training data only, 6-18 months stale)

## IMPORTANT CAVEAT

External verification via WebSearch/WebFetch/MCP tools was unavailable during research. All recommendations below are based on training data and should be validated against current official documentation before finalizing. Version numbers may be outdated.

---

## Recommended Stack

### Core Backend Framework

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **Python** | 3.11+ | Language runtime | Required for LLM ecosystem, excellent async support | HIGH |
| **FastAPI** | 0.110+ | Web framework | Native async, Pydantic validation, automatic OpenAPI docs, ideal for AI APIs | HIGH |
| **Uvicorn** | 0.27+ | ASGI server | Recommended ASGI server for FastAPI, production-ready | HIGH |
| **Pydantic** | 2.x | Data validation | Built into FastAPI, schema-first development | HIGH |

**Why FastAPI over alternatives (Django, Flask):**
- Django: Overkill for this project, synchronous by default, heavier
- Flask: Lacks native async, requires more boilerplate for type validation
- FastAPI: Best of both worlds - async native, automatic docs, Pydantic integration

### Vector Database

| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **ChromaDB** | Semantic search, document embedding storage | Already in project tech stack, simple API, good for <100K vectors | MEDIUM |
| **FAISS** | High-performance vector search | Better scalability than ChromaDB for larger datasets, Facebook-maintained | MEDIUM |

**Recommendation:** Stick with **ChromaDB** for this project (10K jobs, ~100岗位 profiles). The existing codebase already uses it, and it handles this scale well. If performance issues arise at 100K+ vectors, migrate to FAISS or Qdrant.

**Alternatives considered:**

| Alternative | Why Not |
|-------------|---------|
| **Milvus** | Over-engineered for this scale, requires more infrastructure |
| **Pinecone** | Cloud-only, unnecessary cost for offline data |
| **Qdrant** | Viable alternative if ChromaDB has issues, better Rust performance |
| **Weaviate** | More complex setup, less Python-friendly |

### Graph Database

| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **Neo4j** | Knowledge graph, career path mapping | Already in project tech stack, excellent Cypher query language, proven for career/path applications | HIGH |

**Why Neo4j is correct for this project:**
- Career paths and job transitions are inherently graph-shaped (nodes + relationships)
- Cypher queries are natural for "find path from A to B" questions
- Existing matching algorithms likely already model this structure
- Project explicitly requires "岗位晋升图谱" and "换岗路径图谱"

### LLM (Large Language Model)

| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **GLM-4** (Zhipu AI) | Core AI reasoning, report generation | Project constraint per 赛题, excellent Chinese performance, good API | MEDIUM |
| **Qwen-2.5** (Alibaba) | Alternative Chinese LLM | Strong Chinese NLG, open-source options available | MEDIUM |

**Recommendation:** Use **GLM-4** as primary per project constraints. Have **Qwen-2.5** as backup for cost/availability issues.

**API Access:**
- GLM-4: `zhipu-openaiapi` compatible endpoint (智谱AI)
- Qwen: DashScope API or self-hosted Qwen-2.5

**Why Chinese LLMs:**
- Project is Chinese-language career planning
- GLM-4 and Qwen outperform GPT-4 on Chinese benchmarks
- Cost advantage for Chinese-language content
- Project explicitly requires GLM-4

### Embedding Models

| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **text-embedding-3-small** (OpenAI) | General text embedding | Good quality, cost-effective, 1536 dimensions | MEDIUM |
| **BGE-large-zh** (FlagEmbedding) | Chinese-specialized embedding | Best Chinese semantic matching, open-source | MEDIUM |
| **M3E** (Moka) | Chinese embedding alternative | Good balance of speed and quality for Chinese | MEDIUM |

**Recommendation:** Use **BGE-large-zh** for Chinese content. If OpenAI compatibility needed, fall back to text-embedding-3-small. M3E is a lighter alternative if speed is critical.

### RAG Framework

| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **LangChain** | RAG orchestration, agent patterns | Mature ecosystem, good for prototype, extensive integrations | MEDIUM |
| **LlamaIndex** | RAG-focused data ingestion | Better for complex document retrieval, more Pythonic | MEDIUM |
| **Custom (Lite) RAG** | Simple RAG without heavy framework | Avoid framework overhead, use direct API calls | MEDIUM |

**Recommendation:** For a competition project with limited time, use **Lite RAG** (direct API calls) or **LlamaIndex** if complex document hierarchy is needed. LangChain adds complexity without much benefit here.

**Why avoid heavy frameworks:**
- Competition project = limited development time
- Framework overhead obscures what's actually happening
- Harder to debug and optimize
- Simple RAG is just: embed → store → retrieve → augment → generate

### Frontend

| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **React** + **Vite** | UI framework + build tool | Largest ecosystem, excellent AI UI component libraries | HIGH |
| **Vue 3** + **Vite** | Alternative UI framework | Simpler learning curve, good Chinese documentation | MEDIUM |
| **Ant Design** (React) | UI component library | Professional look, good AI dashboard components | MEDIUM |
| **Element Plus** (Vue) | UI component library (Vue version) | Clean, professional | MEDIUM |
| **Tailwind CSS** | Utility-first CSS | Rapid UI development, consistent design | MEDIUM |

**Recommendation:** **React + Vite + Ant Design + Tailwind CSS**

**Why React over Vue:**
- Larger ecosystem for AI/ML dashboards
- More component libraries available
- Better for complex interactive states (matching results, reports)
- React is more common in enterprise/AI products

**Why Vue as alternative:**
- Faster initial learning curve
- Cleaner syntax for simple views
- Good choice if team knows Vue already

### Agent Framework (Optional)

| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **LangGraph** | Agent orchestration | Built on LangChain, good for multi-step reasoning | MEDIUM |
| **Custom FSM** | Simple state machine | Sufficient for this use case, less overhead | MEDIUM |

**Recommendation:** The career planning agent has well-defined steps (parse resume → generate profile → match → generate report). A simple FSM or custom orchestration is sufficient. LangGraph adds unnecessary complexity unless you need dynamic multi-agent workflows.

---

## Installation

```bash
# Core backend
pip install fastapi uvicorn pydantic pydantic-settings
pip install langchain langchain-community  # Optional, for RAG helpers
pip install chromadb neo4j
pip install httpx aiohttp  # For async API calls

# Chinese embedding
pip install sentence-transformers FlagEmbedding  # BGE-large-zh

# LLM clients
pip install zhipuai  # GLM-4 SDK
# or
pip install dashscope  # Qwen SDK

# Frontend (React)
npm create vite@latest frontend -- --template react-ts
npm install antd tailwindcss postcss autoprefixer
npm install @ant-design/icons recharts  # For AI dashboard visualization
```

---

## Architecture Pattern: RAG + Agent

### Recommended Pattern for Career Planning Agent

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface (React)                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (Python)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Resume API  │  │ Matching API│  │ Report Generation API  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────────────────┐
│   ChromaDB      │ │   Neo4j     │ │         LLM (GLM-4)         │
│  (Embeddings)  │ │  (Graph)    │ │  - Profile Generation       │
│  - Job vectors │ │  - Paths    │ │  - Matching Analysis        │
│  - Resume text  │ │  - Relations│ │  - Report Writing           │
└─────────────────┘ └─────────────┘ └─────────────────────────────┘
```

### Data Flow

1. **Resume Upload** → Parse → Extract skills/experience → Generate embedding
2. **Profile Generation** → LLM analyzes resume → Structured profile JSON
3. **Matching** → Retrieve similar job vectors (ChromaDB) → Query career paths (Neo4j) → LLM scoring
4. **Report Generation** → LLM synthesizes all data → Formatted career report

---

## What NOT to Use and Why

| Technology | Why Avoid | Instead Use |
|------------|-----------|-------------|
| **LangChain (full)** | Overkill, verbose, hard to debug | Direct API calls or Lite RAG |
| **LangSmith/LangFuse** | Observability overhead, cost | Simple logging for competition |
| **Milvus/Pinecone** | Over-engineered for 10K vectors | ChromaDB (sufficient) |
| **Django** | Heavy, synchronous, slow development | FastAPI (lighter, async) |
| **Next.js** | Overkill if just web dashboard | Vite + React SPA |
| **GPT-4** | Poor Chinese cost-efficiency | GLM-4 or Qwen (per constraints) |
| **Elasticsearch** | Complex infrastructure | Not needed for this scale |

---

## Stack Summary

**Core Stack:**
- Python 3.11+ / FastAPI / Uvicorn
- ChromaDB (vectors) + Neo4j (graph)
- GLM-4 (LLM) + BGE-large-zh (embeddings)
- React + Vite + Ant Design + Tailwind CSS

**Rationale:**
- FastAPI: Async-native, Pydantic validation, minimal boilerplate
- ChromaDB + Neo4j: Match project constraints, already selected
- GLM-4: Project requirement (Chinese LLM)
- React: Largest ecosystem for AI dashboards

---

## Confidence Assessment

| Component | Confidence | Reason |
|-----------|------------|--------|
| Backend Framework | HIGH | FastAPI is well-established, no major changes expected |
| Vector DB | MEDIUM | ChromaDB choice is correct for scale; alternatives (FAISS) well-understood |
| Graph DB | HIGH | Neo4j is standard, no recent disruptive alternatives |
| Chinese LLM | MEDIUM | GLM-4 known but version/status should verify; Qwen similar |
| Embedding | MEDIUM | BGE-large-zh is strong choice but verify current benchmarks |
| Frontend | HIGH | React ecosystem stable, opinions are well-grounded |
| RAG Pattern | MEDIUM | Pattern is standard; specific library versions need verification |

---

## Sources

**Cannot verify via external tools - following sources are from training data (stale by 6-18 months):**

- FastAPI: https://fastapi.tiangolo.com/ (verify current version)
- ChromaDB: https://docs.trychroma.com/ (verify current status)
- Neo4j: https://neo4j.com/docs/ (verify Cypher version)
- GLM-4: https://github.com/THUDM/GLM-4 (verify API changes)
- Qwen: https://github.com/QwenLM/Qwen (verify current version)
- BGE: https://github.com/FlagOpen/FlagEmbedding (verify latest model)
- LangChain: https://python.langchain.com/docs/ (verify current patterns)

**Validation Required Before Phase 1:**
1. Verify GLM-4 API endpoint and authentication method
2. Check ChromaDB latest version and any breaking changes
3. Confirm BGE-large-zh is still best Chinese embedding (M3E may have improved)
4. Verify frontend library compatibility (React 19, Vite 6, etc.)
