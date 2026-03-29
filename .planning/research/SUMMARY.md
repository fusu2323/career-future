# Project Research Summary

**Project:** 基于AI的大学生职业规划智能体 (AI Career Planning Agent)
**Domain:** AI Career Planning / Human-Resource Matching
**Researched:** 2026-03-29
**Confidence:** MEDIUM

## Executive Summary

This project is a Chinese AI career planning agent that matches college students with suitable jobs by parsing resumes, generating 7-dimension ability profiles, performing 4-dimension job matching (基础要求/职业技能/职业素养/发展潜力), and producing actionable career development reports. It uses a RAG + Agent architecture with ChromaDB for semantic vector search, Neo4j for career path graphs, and GLM-4 as the primary Chinese LLM.

Research confirms the technology stack is appropriate: FastAPI for async API handling, ChromaDB and Neo4j as already-selected project databases, BGE-large-zh for Chinese embeddings, and React/Vite for the frontend. The critical insight is that the job data layer must be built BEFORE student profile generation, since all downstream matching and reporting depends on indexed job profiles. The greatest risks are LLM hallucination in career advice, resume parsing failures on varied Chinese formats, and over-engineering the knowledge graph at the expense of matching accuracy.

## Key Findings

### Recommended Stack

The stack is well-suited for this competition project. Python/FastAPI provides async-native API handling with Pydantic validation. ChromaDB handles vector similarity search for job-student matching at the current 10K scale. Neo4j stores career path relationships (promotion paths, job transitions). GLM-4 is the project-mandated Chinese LLM with strong Chinese NLU performance. BGE-large-zh is the recommended Chinese embedding model, outperforming generic English models on Chinese semantic tasks. React + Vite + Ant Design + Tailwind CSS provides the largest ecosystem for AI dashboard components.

**Core technologies:**
- **Python 3.11+ / FastAPI / Uvicorn** — Async-native backend, native Pydantic validation, automatic OpenAPI docs
- **ChromaDB** — Vector similarity for job-student matching; existing project choice, sufficient for 10K vectors
- **Neo4j** — Career path graph; existing project choice, Cypher queries natural for path-finding
- **GLM-4 (Zhipu AI)** — Project-mandated Chinese LLM; excellent Chinese performance, good API
- **BGE-large-zh (FlagEmbedding)** — Best Chinese semantic matching; open-source, 1024 dimensions
- **React + Vite + Ant Design + Tailwind CSS** — Largest AI dashboard ecosystem

**Avoid:** LangChain (overkill for competition timeline), Milvus/Pinecone (over-engineered for scale), Django (heavy, synchronous), GPT-4 (poor Chinese cost-efficiency per project constraints).

### Expected Features

**Must have (table stakes):**
- Resume upload and parsing (PDF/DOCX) — Primary input, must handle varied Chinese formats
- Student ability profile generation (7 dimensions) — Core output visualized as radar chart
- Job profile and association graph — Promotion paths + transfer paths visualized
- Basic person-job matching with score and explanation — Core matching mechanic
- Career development report with action plan — Final deliverable, PDF export required

**Should have (competitive differentiators):**
- Gap analysis with learning path recommendations — "What am I missing, how do I fix it"
- 4-dimension competency deep dive — Per requirements, captures how student works not just what they know
- AI-powered report polish and professional writing — Per REPORT-04 requirement, one-click optimization
- Interactive job graph exploration — Visual career navigation, not just static reports

**Defer (v2+):**
- Multi-session progress tracking — Requires user auth (out of scope)
- Salary trajectory projection — Requires market data not in dataset
- Career simulation scenarios — High complexity, lower evaluation weight
- Learning resource database — External data required

### Architecture Approach

The system follows a RAG + Agent pattern with clear component boundaries. Five major components: (1) **Student Profile Manager** — parses resumes, generates 7-dim profiles; (2) **Job Profile Builder** — processes 10K jobs into structured profiles indexed in ChromaDB; (3) **Career Path Graph (Neo4j)** — stores promotion/transition relationships; (4) **Matching Engine (4-dimension)** — calculates compatibility with configurable dynamic weights; (5) **Report Generation Pipeline** — orchestrates LLM calls into structured reports with gap analysis and action plans.

Data flow: Resume upload -> Parse -> Generate embedding -> Student Profile; Job postings -> Extract skills -> Index in ChromaDB (vectors) + Neo4j (relationships); Student Profile + ChromaDB similarity search + Neo4j path query -> Matching Engine -> Ranked results -> Report Generation with gap analysis and career paths.

**Key architectural constraint:** Build Job Profile Builder FIRST — all downstream components depend on indexed job data.

### Critical Pitfalls

1. **LLM Hallucination in Career Advice** — The most critical risk. LLMs generate confident but incorrect career advice without grounding. Prevention: Build RAG pipeline BEFORE any advice generation; always retrieve relevant job/career data before generating; add confidence scoring; include disclaimer layer distinguishing data-grounded vs. LLM-generated content.

2. **Resume Parsing Failure on Varied Chinese Formats** — Chinese resumes vary widely in structure (timeline, table, free-form). Prevention: Implement multiple parsing strategies; validate parsed data against schemas; use LLM for structure inference; flag low-confidence parses for user verification.

3. **Over-Engineering Knowledge Graph at Expense of Matching** — Graph features are visually impressive but competition judges matching accuracy first. Prevention: Prioritize matching accuracy over graph depth; build minimum viable graph first; time-box graph development separately.

