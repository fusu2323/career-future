# Phase 2: 岗位向量数据库构建 - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

将清洗后的岗位数据（9178条）接入ChromaDB，建立向量索引，支持语义检索。目标召回Top10相关岗位准确率≥85%。此阶段为后续岗位画像（Phase 3）和人岗匹配（Phase 8）提供向量检索基础。

</domain>

<decisions>
## Implementation Decisions

### Embedding Model
- **D-01:** 使用 **BGE-large-zh** (FlagEmbedding) 作为嵌入模型
  - 理由：最佳中文语义匹配性能，开源，与项目技术栈一致
  - 维度：~1024维
  - 备选：text-embedding-3-small（中文较弱）、M3E（速度更快但质量略低）

### Text Preparation Strategy
- **D-02:** 拼接式全文嵌入（Concatenated Full Record）
  - 将岗位名称、公司名称、行业标签、岗位详情拼接为单一文本字符串
  - 格式：`{job_title} | {company_name} | {industry_tags} | {job_detail}`
  - 理由：简单有效，与BGE-large-zh配合良好
  - 不采用：分字段分别嵌入（复杂且收益不明显）

### Metadata Filtering
- **D-03:** ChromaDB原生metadata过滤
  - 将城市（city）、薪资范围（salary_min/max）、行业（industry_primary）等作为metadata存储
  - 查询时使用ChromaDB的`where`子句进行预过滤
  - 理由：简单直接，ChromaDB支持良好
  - 备选：预过滤方式（更复杂，未采用）

### Retrieval Strategy
- **D-04:** 纯向量 ANN 检索（Approximate Nearest Neighbor）
  - 使用ChromaDB默认HNSW索引
  - 理由：10K规模下HNSW精度与速度平衡良好
  - 备选：精确搜索（ overkill for 10K）、混合搜索（需额外索引，未采用）

### Collection Schema
- **D-05:** ChromaDB Collection 设计
  - Collection名称：`job_postings`
  - 向量字段：`embedding`（BGE-large-zh输出，~1024维）
  - Metadata字段：`job_id`, `title`, `company_name`, `city`, `district`, `industry_primary`, `salary_min_monthly`, `salary_max_monthly`, `company_size_min`, `company_size_max`
  - 原始文本（用于display）：`text`（拼接后的全文）

### Integration Point
- **D-06:** 数据来源
  - 输入：`data/processed/jobs_cleaned.json`（Phase 1输出，9178条记录）
  - 输出集合：`job_postings`（约9178条向量记录）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Context
- `.planning/phases/01-data-cleaning/01-CONTEXT.md` — Phase 1数据清洗输出格式，`jobs_cleaned.json`结构
- `.planning/ROADMAP.md` §Phase 2 — 阶段目标、成功标准
- `.planning/REQUIREMENTS.md` §TECH-02 — ChromaDB向量索引需求
- `.planning/research/STACK.md` — 技术栈选型（ChromaDB、BGE-large-zh）

### Data Files
- `data/processed/jobs_cleaned.json` — 清洗后的岗位数据（9178条）
- `data/processed/cleaning_report.json` — 清洗质量报告

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 无现有向量数据库代码（greenfield）

### Established Patterns
- Phase 1数据清洗输出JSON格式已定义
- `scripts/data_cleaning.py` 存在但仅用于Phase 1

### Integration Points
- Phase 3（岗位画像）将依赖ChromaDB向量检索
- Phase 8（人岗匹配）将使用向量检索获取相关岗位
- FastAPI后端（Phase 5+）将通过API调用ChromaDB

</code_context>

<specifics>
## Specific Ideas

无特殊要求 — 采用标准方法，灵活处理。

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---
*Phase: 02-job-vector-db*
*Context gathered: 2026-03-29*
