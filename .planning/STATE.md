## Translated from English

---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: MVP
status: v1.0 milestone complete
last_updated: "2026-03-30T15:11:52.898Z"
progress:
  total_phases: 5
  completed_phases: 5
  total_plans: 9
  completed_plans: 9
---

# 项目状态

**项目：** 基于AI的大学生职业规划智能体
**当前版本：** v1.0 MVP (已发布 2026-03-30)
**下一步：** v1.1 (Phase 6-10)

## 项目参考

参见：`.planning/PROJECT.md`（更新于 2026-03-30 after v1.0）

**核心价值：** 帮助大学生从"盲目规划"走向"精准匹配"——通过AI分析让学生清楚知道自己"能做什么"、"缺什么"、"该怎么补"。

## v1.0 已交付

| 阶段 | 交付内容 |
|------|---------|
| Phase 1 | 9178条清洗后记录，780条重复记录，薪资标准化覆盖率97.43% |
| Phase 2 | ChromaDB向量索引（9178条，BGE-m3嵌入，Top10召回率100%） |
| Phase 3 | 12个岗位画像，7维度完整 |
| Phase 4 | Neo4j图谱（晋升路径+换岗血缘） |
| Phase 5 | DeepSeek LLM服务、FastAPI路由、22个测试 |

## v1.1 待启动

| 阶段 | 目标 |
|------|------|
| Phase 6 | 简历解析服务（PDF/DOCX→LLM解析） |
| Phase 7 | 学生能力画像生成（7维画像+评分） |
| Phase 8 | 人岗匹配引擎（4维度量化匹配） |
| Phase 9 | 职业报告生成（路径规划+行动计划+导出） |
| Phase 10 | 前端界面（简历上传/画像展示/图谱可视化） |

## 活跃问题

- **技术债**: app/config.py 使用已废弃的 `class Config`（Pydantic V2迁移到ConfigDict）
- **数据差异**: 9178条vs计划9857条（原始数据真实重复导致）

## 决策记录（v1.0）

- 薪资标准化：月薪口径（元直接用，元/天×22，年薪÷12）
- 地址拆分：城市-区域两级
- 行业标签：逗号分隔列表，首个为主行业
- 去重策略：基于职位编码，保留首条
- 嵌入：SiliconFlow BGE-m3 API（vs 本地BGE-large-zh 4-12小时）
- LLM：DeepSeek deepseek-chat，重试3x，超时差异化（profile=15s/match=20s/report=45s）

---
*状态文件：2026-03-29 初始化*
*最后更新：2026-03-30 v1.0里程碑完成*