4. **Vague Non-Actionable Reports** — Generic advice like "improve communication skills" fails actionable requirement. Prevention: Ground every recommendation in specific matching gaps; use structured templates requiring current state, target state, specific actions, success metrics; implement actionability scoring before delivery.

5. **Undefined Accuracy Metrics** — Project targets "80% matching accuracy" and "90% profile accuracy" without defining what these mean. Prevention: Define precision metrics explicitly (e.g., "80% of top-5 recommendations are genuinely suitable"); create validation dataset; separate evaluation from generation.

## Implications for Roadmap

Based on research, the suggested phase structure follows the data dependency chain:

### Phase 1: Foundation — Job Data Layer
**Rationale:** All downstream components depend on indexed job data. Matching needs job vectors. Reports need career paths. Building this first enables parallel development of other components later.
**Delivers:** Job profiles (10K jobs), ChromaDB vector index, Neo4j career path graph (promotion paths, transition paths)
**Implements:** Job Profile Builder component, ChromaDB indexing, Neo4j graph construction
**Avoids:** Pitfall 8 (over-engineering graphs before matching works)

### Phase 2: Input Layer — Student Profile Generation
**Rationale:** Student input is the primary use case. Resume parsing must be robust before matching can be validated.
**Delivers:** Resume upload (PDF/DOCX), resume parser, 7-dimension student profile, profile visualization, completeness scoring
**Implements:** Student Profile Manager component
**Avoids:** Pitfall 2 (parsing failures), Pitfall 7 (Chinese language nuances), Pitfall 4 (cold start handling)

### Phase 3: Core — Matching System with Gap Analysis
**Rationale:** This is the core competitive value — the "精准匹配" that determines 80% accuracy requirement. Must be built and tested before report generation.
**Delivers:** 4-dimension matching engine, gap analysis service, ranked job recommendations, match explanations
**Implements:** Matching Engine component, ChromaDB similarity search integration, Neo4j path query integration
**Avoids:** Pitfall 1 (hallucination — must build RAG before this phase's LLM calls), Pitfall 3 (matching bias), Pitfall 10 (weight over-tuning)

### Phase 4: Output — Report Generation and Polish
**Rationale:** Final deliverable depends on matching results, career paths, and gap analysis. Requires all upstream components.
**Delivers:** Career development report, action plan, report polish per REPORT-04, PDF export
**Implements:** Report Generation Pipeline component
**Avoids:** Pitfall 5 (vague reports), Pitfall 9 (export failures)

### Phase Ordering Rationale

- **Job data before student input** — Matching requires indexed jobs; cannot validate matching accuracy without job data
- **Profile before matching** — Cannot match without student profiles
- **Matching before reports** — Reports depend on matching results and gap analysis
- **Core matching before polish** — Get matching working first, polish later
- **Each phase produces testable outputs** — Enables validation before moving to next phase

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Neo4j schema design — how to model promotion/transition paths for 10K jobs; needs spike on Cypher performance
- **Phase 2:** Resume parsing edge cases — need actual Chinese resume samples to test diverse formats; research Chinese parsing libraries

Phases with standard patterns (skip research-phase):
- **Phase 3:** 4-dimension matching is a known pattern; RAG + vector search is well-documented
- **Phase 4:** Report generation with templates is straightforward; PDF export libraries are mature

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | FastAPI, React are HIGH confidence (stable, well-documented); LLM/embedding choices MEDIUM (couldn't verify GLM-4 API status externally) |
| Features | MEDIUM | Table stakes and anti-features HIGH (explicit project constraints); differentiator assessment MEDIUM (market position shifts) |
| Architecture | MEDIUM | Component boundaries clear; RAG + Agent pattern is standard; ChromaDB/Neo4j integration patterns established |
| Pitfalls | MEDIUM | Patterns identified are well-known in AI/ML systems; prevention strategies standard; some risks (Chinese resume formats) need empirical validation |

**Overall confidence:** MEDIUM

### Gaps to Address

- **GLM-4 API verification:** Current API endpoint and authentication method should be verified before Phase 2
- **Chinese resume format diversity:** Actual testing with 20+ diverse Chinese resume templates needed to validate parsing robustness
- **Accuracy metric definition:** Must define "80% matching accuracy" and "90% profile accuracy" precisely before Phase 3 begins
- **BGE-large-zh vs M3E:** Verify current Chinese embedding benchmarks — M3E may have improved since training data
- **Real user expectations:** Recommend 5-10 college student interviews to validate feature priorities before finalizing Phase 2 scope

## Sources

### Primary (HIGH confidence)
- Project constraints (PROJECT.md, 赛题要求) — explicit technology mandates (GLM-4, Chinese LLM)
- Existing codebase — ChromaDB and Neo4j already selected and partially implemented

### Secondary (MEDIUM confidence)
- STACK.md research — FastAPI/React ecosystem patterns well-established; Chinese LLM selection based on project constraints
- FEATURES.md — Domain knowledge of recruitment platforms (智联招聘, 猎聘, BOSS直聘); competitive whitespace analysis
- ARCHITECTURE.md — RAG + Agent patterns standard; component boundaries clear; build order follows data dependencies
- PITFALLS.md — LLM hallucination and cold-start are well-documented AI system risks; mitigation strategies standard

### Tertiary (LOW confidence)
- GLM-4 specific behavior on Chinese career advice — needs empirical testing
- Actual Chinese resume format distribution — needs domain research
- BGE-large-zh current benchmarks — training data may be 6-18 months stale

---

*Research completed: 2026-03-29*
*Ready for roadmap: yes*
