# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-30
**Phases:** 5 | **Plans:** 9 | **Sessions:** ~15

### What Was Built
- 9178条清洗后岗位数据，标准化薪资/地址/公司规模字段
- ChromaDB向量索引（9178条，BGE-m3嵌入，SiliconFlow API），Top10召回率100%
- 12个标准岗位画像，7维度完整（专业技能/证书/创新/学习/抗压/沟通/实习）
- Neo4j图谱（岗位晋升路径+换岗血缘关系，PROMOTES_TO+TRANSITIONS_TO）
- LLM服务封装（DeepSeek客户端、重试3x、超时控制、JSON解析重试、FastAPI路由、22个测试）
- FastAPI HTTP接口（/llm/profile/generate、/llm/match/analyze、/llm/report/generate、/health、/health/ready）

### What Worked
- GSD工作流执行规范——计划→执行→验证循环清晰，每阶段有SUMMARY和VERIFICATION追溯
- Phase 5测试先行策略——22个测试捕获了tenacity 400/401错误重试bug
- SiliconFlow API替代本地嵌入——5分钟完成vs 4-12小时，效率大幅提升
- YOLO模式快速推进——Phase 5三个计划3波次并行执行，约3分钟/波次

### What Was Inefficient
- Phase 2/3/4缺少正式UAT/VERIFICATION——SUMMARY有记录但未走完完整验证流程
- Phase 4图谱未完成（缺少04-UAT/04-VERIFICATION）——被跳过直接推进到Phase 5
- 阶段依赖串行——Phase 3→Phase 4有真实依赖但未能充分并行
- 9178条vs计划9857条差异未在里程碑层面清晰追踪——导致数据完整性认知偏差

### Patterns Established
- 延迟Settings加载——避免导入时ValidationError（auto-fix in Phase 5）
- 重试谓词_predicate——明确哪些HTTP错误重试、哪些不重试
- YAML frontmatter规范——plan/summary/verification统一格式，便于工具解析
- 多语言归档——所有文档已翻译为中文

### Key Lessons
1. 验证文档(UAT/VERIFICATION)不能跳过——Phase 4被标记为完成但实际缺少验证，回头补代价更高
2. 数据层基础决定下游质量——9178条清洗数据质量直接影响向量库和画像的可靠性
3. 测试先行在API封装层效果显著——22个测试在30秒内捕获关键bug
4. 并行波次执行效率高——Phase 5三波次约10分钟完成全部基础设施

### Cost Observations
- Model mix: sonnet 4 100% (phase executors + verifier)
- Sessions: ~15 (research + plan + execute per phase)
- Notable: Phase 5 verifier ran sonnet in 207s, executors ran sonnet in 360s/256s/1075s — parallel waves very efficient

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | ~15 | 5 | GSD workflow established, YOLO mode for speed |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 22 (pytest) | Phase 5 100% | 0 |

### Top Lessons (Verified Across Milestones)

1. 测试覆盖是唯一可靠的进度证明——Phase 5的22个测试比SUMMARY文档更能反映真实状态
2. auto-fix机制有价值——lazy loading、retry predicate等在执行中自动捕获的bug比人工更及时
