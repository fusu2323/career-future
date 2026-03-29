# Phase 1: 数据清洗与处理 - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

将原始Excel数据（9958条）清洗为干净的结构化数据集，输出干净的10K条数据。目标是数据集完整率≥99%，字段填充率≥95%。此阶段为所有下游阶段（向量库、岗位画像、匹配引擎）提供干净的数据基础。

</domain>

<decisions>
## Implementation Decisions

### 数据存储格式
- **D-01:** 清洗后的数据存储为JSON文件（`data/processed/jobs_cleaned.json`）
- 理由：简单直接，便于调试，Phase 2直接读取
- 每个岗位为独立JSON对象，整体为JSON数组

### 薪资标准化
- **D-02:** 薪资范围统一转为「月薪×12」计算口径
  - 日薪×22×12，月薪直接×12，年薪÷12
  - 输出字段：`salary_min_monthly`, `salary_max_monthly`（单位：元/月）
  - 保留原始薪资文本字段 `salary_original`
- 理由：统一口径后便于后续匹配算法比较

### 缺失数据处理
- **D-03:** 缺失岗位详情的记录保留，标注为 `"data_quality": "incomplete"`
- 不删除记录，保留数据完整性
- 理由：9958条数据宝贵，后续Phase可根据需要过滤或补充

### 公司规模标准化
- **D-04:** 公司规模映射为数字区间，输出 `company_size_min`, `company_size_max`（单位：人）
  - "20-99人" → 20, 99
  - "1000-9999人" → 1000, 9999
  - "少于20人" → 0, 19
  - "10000人以上" → 10000, null（无上限）
- 保留原始文本字段 `company_size_original`

### 行业分类处理
- **D-05:** 保留多级行业标签，存入列表字段 `industry_tags`
- "计算机软件,互联网,IT服务" → ["计算机软件", "互联网", "IT服务"]
- 提取第一个作为主分类 `industry_primary`

### 地址字段标准化
- **D-06:** 地址拆分为「城市-区域」两级
  - "东莞-虎门镇" → `city`: "东莞", `district`: "虎门镇"
  - "广州-天河区" → `city`: "广州", `district`: "天河区"
  - 无区域时 district 设为 null
- 保留原始地址文本字段 `address_original`

### 岗位详情清洗
- **D-07:** 岗位详情（岗位描述）中去除HTML标签（`<br>`等）
- 保留纯文本内容

### 重复检测
- **D-08:** 基于「职位编码」字段去重，保留第一条
- 检测到重复时记录到 `data/processed/duplicates.json`

### 输出文件结构
- **D-09:** 输出文件：
  - `data/processed/jobs_cleaned.json` — 清洗后的完整数据
  - `data/processed/duplicates.json` — 重复记录（如有）
  - `data/processed/cleaning_report.json` — 清洗报告（记录数/字段填充率/异常值统计）

### 清洗质量指标
- **D-10:** 数据集完整率≥99%（9958条中至少9857条可用）
- **D-11:** 字段填充率≥95%（每个字段缺失值比例≤5%）
- **D-12:** 薪资标准化覆盖率≥95%（无法识别的格式记录到日志）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/ROADMAP.md` §Phase 1 — Phase 1目标、成功标准、依赖关系
- `.planning/REQUIREMENTS.md` §TECH-04 — 数据清洗需求定义
- `.planning/research/STACK.md` — 技术栈选型（Embedding、向量库等）
- `C:/Users/Administrator/Desktop/职引未来/20260226105856_457.xls` — 原始数据文件

</canonical_refs>

<codebase_context>
## Existing Code Insights

### Reusable Assets
- 无现有代码（greenfield项目）

### Established Patterns
- 无（Phase 1是最先执行的阶段）

### Integration Points
- Phase 2（岗位向量数据库）依赖 `data/processed/jobs_cleaned.json`
- Phase 3（岗位画像构建）依赖 `data/processed/jobs_cleaned.json`
- Phase 4（岗位图谱）依赖 `data/processed/jobs_cleaned.json`

</codebase_context>

<specifics>
## Specific Ideas

- 数据文件位置：`C:/Users/Administrator/Desktop/职引未来/20260226105856_457.xls`
- 数据格式：Excel (.xls)，9958条记录，12个字段
- 字段：岗位名称、地址、薪资范围、公司名称、所属行业、公司规模、公司类型、岗位编码、岗位详情、更新日期、公司详情、岗位来源地址

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---
*Phase: 01-data-cleaning*
*Context gathered: 2026-03-29*
