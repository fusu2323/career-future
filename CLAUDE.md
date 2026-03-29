<!-- GSD:project-start source:PROJECT.md -->
## Project

**基于AI的大学生职业规划智能体**

面向大学生的AI职业规划智能体，通过上传简历自动解析学生就业能力画像，对接企业招聘数据构建的岗位画像与关联图谱，生成个性化人岗匹配分析与职业生涯发展报告。帮助学生清晰认知自身能力与目标岗位的差距，制定可操作的行动计划。

**Core Value:** 帮助大学生从"盲目规划"走向"精准匹配"——通过AI分析让学生清楚知道自己"能做什么"、"缺什么"、"该怎么补"。

### Constraints

- **LLM**: 必须使用大语言模型作为核心（glm-4等）进行画像生成、匹配、报告生成
- **数据规模**: 10000条岗位数据，约100个岗位
- **匹配维度**: 人岗匹配从基础要求、职业技能、职业素养、发展潜力4个维度分析
- **准确率指标**: 关键技能匹配≥80%，画像准确率≥90%
- **技术栈**: 现有Python后端（FastAPI）+ 前端技术
- **开发周期**: 竞赛项目，周期有限
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## IMPORTANT CAVEAT
## Recommended Stack
### Core Backend Framework
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **Python** | 3.11+ | Language runtime | Required for LLM ecosystem, excellent async support | HIGH |
| **FastAPI** | 0.110+ | Web framework | Native async, Pydantic validation, automatic OpenAPI docs, ideal for AI APIs | HIGH |
| **Uvicorn** | 0.27+ | ASGI server | Recommended ASGI server for FastAPI, production-ready | HIGH |
| **Pydantic** | 2.x | Data validation | Built into FastAPI, schema-first development | HIGH |
- Django: Overkill for this project, synchronous by default, heavier
- Flask: Lacks native async, requires more boilerplate for type validation
- FastAPI: Best of both worlds - async native, automatic docs, Pydantic integration
### Vector Database
| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **ChromaDB** | Semantic search, document embedding storage | Already in project tech stack, simple API, good for <100K vectors | MEDIUM |
| **FAISS** | High-performance vector search | Better scalability than ChromaDB for larger datasets, Facebook-maintained | MEDIUM |
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
- Career paths and job transitions are inherently graph-shaped (nodes + relationships)
- Cypher queries are natural for "find path from A to B" questions
- Existing matching algorithms likely already model this structure
- Project explicitly requires "岗位晋升图谱" and "换岗路径图谱"
### LLM (Large Language Model)
| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **GLM-4** (Zhipu AI) | Core AI reasoning, report generation | Project constraint per 赛题, excellent Chinese performance, good API | MEDIUM |
| **Qwen-2.5** (Alibaba) | Alternative Chinese LLM | Strong Chinese NLG, open-source options available | MEDIUM |
- GLM-4: `zhipu-openaiapi` compatible endpoint (智谱AI)
- Qwen: DashScope API or self-hosted Qwen-2.5
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
### RAG Framework
| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **LangChain** | RAG orchestration, agent patterns | Mature ecosystem, good for prototype, extensive integrations | MEDIUM |
| **LlamaIndex** | RAG-focused data ingestion | Better for complex document retrieval, more Pythonic | MEDIUM |
| **Custom (Lite) RAG** | Simple RAG without heavy framework | Avoid framework overhead, use direct API calls | MEDIUM |
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
- Larger ecosystem for AI/ML dashboards
- More component libraries available
- Better for complex interactive states (matching results, reports)
- React is more common in enterprise/AI products
- Faster initial learning curve
- Cleaner syntax for simple views
- Good choice if team knows Vue already
### Agent Framework (Optional)
| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **LangGraph** | Agent orchestration | Built on LangChain, good for multi-step reasoning | MEDIUM |
| **Custom FSM** | Simple state machine | Sufficient for this use case, less overhead | MEDIUM |
## Installation
# Core backend
# Chinese embedding
# LLM clients
# or
# Frontend (React)
## Architecture Pattern: RAG + Agent
### Recommended Pattern for Career Planning Agent
### Data Flow
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
## Stack Summary
- Python 3.11+ / FastAPI / Uvicorn
- ChromaDB (vectors) + Neo4j (graph)
- GLM-4 (LLM) + BGE-large-zh (embeddings)
- React + Vite + Ant Design + Tailwind CSS
- FastAPI: Async-native, Pydantic validation, minimal boilerplate
- ChromaDB + Neo4j: Match project constraints, already selected
- GLM-4: Project requirement (Chinese LLM)
- React: Largest ecosystem for AI dashboards
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
## Sources
- FastAPI: https://fastapi.tiangolo.com/ (verify current version)
- ChromaDB: https://docs.trychroma.com/ (verify current status)
- Neo4j: https://neo4j.com/docs/ (verify Cypher version)
- GLM-4: https://github.com/THUDM/GLM-4 (verify API changes)
- Qwen: https://github.com/QwenLM/Qwen (verify current version)
- BGE: https://github.com/FlagOpen/FlagEmbedding (verify latest model)
- LangChain: https://python.langchain.com/docs/ (verify current patterns)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
