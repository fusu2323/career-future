# 项目状态

**项目：** 基于AI的大学生职业规划智能体
**当前版本：** v1.1 (started 2026-03-30)
**下一步：** Phase 6 开始执行

---

## 当前阶段

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-03-30 — v1.1 milestone started

---

## 上下文积累

### Phase 1 数据清洗
- 数据存储JSON/薪资标准化月薪口径/缺失标记保留/公司规模数字区间/地址拆分为城市-区域

### Phase 2 向量库
- SiliconFlow BGE-m3 API嵌入/拼接式全文嵌入/ChromaDB metadata过滤/HNSW ANN检索

### Phase 3 画像
- 12个岗位画像/professional_skills分core/soft/tools三层/7维度评分1-10分

### Phase 4 图谱
- Neo4j库planer(neo4j/fusu2023yzcm)/单图双关系PROMOTES_TO+TRANSITIONS_TO/职级节点初级-中级-高级拆分

### Phase 5 LLM服务
- DeepSeek deepseek-chat/base_url https://api.deepseek.com/HTTP retry 3x/retry on 5xx/503/429/timeout NOT on 400/401/per-task timeout/profile=15s match=20s report=45s/JSON parse retry 1-2x

---

## 项目参考

参见：`.planning/PROJECT.md`（更新于 2026-03-30）

**核心价值：** 帮助大学生从"盲目规划"走向"精准匹配"——通过AI分析让学生清楚知道自己"能做什么"、"缺什么"、"该怎么补"。
**当前里程碑：** v1.1 核心功能交付
