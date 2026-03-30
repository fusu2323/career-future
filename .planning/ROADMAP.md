# Roadmap: 基于AI的大学生职业规划智能体

**核心价值：** 帮助大学生从"盲目规划"走向"精准匹配"

## Milestones

- ✅ **v1.0 MVP** — Phases 1-5 (shipped 2026-03-30)
- 🚧 **v1.1 核心功能交付** — Phases 6-10 (in progress)

---

## Phases

- [ ] **Phase 6: 简历解析服务** - PDF/DOCX上传 + LLM解析 → 结构化能力数据
- [ ] **Phase 7: 学生能力画像** - 7维画像 + 完整度评分
- [ ] **Phase 8: 人岗匹配引擎** - 4维度量化匹配 + 差距分析 + Top-5推荐
- [ ] **Phase 9: 职业报告生成** - 路径规划 + 行动计划 + 评估指标 + PDF导出
- [ ] **Phase 10: 前端界面** - 简历上传/画像展示/图谱可视化/匹配结果/报告导出

---

## Phase Details

### Phase 6: 简历解析服务

**Goal**: User can upload a resume and receive structured parsed data (basic info, education, skills, experience)

**Depends on**: Phase 5 (LLM service infrastructure)

**Requirements**: STU-01, STU-02, STU-03, STU-04, STU-05

**Success Criteria** (what must be TRUE):

1. User can upload a PDF or DOCX resume file up to 10MB and receive successful parsing confirmation
2. User receives parsed basic info (name, education level, contact information) extracted by LLM
3. User receives parsed education history (school, major, GPA if available, enrollment/graduation years)
4. User receives parsed skills organized by category: core skills / soft skills / tools
5. User receives parsed experience data: internship, projects, extracurricular activities with dates and descriptions

**Plans**: 2

Plans:
- [ ] 06-01-PLAN.md — Wave 1: Infrastructure + Models + Router skeleton + Test scaffold
- [ ] 06-02-PLAN.md — Wave 2: Endpoint implementation + integration tests

### Phase 7: 学生能力画像

**Goal**: System generates a 7-dimension student ability profile with completeness scoring

**Depends on**: Phase 6 (parsed resume data)

**Requirements**: STU-06, STU-07

**Success Criteria** (what must be TRUE):

1. User receives a 7-dimension ability profile with ratings (1-5 scale) across: professional_skills (core+soft+tools), certificates (required+preferred), innovation, learning, stress_resistance, communication, internship
2. User receives a completeness score showing percentage of filled fields vs total fields

**Plans**: TBD

### Phase 8: 人岗匹配引擎

**Goal**: System performs 4-dimension quantitative matching and returns ranked job recommendations with gap analysis

**Depends on**: Phase 7 (student profile)

**Requirements**: MATCH-01, MATCH-02, MATCH-03

**Success Criteria** (what must be TRUE):

1. User receives 4-dimension match scores (0-100) for each dimension: 基础要求/职业技能/职业素养/发展潜力
2. User receives gap analysis in natural language listing missing required and preferred skills
3. User receives top-5 job recommendations ranked by aggregate score with per-dimension breakdown

**Plans**: TBD

### Phase 9: 职业报告生成

**Goal**: System generates a comprehensive career report with path planning, action plans, evaluation metrics, and gap remediation recommendations

**Depends on**: Phase 8 (matching results)

**Requirements**: REPORT-01, REPORT-02, REPORT-03, REPORT-04, REPORT-05

**Success Criteria** (what must be TRUE):

1. User receives career path plan retrieved from Neo4j graph: promotion paths and job transition bloodlines
2. User receives action plan organized by timeline: short-term (3 months) / medium-term (6 months) / long-term (1 year) learning activities
3. User receives evaluation metrics with success criteria for each milestone
4. User receives gap remediation recommendations with specific learning resources and certificate suggestions for each gap
5. User can export the complete career report as PDF

**Plans**: TBD

### Phase 10: 前端界面

**Goal**: User can interact with all backend services through a web interface (resume upload, profile visualization, career path graph, matching results, report export)

**Depends on**: Phases 6, 7, 8, 9 (all backend services)

**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05

**Success Criteria** (what must be TRUE):

1. User can upload resume via drag-and-drop interface supporting PDF and DOCX formats
2. User can view 7-dimension profile as radar chart visualization
3. User can view career path graph as interactive visualization
4. User can view matching results with gap analysis and top-5 recommendations
5. User can view and download complete career report as PDF

**Plans**: TBD
**UI hint**: yes

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|---------------|--------|-----------|
| 1 | v1.0 | 1/1 | Complete | 2026-03-29 |
| 2 | v1.0 | 1/1 | Complete | 2026-03-29 |
| 3 | v1.0 | 3/3 | Complete | 2026-03-30 |
| 4 | v1.0 | 1/1 | Complete | 2026-03-30 |
| 5 | v1.0 | 3/3 | Complete | 2026-03-30 |
| 6 | v1.1 | 0/2 | In planning | - |
| 7 | v1.1 | 0/TBD | Not started | - |
| 8 | v1.1 | 0/TBD | Not started | - |
| 9 | v1.1 | 0/TBD | Not started | - |
| 10 | v1.1 | 0/TBD | Not started | - |

---

## 依赖关系图

```
Phase1(数据清洗) ──┬──→ Phase2(向量库) ──→ Phase3(岗位画像) ──┬──→ Phase8(匹配引擎) ──→ Phase9(报告生成) ──┐
                   │                    │                      │                                      ↓
Phase5(LLM封装) ──┤                    │                      │                              Phase10(前端界面)
                   │                    │                      │
                   └──→ Phase6(简历解析) → Phase7(学生画像) ──┘
                            ↑
Phase4(图谱) ───────────────┘（图谱可与Phase3并行）
```

---

<details>
<summary>✅ v1.0 MVP (Phases 1-5) — SHIPPED 2026-03-30</summary>

### Phase 1：数据清洗与处理
**目标：** 将原始Excel数据（9958条）清洗为干净的结构化数据集
**输出：** 9178条清洗后记录（去重后），780条重复记录，薪资标准化覆盖率97.43%
**Plans:** [x] 01-01 — 数据清洗脚本

### Phase 2：岗位向量数据库构建
**目标：** 将清洗后的岗位数据接入ChromaDB，建立向量索引，支持语义检索
**输出：** 9178条岗位记录索引至ChromaDB，BGE-m3嵌入（SiliconFlow API），Top10召回率100%
**Plans:** [x] 02-01 — ChromaDB vector index with BGE-m3 embedding

### Phase 3：岗位画像构建
**目标：** 从10K数据中抽取典型岗位特征，构建≥10个标准岗位画像
**输出：** 12个岗位画像（data/processed/job_profiles.json），7维度完整，11项自动化测试全部通过
**Plans:** [x] 03-01 — Test infrastructure, [x] 03-02 — Profiling script, [x] 03-03 — Verification

### Phase 4：岗位图谱构建
**目标：** Neo4j中建立晋升路径图谱和换岗血缘图谱
**Plans:** [x] 04-01 — Job graph builder

### Phase 5：LLM服务封装
**目标：** 统一封装DeepSeek API，支持画像生成/匹配分析/报告生成调用
**输出：** DeepSeek客户端、Pydantic模型、重试/超时/JSON解析重试逻辑、FastAPI路由器、22个测试
**Plans:** [x] 05-01 — Core service infrastructure, [x] 05-02 — Router endpoints + health check, [x] 05-03 — Unit and integration tests

</details>

---

_路线图制定：2026-03-30 | 更新：2026-03-31 Phase 6 planning_
