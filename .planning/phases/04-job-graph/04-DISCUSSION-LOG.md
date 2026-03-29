# Phase 4: 岗位图谱构建 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 04-job-graph
**Areas discussed:** 图谱结构设计, 路径生成策略, 节点类型规划, 边生成规则, 数据清理策略

---

## Areas Discussed

### 图谱结构设计
| Option | Description | Selected |
|--------|-------------|----------|
| 单图双关系类型 | 同一张图用 PROMOTES_TO 和 TRANSITIONS_TO 两种边 | ✓ |
| 双图分区 | 用 graph_name 或独立数据库区分 | |
| 带标签子图 | 用 :PromotionPath 和 :TransitionPath 关系标签区分 | |

**User's choice:** 单图双关系类型
**Notes:** 两张图分开存储会丢失交叉分析能力，岗位既可晋升又可转岗

### 路径生成策略
| Option | Description | Selected |
|--------|-------------|----------|
| 基于技能相似度 | 计算技能重叠度，超过阈值则连边 | |
| 基于薪资+职级 | 薪资递增+职位级别上升定义为晋升 | |
| LLM分析 | LLM直接判断是否存在晋升/换岗关系 | ✓ |
| 混合策略 | LLM生成初始候选+规则过滤 | |

**User's choice:** LLM分析 + 规则验证
**Notes:** 12个岗位规模，LLM调用成本可接受，能捕捉语义关联

### 节点类型规划
| Option | Description | Selected |
|--------|-------------|----------|
| 仅JobProfile | 晋升/换岗关系直接连两个JobProfile节点 | ✓ |
| +Skill节点 | 用 :Skill 节点作为中间连接点 | |
| +SalaryLevel | 用薪资级别作为中间节点 | |
| +JobCategory | 按职业大类建立层级 | |

**User's choice:** 仅JobProfile（通过职级节点拆分实现节点数≥100）
**Notes:** 12岗位×3职级=36节点，加上属性节点可达到100+节点要求

### 边生成规则
| Option | Description | Selected |
|--------|-------------|----------|
| 硬编码阈值 | 技能重叠>60%=换岗边，薪资增幅>30%=晋升边 | |
| LLM生成边 | LLM直接判断任意两岗位间是否存在关系 | ✓ |
| 类型内路径 | 同一job_type内按薪资/经验自动生成晋升边 | |

**User's choice:** LLM逐对判断（144次调用，成本可接受）
**Notes:** 分批：先job_type内生成晋升边，再跨类型生成换岗边

### 数据清理策略
| Option | Description | Selected |
|--------|-------------|----------|
| DETACH DELETE全量清除 | MATCH (n) DETACH DELETE n | ✓ |
| 按标签删除 | MATCH (n:JobProfile) DETACH DELETE n | |
| 删除再重建DB | DROP DATABASE && CREATE DATABASE | |

**User's choice:** MATCH (n) DETACH DELETE n（全量清除）
**Notes:** 用户明确要求删除旧数据，竞赛项目数据量小，清理整个图谱没有损失

---

## Deferred Ideas

None — discussion stayed within phase scope.
