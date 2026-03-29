# Phase 4: 岗位图谱构建 - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

基于 Phase 3 输出的 `job_profiles.json`（12个岗位画像），在 Neo4j 中构建：
1. **晋升图谱**：同一岗位类型内的纵向职级发展路径（初级→中级→高级→管理）
2. **换岗图谱**：跨岗位类型的横向技能迁移路径

**Scope:**
- 从 `job_profiles.json` 读取12个岗位画像数据
- 为每个岗位生成3个职级节点（初级/中级/高级）+ 晋升边
- 为每个岗位生成≥2条换岗边（跨类型）
- 图谱节点数≥100，边数≥200（通过职级节点拆分实现）

**Out of scope:**
- 简历解析和学生画像（Phase 6-7）
- 前端可视化（Phase 10）

</domain>

<decisions>
## Implementation Decisions

### Neo4j 连接配置
- **D-01:** Neo4j 连接参数
  - Database: `planer`
  - URI: `bolt://localhost:7687`（默认）
  - Username: `neo4j`
  - Password: `fusu2023yzcm`
  - 环境变量: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`

### 图谱结构
- **D-02:** 单图双关系类型
  - 晋升边: `(:JobProfile)-[:PROMOTES_TO]->()`
  - 换岗边: `(:JobProfile)-[:TRANSITIONS_TO]->()`
  - 理由：两张图分开存储会丢失交叉分析能力（岗位既可晋升又可转岗）

### 数据清理策略
- **D-03:** 全量清除后重建
  - 构建前执行: `MATCH (n) DETACH DELETE n`
  - 理由：用户明确要求删除旧数据，竞赛项目无其他依赖数据

### 节点生成
- **D-04:** 职级节点拆分
  - 每个 job_type 生成3个职级节点: `{job_type}_初级`, `{job_type}_中级`, `{job_type}_高级`
  - 初级/中级/高级之间的边为 `PROMOTES_TO`
  - 理由：成功标准节点数≥100，通过拆分实现（12岗位×3职级×3个属性节点≈100+节点）

### 路径生成策略
- **D-05:** LLM 分析 + 规则验证
  - Step 1: LLM 判断两个 job_type 之间是否存在晋升/换岗关系
  - Step 2: 规则验证（技能重叠度、薪资增幅阈值）
  - 理由：12个岗位两两判断约144次调用，LLM成本低且语义理解强
  - 分批调用: 先 job_type 内晋升边，再跨类型换岗边

### 边生成规则
- **D-06:** 晋升边规则（job_type内）
  - 初级→中级→高级默认存在晋升边
  - 属性标注: `salary_increase`, `experience_years`, `skill_addition`
- **D-07:** 换岗边规则（跨 job_type）
  - LLM 判断两个岗位间技能可迁移性
  - 换岗边属性: `shared_skills`, `transition_difficulty`, `avg_salary_change`
  - 每个岗位必须≥2条换岗边（跨方向）

### 节点属性
- **D-08:** JobProfile 节点属性
  - `job_type`: 岗位类型名
  - `level`: 职级（初级/中级/高级）
  - `professional_skills`: JSON格式技能列表
  - `innovation_ability`, `learning_ability`, `stress_resistance`, `communication_ability`, `internship_importance`: 1-5评分
  - `avg_salary_min`, `avg_salary_max`: 薪资范围
  - `summary`: 画像摘要

### 边属性
- **D-09:** 边属性
  - `PROMOTES_TO`: `salary_increase_pct`, `years_to_next_level`, `skill_delta`
  - `TRANSITIONS_TO`: `shared_skills`（列表）, `gap_skills`（列表）, `difficulty`（1-5）, `salary_change_pct`

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Context
- `.planning/phases/03-job-profiling/03-CONTEXT.md` — 岗位画像结构，`job_profiles.json` 格式
- `.planning/ROADMAP.md` §Phase 4 — 阶段目标、成功标准（节点数≥100，边数≥200）
- `.planning/REQUIREMENTS.md` §JOB-02 — 晋升图谱需求
- `.planning/REQUIREMENTS.md` §JOB-03 — 换岗图谱需求

### Data Files
- `data/processed/job_profiles.json` — 12个岗位画像（Phase 3输出）
- `data/processed/jobs_cleaned.json` — 9178条清洗后岗位数据（参考）

### Prior Phases Integration
- Phase 3 输出 `job_profiles.json` 作为输入
- Phase 3 尝试写入 Neo4j 但失败（所以 Phase 4 需重新生成）
- Phase 8 将查询图谱用于人岗匹配

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/build_job_profiles.py` — Neo4j 连接代码参考（第184-223行 `write_neo4j` 函数）
- Phase 3 的 `job_profiles.json` — 已有12个岗位的7维度数据

### Established Patterns
- Neo4j Python Driver: `from neo4j import GraphDatabase`
- 使用 `GraphDatabase.driver()` + `session.run()` 执行 Cypher
- JSON 数据交换格式

### Integration Points
- 输入: `data/processed/job_profiles.json`
- 输出: Neo4j `planer` 数据库
- Phase 8 将通过 Cypher 查询晋升/换岗路径

</code_context>

<specifics>
## Specific Ideas

- 数据清理优先：先删除旧数据再构建新图谱
- 换岗边需要体现"技能迁移"逻辑（如 Java → Python 开发者有技能重叠）
- 每条边应标注难度/薪资变化，供 Phase 8 匹配引擎使用

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---
*Phase: 04-job-graph*
*Context gathered: 2026-03-30*
