# Phase 3: 岗位画像构建 - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

从9178条清洗后岗位数据（`jobs_cleaned.json`）中，通过LLM分析抽取典型岗位特征，构建≥10个标准岗位画像，每个画像7个维度完整。为后续人岗匹配（Phase 8）提供岗位标准参照。

**Scope:**
- 从数据中自动发现典型岗位类型（不是预定义）
- 每个画像7个维度：专业技能、证书要求、创新能力、学习能力、抗压能力、沟通能力、实习能力
- 画像准确率≥90%
- 输出JSON + Neo4j双存储，供Phase 4图谱和Phase 8匹配使用

**Out of scope:**
- 晋升图谱和换岗图谱（Phase 4负责）
- 人岗匹配逻辑（Phase 8负责）
- 前端展示（Phase 10负责）

</domain>

<decisions>
## Implementation Decisions

### 岗位选取策略
- **D-01:** 从9178条真实数据中按岗位名称词频统计，自动发现热门岗位类型
  - 合并相似表述（如"Web前端开发"和"前端开发"归为一类）
  - 取TOP-K（≥10个）最常见的岗位类型
  - 理由：按实际热门岗位确定，而非预设，确保画像有数据支撑

### 画像生成方式
- **D-02:** LLM直接分析真实数据后生成
  - 将同类岗位的多条记录（如100条"Java开发"）发给LLM
  - LLM综合分析生成标准画像，包含每个维度的具体描述和熟练度要求
  - 理由：能捕捉真实招聘需求的细微差别，比模板填充更准确

### 输出格式与存储
- **D-03:** JSON + Neo4j双存储
  - JSON文件（`data/processed/job_profiles.json`）：主要数据文件，包含所有画像的完整7维数据
  - Neo4j节点：存储岗位类型节点，属性含画像摘要（供Phase 4图谱衔接）
  - 理由：Phase 4需要Neo4j存储图关系，但JSON更易于Phase 8匹配引擎读取

### LLM调用策略
- **D-04:** 分步调用（结构化提取+综合生成）
  - Step 1：LLM从同类岗位数据中提取关键信息（技能词频、学历要求、薪资范围、工作年限等）
  - Step 2：基于提取的结构化数据，LLM生成完整的7维画像
  - 理由：复杂任务拆分，每次调用数据量小，更易调试和追踪

### 画像维度定义
- **D-05:** 7个维度统一标准
  - 专业技能：硬技能（编程语言/工具/框架）、软技能
  - 证书要求：行业认可证书（如PMP、软考、CFA等）
  - 创新能力：岗位对创新思维的要求程度（1-5分）
  - 学习能力：持续学习要求程度（1-5分）
  - 抗压能力：工作压力强度（1-5分）
  - 沟通能力：团队协作和沟通要求（1-5分）
  - 实习能力：实习/项目经验对岗位的重要性（1-5分）

### 画像质量标准
- **D-06:** 画像准确率≥90%
  - 通过抽样人工评估验证
  - 关键信息（技能列表、学历要求、薪资范围）与原始数据偏差≤10%

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Context
- `.planning/phases/01-data-cleaning/01-CONTEXT.md` — 数据清洗输出格式，`jobs_cleaned.json`结构
- `.planning/phases/02-job-vector-db/02-CONTEXT.md` — ChromaDB向量库决策（用于参考检索方式）
- `.planning/ROADMAP.md` §Phase 3 — 阶段目标、成功标准
- `.planning/REQUIREMENTS.md` §JOB-01 — 岗位画像需求定义
- `.planning/REQUIREMENTS.md` §TECH-01 — LLM调用封装（Phase 5，但决策影响Phase 3设计）

### Data Files
- `data/processed/jobs_cleaned.json` — 清洗后的岗位数据（9178条）
- `data/processed/cleaning_report.json` — 清洗质量报告

### Prior Phases Integration
- Phase 1提供清洗后数据（9178条）
- Phase 2提供向量检索能力（画像构建完成后可用于验证相似度）
- Phase 4将基于画像构建图谱
- Phase 8将使用画像进行人岗匹配

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 无现有岗位画像代码（greenfield）
- Phase 1的`jobs_cleaned.json`读取模式可参考
- Phase 2的LLM调用模式可参考

### Established Patterns
- JSON文件作为数据交换格式
- DeepSeek API调用（Phase 5封装，但Phase 3可以直接调用）

### Integration Points
- 输入：`data/processed/jobs_cleaned.json`
- 输出：`data/processed/job_profiles.json` + Neo4j节点
- Phase 4：Neo4j节点用于构建晋升/换岗图谱
- Phase 8：JSON画像用于人岗匹配计算

</code_context>

<specifics>
## Specific Ideas

无特殊要求 — 按上述决策执行即可。

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---
*Phase: 03-job-profiling*
*Context gathered: 2026-03-30*
