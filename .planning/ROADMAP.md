# Roadmap: 基于AI的大学生职业规划智能体

**核心价值：** 帮助大学生从"盲目规划"走向"精准匹配"

## Milestones

- ✅ **v1.0 MVP** — Phases 1-5 (shipped 2026-03-30)
- 📋 **v1.1** — Phases 6-10 (planned)

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|---------------|--------|-----------|
| 1 | v1.0 | 1/1 | Complete | 2026-03-29 |
| 2 | v1.0 | 1/1 | Complete | 2026-03-29 |
| 3 | v1.0 | 3/3 | Complete | 2026-03-30 |
| 4 | v1.0 | 1/1 | Complete | 2026-03-30 |
| 5 | v1.0 | 3/3 | Complete | 2026-03-30 |
| 6 | v1.1 | 0/1 | Not started | - |
| 7 | v1.1 | 0/1 | Not started | - |
| 8 | v1.1 | 0/1 | Not started | - |
| 9 | v1.1 | 0/1 | Not started | - |
| 10 | v1.1 | 0/1 | Not started | - |

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

_详细归档见：`.planning/milestones/v1.0-ROADMAP.md`_
_路线图制定：2026-03-29 | 更新：2026-03-30 v1.0里程碑完成_
