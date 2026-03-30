# Stack Research — v1.1 New Features

**Domain:** AI Career Planning Agent (resume parsing, profiling, matching, reporting, React frontend)
**Project:** 基于AI的大学生职业规划智能体
**Researched:** 2026-03-30
**Confidence:** MEDIUM (WebSearch unavailable; training knowledge with known gaps flagged)

---

## Context: What Is Already Validated (v1.0)

The following technologies were already selected and validated in v1.0. This document covers only the **additions** needed for v1.1. Do not re-research these:

| Component | Technology | Status |
|-----------|------------|--------|
| Backend framework | Python 3.11+ / FastAPI / Uvicorn / Pydantic 2.x | Validated |
| Vector DB | ChromaDB | Validated |
| Graph DB | Neo4j | Validated |
| LLM | DeepSeek (deepseek-chat) via HTTP | Validated |
| Embeddings | BGE-m3 via SiliconFlow API | Validated |
| Async HTTP | httpx + tenacity | Validated |

---

## v1.1 New Technology Additions

### 1. Document Parsing (Python — Phase 6)

**Purpose:** Extract text and structure from uploaded resumes (PDF and DOCX formats).

| Library | Version | Purpose | Why Recommended |
|---------|---------|---------|-----------------|
| **pdfplumber** | 0.11+ | PDF text/table extraction | Best Python-native PDF parsing; preserves layout, handles tables well |
| **pymupdf** | 1.24+ | PDF fast extraction, image extraction | Faster than pdfplumber, good for large files; complements pdfplumber |
| **python-docx** | 1.1+ | DOCX parsing | Standard Python DOCX library; easy table/text extraction |

**Installation:**
```bash
pip install pdfplumber pymupdf python-docx
```

**Alternative Considered:**

| Our Choice | Alternative | When to Use Alternative |
|------------|-------------|------------------------|
| pdfplumber | PyPDF2 | PyPDF2 has slower table extraction; pdfplumber is better for structured resumes |
| pdfplumber + pymupdf | marker (OCR) | Only if scanned PDFs are a major concern; adds GPU/OCR complexity |
| python-docx | docx2txt | docx2txt simpler but less API control; python-docx gives structured access |

**Recommendation:** Use **pdfplumber** as primary PDF parser (good table/layout handling), **pymupdf** as fallback for speed-critical paths, and **python-docx** for DOCX. Do not add OCR libraries (marker/paddleocr) unless scanned PDF handling becomes a demonstrated problem — OCR adds significant complexity for marginal gain on a competition project where most resumes are digital.

---

### 2. Matching Engine (No New Libraries — Phase 8)

The matching engine uses existing validated infrastructure:
- **ChromaDB** — vector similarity search for candidate job retrieval
- **Neo4j** — career path graph traversal
- **DeepSeek LLM** — scoring and gap analysis via structured prompting

**No new Python packages needed.** The matching engine is primarily algorithmic work on top of existing services.

**Potential consideration (optional):**

| Library | Purpose | When to Consider |
|---------|---------|-----------------|
| **scikit-learn** | Additional similarity metrics (cosine, euclidean) | If vector similarity alone is insufficient |
| **numpy** | Numerical operations for weighted scoring | Already a transitive dependency |

---

### 3. Report Generation (Python — Phase 9)

**Purpose:** Generate structured career planning reports (path planning, action plans, evaluation metrics) and export as PDF.

| Library | Version | Purpose | Why Recommended |
|---------|---------|---------|-----------------|
| **WeasyPrint** | 0.22+ | HTML-to-PDF generation (server-side) | Produces reliable, consistent PDF output; HTML templating is familiar and flexible |
| **Jinja2** | 3.1+ | HTML templating for reports | Natural fit with WeasyPrint; FastAPI ecosystem staple |

**Installation:**
```bash
pip install weasyprint jinja2
```

**Alternative Considered:**

| Our Choice | Alternative | When to Use Alternative |
|------------|-------------|------------------------|
| WeasyPrint (server-side) | @react-pdf/renderer (client-side) | @react-pdf has React-specific learning curve; WeasyPrint is simpler for Python/FastAPI stack |
| WeasyPrint (server-side) | pdfkit + wkhtmltopdf | pdfkit requires system wkhtmltopdf binary; WeasyPrint is pure Python, easier to deploy |
| WeasyPrint (server-side) | reportlab | reportlab is low-level API; WeasyPrint with HTML/CSS is faster to template |

**Recommendation:** Use **WeasyPrint + Jinja2** for server-side PDF generation. Write report templates in HTML/CSS (styled with inline CSS for PDF compatibility), render via WeasyPrint. This is faster to iterate on report formatting than low-level APIs and avoids browser compatibility issues with client-side PDF.

**Important:** WeasyPrint requires GTK/Windows dependencies. On Windows, ensure Visual C++ redistributables are available. Test PDF generation early in Phase 9.

---

### 4. React Frontend (Phase 10)

**Purpose:** Resume upload, student profile display, career path graph visualization, matching results, report viewing/export.

The base stack (React + Vite + Ant Design + Tailwind CSS) was already recommended in v1.0 and is confirmed. The following additions are needed:

#### 4a. File Upload

| Library | Purpose | Why |
|---------|---------|-----|
| **react-dropzone** | Drag-and-drop file upload | Industry standard; handles validation, drag-drop, progress |

**Installation:**
```bash
npm install react-dropzone
```

**Built-in alternative:** HTML5 `<input type="file">` is sufficient for simple uploads. react-dropzone adds polish and is worth the dependency for a professional-feeling upload experience.

#### 4b. Graph Visualization (Career Path)

