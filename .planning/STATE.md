---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Executing Phase 05
last_updated: "2026-03-30T14:45:25Z"
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 9
  completed_plans: 9
---

# 项目状态

**项目：** 基于AI的大学生职业规划智能体
**当前阶段：** 5 - LLM服务封装
**当前计划：** 05-03 (Unit and Integration Tests)
**模式：** YOLO

## 项目参考

参见：`.planning/PROJECT.md`（更新于 2026-03-29）

**核心价值：** 帮助大学生从"盲目规划"走向"精准匹配"——通过AI分析让学生清楚知道自己"能做什么"、"缺什么"、"该怎么补"。
**当前重点：** Phase 2 上下文已捕获（ChromaDB + BGE-large-zh + 拼接式全文嵌入）

## 阶段状态

| # | 阶段 | 状态 | 进度 | 阻塞 |
|---|------|------|------|------|
| 1 | 数据清洗与处理 | ● 完成 | 100% | — |
| 2 | 岗位向量数据库构建 | ● 完成 | 100% (1/1) | Phase 1 |
| 3 | 岗位画像构建 | ● 完成 | 100% (3/3) | Phase 1, 2 |
| 4 | 岗位图谱构建 | ◐ 已规划 | 1/1 | Phase 1, 3 |
| 5 | LLM服务封装 | ● 完成 | 100% (3/3) | — |
| 6 | 简历解析服务 | ○ 待启动 | 0% | Phase 5 |
| 7 | 学生能力画像生成 | ○ 待启动 | 0% | Phase 5, 6 |
| 8 | 人岗匹配引擎 | ○ 待启动 | 0% | Phase 3, 7 |
| 9 | 职业报告生成 | ○ 待启动 | 0% | Phase 5, 8 |
| 10 | 前端界面开发 | ○ 待启动 | 0% | Phase 2-9 |

## 最近更新

- **2026-03-30：** Phase 5 Plan 1 执行完成：LLM服务基础设施（generate_structured/DeepSeek client/Pydantic models/异常类型），HTTP retry 3x (1s/2s/4s)/per-task timeout (profile=15s, match=20s, report=45s)/JSON parse retry 1-2x。auto-fix: lazy Settings loading。
- **2026-03-30：** Phase 4 上下文已捕获：单图双关系类型(PROMOTES_TO/TRANSITIONS_TO)/LLM分析生成路径/职级节点拆分(12岗位×3职级)/MATCH (n) DETACH DELETE n全量清理/Neo4j库planer(neo4j/fusu2023yzcm)
- **2026-03-29：** Phase 2 Plan 1 执行完成：9178条岗位记录已索引至ChromaDB（SiliconFlow BGE-m3 API ~5分钟，本地BGE-large-zh需4-12小时），Top10召回率100%（超85%目标）。偏离计划：使用SiliconFlow API代替本地BGE-large-zh。
- **2026-03-29：** Phase 1 Plan 1 执行完成：9178条清洗后记录，780条重复记录，薪资标准化覆盖率97.43%
- **2026-03-29：** Phase 1上下文已捕获：数据存储JSON/薪资标准化月薪口径/缺失标记保留/公司规模数字区间/地址拆分为城市-区域
- **2026-03-29：** Phase 2上下文已捕获：BGE-large-zh嵌入模型/拼接式全文嵌入/ChromaDB metadata过滤/HNSW ANN检索

## 活跃问题

- **数据完整性差异：** 清洗后记录数9178条，低于计划预期的9857条（99%完整性）。原因：原始数据中存在780个重复职位编码，按计划要求已去重。

## 决策记录

- 薪资标准化：统一转为月薪口径（元直接用，元/天×22，年薪÷12）
- 地址拆分：城市-区域两级，区域可为空
- 行业标签：逗号分隔列表，首个为主行业
- 去重策略：基于职位编码，保留首条，后续重复记录单独保存
- **Phase 2 向量库**：SiliconFlow BGE-m3 API嵌入（因本地BGE-large-zh CPU太慢 4-12小时）/拼接式全文嵌入/ChromaDB metadata过滤/HNSW ANN检索
- **Phase 3 画像**：12个岗位画像/professional_skills分core/soft/tools三层/7维度评分1-10分/avg_salary为min-max范围/innovation_learning抗压沟通实习重要性各维度/Neo4j节点未写入（Phase 4需处理）
- **Phase 4 图谱**：Neo4j库planer(neo4j/fusu2023yzcm)/单图双关系PROMOTES_TO+TRANSITIONS_TO/职级节点初级-中级-高级拆分/LLM生成晋升+换岗路径/全量清理MATCH (n) DETACH DELETE n
- **Phase 5 LLM服务**：DeepSeek deepseek-chat/base_url https://api.deepseek.com/HTTP retry 3x (1s/2s/4s backoff)/retry on 5xx/503/429/timeout, NOT on 400/401/per-task timeout (profile=15s, match=20s, report=45s)/JSON parse retry 1-2x/asyncio.to_thread for sync SDK
- **Phase 5 Plan 2 路由**：POST /llm/profile/generate|/llm/match/analyze|/llm/report/generate (task_type implicit per path)/GET /health (liveness, no DeepSeek)/GET /health/ready (readiness probe, max_tokens=5, timeout=5s)/返回503 if DeepSeek unreachable/_handle_llm_error() DRY helper maps 504/422/502
- **Phase 5 Plan 3 测试**：pytest配置/asyncio_mode=auto/5个fixtures (mock_deepseek_client, mock_deepseek_client_json_fail, mock_timeout_client, mock_500_client, mock_400_client)/13个单元测试 (retry/timeout/JSON parse retry)/10个集成测试 (HTTP endpoints)/auto-fix: tenacity _retry_if_retryable_http_error predicate防止400/401被retry

---
*状态文件：2026-03-29 初始化*
*最后更新：2026-03-30 Phase 5 Plan 3 执行完成*
