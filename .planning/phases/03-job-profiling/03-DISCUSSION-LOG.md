# Phase 3: 岗位画像构建 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 03-job-profiling
**Mode:** discuss

## Areas Discussed

### 1. 岗位选取策略

| Option | Description | Selected |
|--------|-------------|----------|
| 按数据中实际热门岗位确定 | 根据9178条数据中的岗位名称出现频率，取TOP-K最常见的岗位，让LLM分析真实数据中的共同特征 | ✓ |
| 预定义标准岗位类型 | 根据行业常识预设10-15个标准岗位，再去数据中匹配 | |

**User's choice:** 按数据中实际热门岗位确定

### 2. 画像生成方式

| Option | Description | Selected |
|--------|-------------|----------|
| LLM分析真实数据后直接生成 | 将同类岗位的多条记录一起发给LLM，LLM综合分析生成标准画像 | ✓ |
| 先定义模板再填充数据 | 每个维度有预定义评分标准，LLM统计同类岗位数据后填入模板 | |

**User's choice:** LLM分析真实数据后直接生成

### 3. 输出格式与存储

| Option | Description | Selected |
|--------|-------------|----------|
| JSON文件 | 存储为JSON文件，便于后续API读取和Phase 8匹配引擎使用 | |
| Neo4j图数据库 | 岗位画像存入Neo4j作为节点，适合与Phase 4图谱衔接 | |
| JSON + Neo4j双存储 | JSON作为主要数据文件，Neo4j额外存储图关系 | ✓ |

**User's choice:** JSON + Neo4j双存储

### 4. LLM调用方式

| Option | Description | Selected |
|--------|-------------|----------|
| 每类岗位一次API调用 | 将某类岗位的全部数据拼接为一个长Prompt，生成一个完整画像 | |
| 分步调用（结构化提取+综合生成） | Step1提取关键信息，Step2基于结构化数据生成画像 | ✓ |

**User's choice:** 分步调用（结构化提取+综合生成）

## Deferred Ideas

None — discussion stayed within phase scope.
