# Phase 5: LLM服务封装 - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

统一封装DeepSeek API，提供LLM调用服务，供下游Phase 6-9（简历解析、学生画像、人岗匹配、报告生成）调用。核心是可靠的LLM调用封装，支持画像生成/匹配分析/报告生成三种任务类型。

**Scope:**
- 统一的LLM服务层（FastAPI HTTP endpoints）
- 支持画像生成/匹配分析/报告生成三种任务路由
- 错误处理和重试机制
- 响应时间满足TECH-01指标

**Out of scope:**
- 具体业务逻辑（画像结构、匹配算法、报告格式）由下游Phase定义
- 前端集成（Phase 10负责）
- 多模型路由/负载均衡（单一DeepSeek模型）

</domain>

<decisions>
## Implementation Decisions

### 服务模式
- **D-01:** FastAPI HTTP endpoints，路由分开
  - `/llm/profile/generate` — 画像生成（调用deepseek-chat）
  - `/llm/match/analyze` — 匹配分析
  - `/llm/report/generate` — 报告生成
  - 理由：更好的可观测性，未来可从前端直接调用

### 错误处理策略
- **D-02:** Retry 3次 + 指数退避
  - 重试间隔：1s → 2s → 4s
  - 重试触发：API错误（500/503）、超时
  - 不重试：400错误（请求格式问题）、401认证失败
  - 理由：标准可靠性模式，平衡延迟与成功率

### 超时配置
- **D-03:** 任务级别超时
  - 画像生成（/llm/profile/generate）：15秒超时
  - 报告生成（/llm/report/generate）：45秒超时
  - 理由：TECH-01要求P95≤10s/≤30s，留出buffer处理网络抖动

### JSON输出处理
- **D-04:** JSON解析失败时Retry 1-2次
  - 使用 `response_format={"type": "json_object"}` 强制结构化输出
  - 首次解析失败后重试调用
  - 2次失败后返回错误信息
  - 理由：大多数失败是LLM偶尔输出格式偏差，重试可解决

### API调用配置
- **D-05:** DeepSeek API标准配置
  - Model: `deepseek-chat`
  - Temperature: 0.1-0.2（结构化输出）
  - base_url: `https://api.deepseek.com`
  - 理由：与Phase 3/4现有调用模式一致

### 请求模型
- **D-06:** 统一请求格式
  ```python
  class LLMGenerateRequest(BaseModel):
      task_type: Literal["profile", "match", "report"]
      prompt: str
      temperature: float = 0.1
      max_tokens: Optional[int] = None
  ```
  - 理由：统一接口，便于扩展和监控

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Context
- `.planning/ROADMAP.md` §Phase 5 — 阶段目标、成功标准（TECH-01: API调用成功率≥95%，响应时间P95≤10s/≤30s）
- `.planning/REQUIREMENTS.md` §TECH-01 — LLM调用封装需求

### Prior Phases Integration
- Phase 3（岗位画像）使用 `call_llm()` 直接调用DeepSeek — 参考 `scripts/build_job_profiles.py` 第102-110行
- Phase 4（图谱）使用 `call_llm()` + DashScope Qwen — 参考 `scripts/build_job_graph.py` 第83-137行
- Phase 6（简历解析）将依赖此LLM服务
- Phase 7（学生画像）将依赖此LLM服务
- Phase 8（人岗匹配）将依赖此LLM服务
- Phase 9（报告生成）将依赖此LLM服务

### Project Constraints
- `.planning/REQUIREMENTS.md` — LLM必须使用大语言模型作为核心（glm-4等）
- `.planning/PROJECT.md` — DeepSeek为已选型（性价比高，API便宜，中文能力好）

</canonical_refs>

<codebase_context>
## Existing Code Insights

### Reusable Assets
- `scripts/build_job_profiles.py` 第102-110行 — `call_llm()` 函数，实现 DeepSeek chat completion 调用
- `scripts/build_job_graph.py` 第83-137行 — LLM批量调用模式，带token估算和错误处理

### Established Patterns
- `openai.OpenAI` 客户端，OpenAI兼容API
- `response_format={"type": "json_object"}` 强制JSON输出
- Temperature 0.1-0.2 用于结构化任务
- JSON解析：`json.loads(response.choices[0].message.content)`

### Integration Points
- 输入：无（greenfield service）
- 输出：FastAPI endpoints，被 Phase 6-9 调用
- 环境变量：`DEEPSEEK_API_KEY`

</codebase_context>

<specifics>
## Specific Ideas

无特殊要求 — 采用标准方法，灵活处理。

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---
*Phase: 05-llm-service*
*Context gathered: 2026-03-30*