| Library | Purpose | Why Recommended |
|---------|---------|-----------------|
| **react-force-graph** | Interactive 2D/3D force-directed graphs | Best for career path visualization; Neo4j data renders naturally as nodes + edges |
| **@ant-design/charts** | Ant Design chart wrappers (G2Plot) | Alternative if already in Ant Design ecosystem; good for standard chart types |

**Installation:**
```bash
npm install react-force-graph
```

**Why react-force-graph:**
- Career paths are inherently graph-shaped (nodes = jobs, edges = promotions/transitions)
- react-force-graph renders interactive 2D and 3D graphs with pan/zoom/click
- Works well with Neo4j data exported as {nodes, links} JSON
- Lightweight (~60KB) vs full D3.js (~90KB)

**Alternative considered:**

| Our Choice | Alternative | When to Use Alternative |
|------------|-------------|------------------------|
| react-force-graph | echarts-for-react | ECharts has graph support but less graph-specific interaction; better for standard charts |
| react-force-graph | visx | Visx is lower-level D3; more control but more code; react-force-graph is faster for graph use case |
| react-force-graph | d3 | Raw D3 gives most control; react-force-graph is sufficient abstraction for this use case |

#### 4c. Charting (Student Profile Radar, Match Results)

**Already covered:** Recharts is already in the v1.0 recommendations and handles radar charts, bar charts, and line charts well. No new library needed.

**If Recharts proves insufficient:** @ant-design/charts provides Ant Design-compatible charting with less customization.

#### 4d. PDF Export (Report Download)

| Approach | Library | When to Use |
|----------|---------|-------------|
| Server-side (recommended) | FastAPI endpoint returns PDF via WeasyPrint | Single approach; simpler, consistent output |
| Client-side | @react-pdf/renderer | Only if offline capability is needed |

**Recommendation:** Use server-side PDF generation (WeasyPrint from Phase 9) and serve via FastAPI download endpoint. Client-side PDF adds complexity with minimal benefit for a competition project.

---

## Frontend Package Summary (Phase 10)

```bash
# Core frontend additions
npm install react-dropzone react-force-graph

# Already recommended in v1.0 (confirm installed)
npm install antd tailwindcss postcss autoprefixer
npm install @ant-design/icons recharts
```

---

## v1.1 Stack Summary (All New + Existing)

### Complete Python Stack (Backend)

```bash
# Already installed (v1.0)
pip install fastapi uvicorn pydantic pydantic-settings httpx tenacity chromadb neo4j

# v1.1 additions
pip install pdfplumber pymupdf python-docx weasyprint jinja2
```

### Complete Node Stack (Frontend)

```bash
# v1.0 confirmed
npm create vite@latest frontend -- --template react-ts
npm install antd tailwindcss postcss autoprefixer @ant-design/icons recharts

# v1.1 additions
npm install react-dropzone react-force-graph
```

---

## What NOT to Add for v1.1

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **OCR libraries** (paddleocr, marker) | Adds significant complexity; most resumes are digital text | pdfplumber text extraction |
| **Client-side PDF rendering** (@react-pdf/renderer) | Extra dependency, browser compatibility issues | Server-side WeasyPrint |
| **Full LangChain** | Overkill for structured prompting needs | Direct DeepSeek API calls |
| ** LlamaIndex/RAG frameworks** | Simple RAG is direct API calls | Existing httpx + prompting |
| **Additional charting libraries** | Recharts handles all needed chart types | Only add if Recharts fails |
| **Redux/toolkit for state** | React useState/useReducer sufficient for this scope | Simpler state management |

---

## Technology Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| PDF parsing | pdfplumber + pymupdf | Best Python-native PDF extraction; table/layout aware |
| DOCX parsing | python-docx | Standard, well-maintained |
| Report generation | WeasyPrint + Jinja2 | HTML/CSS templates; reliable cross-platform PDF |
| File upload UI | react-dropzone | Professional drag-drop; validates file types |
| Career path visualization | react-force-graph | Graph-native rendering; node/edge model maps to Neo4j data |
| Charting | Recharts (existing) | Already recommended; covers radar/bar/line |
| PDF export | Server-side (WeasyPrint) | Consistent output; simpler than client-side |

---

## Confidence Assessment (v1.1 Additions)

| Component | Confidence | Notes |
|-----------|------------|-------|
| Document parsing | MEDIUM | pdfplumber/python-docx are well-established; pymupdf is stable. No recent disruptive changes expected. |
| Report generation (WeasyPrint) | MEDIUM | WeasyPrint is mature; Windows dependency can be tricky — flag as implementation concern |
| React file upload | HIGH | react-dropzone is industry standard; no significant alternatives |
| Graph visualization | MEDIUM | react-force-graph is strong choice but verify it handles large Neo4j result sets gracefully |
| Frontend stack (React/Vite/AntD/Recharts) | HIGH | Already validated in v1.0 planning |

---

## Sources

**Cannot verify via external tools (WebSearch/MCP unavailable).** The following are based on training knowledge and should be verified before finalizing:

- pdfplumber: https://github.com/jsvine/pdfplumber (verify current version, Windows compatibility)
- pymupdf: https://pymupdf.io/ (verify v1.24+ features)
- python-docx: https://python-docx.readthedocs.io/ (verify current version)
- WeasyPrint: https://doc.courtbouillon.org/weasyprint/ (verify Windows installation requirements)
- react-force-graph: https://github.com/vasturiano/react-force-graph (verify bundle size, React 18/19 compatibility)
- react-dropzone: https://react-dropzone.js.org/ (verify React 18/19 compatibility)

**Verified by project constraints (v1.0):**
- FastAPI, ChromaDB, Neo4j, DeepSeek, BGE-m3 — already validated and in use
- Ant Design, Recharts — confirmed in CLAUDE.md and v1.0 decisions

---

*v1.1 stack additions research for: AI Career Planning Agent*
*Researched: 2026-03-30*
