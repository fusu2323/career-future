# Requirements: 基于AI的大学生职业规划智能体

**Defined:** 2026-03-30
**Core Value:** 帮助大学生从"盲目规划"走向"精准匹配"——通过AI分析让学生清楚知道自己"能做什么"、"缺什么"、"该怎么补"。
**Milestone:** v1.1

---

## v1.1 Requirements

### Resume Parsing (Phase 6)

- [x] **STU-01**: User can upload PDF or DOCX resume file — 文件上传 endpoint，10MB限制，pdfplumber解析PDF，python-docx解析DOCX
- [x] **STU-02**: User receives parsed basic info — 姓名、学历、联系方式 from LLM extraction
- [x] **STU-03**: User receives parsed education history — 学校、专业、 GPA（如有）、入学毕业年份
- [x] **STU-04**: User receives parsed skills with categorization — core skills / soft skills / tools 三层分类
- [x] **STU-05**: User receives parsed experience data — 实习经历、项目经验、课外活动 with 时间 and 描述

### Student Ability Profiling (Phase 7)

- [ ] **STU-06**: System generates 7-dimension student profile — professional_skills (core+soft+tools), certificates (required+preferred), innovation, learning, stress_resistance, communication, internship 各维度评分 1-5
- [ ] **STU-07**: System calculates and returns completeness score — 已填充字段 / 总字段 百分比

### Matching Engine (Phase 8)

- [ ] **MATCH-01**: System performs 4-dimension quantitative matching — 基础要求/职业技能/职业素养/发展潜力 each dimension scored 0-100
- [ ] **MATCH-02**: System generates gap analysis — LLM-generated natural language: "Missing: Python (required), SQL (preferred)"
- [ ] **MATCH-03**: System returns top-5 job recommendations — ranked by aggregate score with per-dimension breakdown

### Career Report (Phase 9)

- [ ] **REPORT-01**: System generates career path plan — 从 Neo4j 图谱 retrieval: 晋升路径 + 换岗血缘
- [ ] **REPORT-02**: System generates action plan with timelines — 短期(3个月)/中期(6个月)/长期(1年) 学习活动
- [ ] **REPORT-03**: System generates evaluation metrics — 每个 milestone 的成功标准
- [ ] **REPORT-04**: System returns gap remediation recommendations — 针对每个 gap 的具体学习资源和证书建议
- [ ] **REPORT-05**: System exports report as PDF — WeasyPrint HTML-to-PDF or browser print

### Frontend (Phase 10)

- [ ] **UI-01**: User can upload resume via drag-and-drop interface — React + react-dropzone，PDF/DOCX 支持
- [ ] **UI-02**: User can view 7-dimension profile as radar chart — recharts RadarChart，可视化 STU-06 输出
- [ ] **UI-03**: User can view career path graph — react-force-graph，可视化 REPORT-01 路径
- [ ] **UI-04**: User can view matching results with gap analysis — 匹配分数 + gap list + top-5 推荐
- [ ] **UI-05**: User can view and download career report — PDF export of REPORT-01~04

---

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Competitiveness Scoring

- **STU-v2-01**: System calculates competitiveness score — 学生画像 vs 岗位市场平均值 比值

### Advanced Matching

- **MATCH-v2-01**: System supports multi-target matching — 同时匹配多个岗位类型
- **MATCH-v2-02**: System supports career path simulation — "what if I choose X path vs Y"

### Advanced Reporting

- **REPORT-v2-01**: System generates AI-polished report — LLM reviews and improves own output
- **REPORT-v2-02**: System tracks progress over time — 多次简历上传历史对比

---

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| User login/registration | Competition project, focus on core matching |
| Mobile native app | Web-first, mobile later |
| Real-time resume scanning | Adds latency and external dependencies |
| Salary prediction | No historical salary data for students |
| Peer comparison/social | Privacy concerns, not core value |
| Learning resource database | No external course/certificate data; LLM generates generic recommendations |
| Manual profile editing | Breaks automated pipeline; use LLM-based suggestion refinement |

---

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| STU-01 | Phase 6 | Complete |
| STU-02 | Phase 6 | Complete |
| STU-03 | Phase 6 | Complete |
| STU-04 | Phase 6 | Complete |
| STU-05 | Phase 6 | Complete |
| STU-06 | Phase 7 | Pending |
| STU-07 | Phase 7 | Pending |
| MATCH-01 | Phase 8 | Pending |
| MATCH-02 | Phase 8 | Pending |
| MATCH-03 | Phase 8 | Pending |
| REPORT-01 | Phase 9 | Pending |
| REPORT-02 | Phase 9 | Pending |
| REPORT-03 | Phase 9 | Pending |
| REPORT-04 | Phase 9 | Pending |
| REPORT-05 | Phase 9 | Pending |
| UI-01 | Phase 10 | Pending |
| UI-02 | Phase 10 | Pending |
| UI-03 | Phase 10 | Pending |
| UI-04 | Phase 10 | Pending |
| UI-05 | Phase 10 | Pending |

**Coverage:**
- v1.1 requirements: 21 total
- Mapped to phases: 21/21
- Unmapped: 0

---

## Phase Mapping Summary

| Phase | Requirements | Count |
|-------|-------------|-------|
| Phase 6 | STU-01, STU-02, STU-03, STU-04, STU-05 | 5 |
| Phase 7 | STU-06, STU-07 | 2 |
| Phase 8 | MATCH-01, MATCH-02, MATCH-03 | 3 |
| Phase 9 | REPORT-01, REPORT-02, REPORT-03, REPORT-04, REPORT-05 | 5 |
| Phase 10 | UI-01, UI-02, UI-03, UI-04, UI-05 | 5 |

---

*Requirements defined: 2026-03-30*
*Last updated: 2026-03-30 after v1.1 roadmap created*
