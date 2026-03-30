# 项目：基于AI的大学生职业规划智能体

**核心价值：** 帮助大学生从"盲目规划"走向"精准匹配"——通过AI分析让学生清楚知道自己"能做什么"、"缺什么"、"该怎么补"。
**当前版本：** v1.0 MVP (shipped 2026-03-30)
**下一步：** v1.1 (Phases 6-10: 简历解析→学生画像→匹配引擎→报告生成→前端界面)

---

## 当前里程碑：v1.1 核心功能交付

**目标：** 完成简历解析→学生画像→人岗匹配→职业报告的完整链路

**目标功能：**
- **Phase 6**: 简历解析服务 — PDF/DOCX上传 + LLM解析 → 结构化能力数据
- **Phase 7**: 学生能力画像生成 — 7维画像 + 完整度评分 + 竞争力评分
- **Phase 8**: 人岗匹配引擎 — 4维度量化匹配 + 差距分析
- **Phase 9**: 职业报告生成 — 路径规划 + 行动计划 + 评估指标 + 导出
- **Phase 10**: 前端界面 — 简历上传 / 画像展示 / 图谱可视化 / 匹配结果 / 报告编辑导出

---

## 当前状态

**技术栈：** Python 3.11+ / FastAPI / ChromaDB / Neo4j / DeepSeek (LLM)
**已交付：** 9178条清洗后数据、ChromaDB向量索引（9178条）、12个岗位画像、Neo4j图谱、LLM服务（DeepSeek封装）、FastAPI HTTP接口、22个测试
**待开发：** 简历解析、学生画像、匹配引擎、报告生成、前端界面

---

## 需求

### 已验证 (v1.1)

- ✅ **STU-01**: 简历解析服务——PDF/DOCX上传→LLM解析→结构化能力数据 (Phase 6)

### 已验证 (v1.0)

- ✅ **TECH-04**: 数据清洗——9178条清洗后记录，780条重复记录，薪资标准化覆盖率97.43% (v1.0)
- ✅ **TECH-02**: ChromaDB向量索引——9178条岗位记录索引，BGE-m3嵌入（SiliconFlow API），Top10召回率100% (v1.0)
- ✅ **JOB-01**: 岗位画像构建——12个岗位画像，7维度完整 (v1.0)
- ✅ **JOB-02**: 垂直晋升图谱——Neo4j图谱，≥5岗位×2路径 (v1.0)
- ✅ **JOB-03**: 换岗路径图谱——单图双关系类型 (v1.0)
- ✅ **TECH-01**: LLM服务封装——DeepSeek客户端、重试/超时/JSON解析重试、FastAPI路由、22个测试 (v1.0)

### 进行中 (v1.1)

- [ ] **STU-02**: 学生能力画像生成——7维画像+完整度评分+竞争力评分
- [ ] **STU-02**: 学生能力画像生成——7维画像+完整度评分+竞争力评分
- [ ] **MATCH-01**: 人岗匹配引擎——4维度量化匹配+差距分析
- [ ] **REPORT-01**: 职业报告生成——路径规划+行动计划+评估指标+导出
- [ ] **UI-01**: 前端界面——简历上传/画像展示/图谱可视化/匹配结果/报告编辑导出

### 范围之外

- 用户登录/注册系统——聚焦核心匹配与报告功能
- 移动端原生应用——Web端优先
- 多语言支持——中文单语言
- 实时招聘平台对接——使用离线数据

---

## 关键决策

| 决策 | 理由 | 状态 |
|------|------|------|
| LLM: DeepSeek | 性价比高，API便宜，中文能力好 | ✅ 已验证 |
| 前端: React + Ant Design | 生态丰富，组件完善，适合快速开发 | ⚠️ 待确认 |
| 向量DB: ChromaDB | 已有技术积累，支持本地部署 | ✅ 已验证 |
| 图DB: Neo4j | 已有技术积累，Cypher适合路径查询 | ✅ 已验证 |
| 后端: FastAPI + Python | 轻量异步，接口规范，现有代码可复用 | ✅ 已验证 |
| 嵌入: SiliconFlow BGE-m3 API | 本地BGE-large-zh CPU太慢（4-12小时），API约5分钟 | ✅ 已验证 |
| 薪资标准化: 月薪口径 | 元直接用，元/天×22，年薪÷12 | ✅ 已验证 |
| 地址拆分: 城市-区域两级 | 区域可为空，灵活适配 | ✅ 已验证 |
| 去重策略: 职位编码去重 | 保留首条，重复记录单独保存 | ✅ 已验证 |
| LLM重试: 3x (1s/2s/4s) | 平衡延迟与可靠性 | ✅ 已验证 |
| LLM超时: profile=15s, match=20s, report=45s | 按任务复杂度差异化 | ✅ 已验证 |
| JSON解析重试: 1-2x | LLM输出格式容错 | ✅ 已验证 |

---

## 技术债

- `app/config.py` 使用已废弃的 `class Config`（Pydantic V2，应迁移到 `ConfigDict`）
- Phase 4 Neo4j节点未从 job_profiles.json 自动写入（需手动或脚本触发）
- Phase 2/3/4 缺少正式 UAT/VERIFICATION 文档

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

### Phase 6 简历解析
- pdfplumber+python-docx文件提取/DeepSeek generate_structured调用/resume timeout=20s/自修正prompt+部分降级/resume_models对齐Phase7七维画像

### Phase 5 LLM服务
- DeepSeek deepseek-chat/base_url https://api.deepseek.com/HTTP retry 3x/retry on 5xx/503/429/timeout NOT on 400/401/per-task timeout/profile=15s match=20s report=45s/JSON parse retry 1-2x

---

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*最后更新：2026-03-31 after Phase 6 complete*
