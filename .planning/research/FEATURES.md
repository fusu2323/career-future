# Feature Landscape

**Domain:** AI Career Planning/Counseling (AI职业规划智能体)
**Researched:** 2026-03-29
**Research Mode:** Ecosystem
**Confidence:** MEDIUM (based on domain knowledge; web search tools unavailable for verification)

---

## Executive Summary

AI career planning products in the Chinese market have converged on a common feature set driven by recruitment platform competition and user expectations. For a competition project targeting college students, features cluster around resume analysis, capability profiling, job matching, and actionable report generation. The market distinguishes between **table stakes** (must-have features that users expect as baseline) and **differentiators** (features that create competitive advantage).

This analysis is tailored to:
- **Target users:** Chinese college students (primarily final-year students seeking employment)
- **Use context:** Competition demo, offline data, single-session usage
- **Core value prop:** "精准匹配" - helping students understand capability gaps and how to close them

---

## 1. Table Stakes Features

These are features users expect as minimum viable functionality. Missing any of these will cause users to perceive the product as incomplete or unprofessional.

### 1.1 Resume Parsing and Capability Extraction

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Resume upload (PDF/DOCX) | Primary input method for students | Medium | Must handle various templates and formats |
| Basic information extraction | Name, education, contact | Low | Well-structured output expected |
| Skills identification | Core to value proposition | High | Requires domain-specific NLP for Chinese resumes |
| Work/experience parsing | Establishes baseline capability | Medium | Internships, projects, extracurriculars |
| Education background extraction | Critical for Chinese job matching | Low | University, major, GPA if available |

**Market expectation:** Users expect "smart parsing" that surfaces information human reviewers would notice. Rough extraction is table stakes; accurate extraction with context is a differentiator.

**Dependencies:** Resume parsing is foundational - almost all other features depend on it.

---

### 1.2 Student Capability Profile Generation

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Multi-dimensional profiling | Students need holistic self-understanding | High | 7 dimensions per PROJECT.md requirements |
| Profile visualization | Makes abstract capabilities concrete | Medium | Radar charts, capability scores |
| Completeness scoring | Motivates profile improvement | Low | Percentage-based, easily understood |
| Competitiveness scoring | Relative measure against peers/jobs | Medium | Requires benchmark data |

**Market expectation:** Products like 智联招聘 and 猎聘 offer profile completeness indicators. Students expect to see their capability profile visualized and scored.

**Dependencies:** Depends on resume parsing; feeds into matching algorithms.

---

### 1.3 Job Profile and Association Graph

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Job description parsing | Foundation of job requirements | High | Extract skills, requirements, preferences |
| Job categorization | EnablesBrowse/search | Medium | Hierarchical categories |
| Promotion path visualization | Answers "what's next" question | High | Vertical career ladder |
| Transfer path visualization | Answers "what else" question | High | Lateral moves to related roles |

**Market expectation:** Chinese students frequently ask "What jobs can I progress to?" and "What other roles match my skills?". Graph-based visualization is increasingly expected.

**Dependencies:** Job profiles require job data; graphs require relationship modeling.

---

### 1.4 Basic Person-Job Matching

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Skill matching | Core matching mechanic | High | Match student skills to job requirements |
| Overall match score | Quick suitability indicator | Low | Percentage or star-based |
| Match explanation | Why match works/doesn't | Medium | Natural language reasoning |

**Market expectation:** All major platforms (智联, 猎聘, BOSS) show match scores. Users expect to understand why they match or don't match.

**Dependencies:** Depends on student profile and job profiles.

---

### 1.5 Career Development Report Generation

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Goal setting | Foundational career planning | Medium | Short/medium/long-term objectives |
| Action plan generation | Makes recommendations concrete | High | Specific learning activities, timelines |
| Report export | Submission for applications | Low | PDF format expected |

**Market expectation:** Users expect a downloadable document they can reference. Competition requirements explicitly mandate export functionality.

**Dependencies:** Depends on matching results and profile data.

---

## 2. Differentiators

These features set products apart from basic implementations. A product with only table stakes features feels like a commodity.

### 2.1 Gap Analysis and Learning Path Recommendations

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Skill gap identification | Precise "what am I missing" | High | Compare profile to target jobs |
| Prioritized gap list | Not all gaps equal importance | Medium | Weighted by job relevance |
| Learning resource recommendations | "How do I close this gap" | High | Courses, certifications, projects |
| Time-bound improvement plans | Realistic goal-setting | High | 3-month, 6-month milestones |

**Why differentiating:** Most basic products stop at "you don't match". Differentiating products tell users *how* to improve and *by when*.

**Dependencies:** Requires robust job profile data and likely external learning resource data.

---

### 2.2 Multi-Dimensional Competency Deep Dive

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| 4-dimension analysis (per requirements) | Comprehensive evaluation | High | 基础要求/职业技能/职业素养/发展潜力 |
| Competency weight customization | Personalized importance | Medium | Different jobs weight dimensions differently |
| Longitudinal progress tracking | "Am I improving" over time | High | Requires user accounts, multiple sessions |

**Why differentiating:** Shallow matching (skill-only) is table stakes. Deep competency modeling that captures *how* someone does work (not just *what* they know) is differentiating.

---

### 2.3 Career Path Simulation and Scenario Planning

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| "What if I pursue X instead" | Alternative career exploration | Very High | Requires comprehensive job graph |
| Salary trajectory projection | Realistic expectation setting | High | Based on market data, experience accumulation |
| Risk assessment for career moves | Informed decision-making | High | Market demand, skill portability |

**Why differentiating:** Most products answer "can I get this job". Differentiators answer "should I pursue this path" and "what's the upside".

---

### 2.4 AI-Powered Report Polish and Professional Writing

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Natural language refinement | More professional report tone | Medium | LLM-powered editing |
| Completeness checking | Ensure all sections populated | Low | Structural validation |
| One-click optimization | Effortless improvement | Medium | One-button enhancement |

**Why differentiating:** Report generation is table stakes. Report *optimization* that produces professional-quality output is differentiating.

**Competition relevance:** REPORT-04 explicitly requires "智能润色、内容完整性检查、编辑优化", making this a key differentiator to implement well.

---

### 2.5 Interactive Visualization and Exploration

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Interactive job graph exploration | Visual career navigation | High | Zoom, filter, click-through |
| Capability radar comparison | Visual student-job comparison | Low | Overlay student vs job requirements |
| Animated path highlighting | Clear progression visualization | Medium | Show career journey dynamically |

**Why differentiating:** Static reports are table stakes. Interactive exploration that lets students "see" their career possibilities is differentiating.

---

## 3. Anti-Features

Features to deliberately NOT build, either because they are out of scope, would dilute value, or are inappropriate for the competition context.

### 3.1 Features Explicitly Out of Scope

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| User authentication/login | PROJECT.md explicitly excludes | Focus on core single-session flow |
| Real-time job platform integration | Offline data requirement | Use provided 10000 job records |
| Mobile native app | Web-first decision | Ensure responsive Web experience |
| Multi-language support | Chinese single-language requirement | Focus UX on Chinese users |

### 3.2 Features That Would Dilute Value

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Generic career advice | Loses "精准" value proposition | Keep advice job-specific |
| Overly complex matching models | Competitions don't reward complexity | Optimize for explainability |
| Too many input fields | Kills user engagement | Max 5-7 resume uploads for demo |

### 3.3 Features Inappropriate for Competition Context

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Freemium/paywall simulation | Distracts from core evaluation | Keep all features accessible |
| Social features (peer comparison) | Privacy concerns, complexity | Focus on student-to-job matching |
| Job application integration | Not evaluated | Report generation is the deliverable |

---

## 4. Feature Dependencies

Understanding dependencies is critical for phase ordering.

```
Resume Upload/Parsing
        │
        ├──► Student Profile Generation
        │           │
        │           ├──► Completeness/Competitiveness Scoring
        │           │
        │           └──► Gap Analysis
        │                    │
        │                    └──► Learning Path Recommendations
        │
        ├──► Job Profile Generation
        │           │
        │           └──► Job Graph (Promotion + Transfer Paths)
        │                    │
        │                    └──► Career Path Simulation
        │
        └──► Person-Job Matching ──► Match Explanation
                    │
                    └──► Career Development Report
                             │
                             └──► Report Polish/Export
```

### Critical Path for MVP

1. **Resume Parsing** (foundation)
2. **Student Profile Generation** (core output)
3. **Job Profile + Graph** (enables matching)
4. **Basic Matching** (core value)
5. **Report Generation** (final deliverable)

---

## 5. MVP Recommendation

For a competition project with limited development time, prioritize in this order:

### Phase 1: Table Stakes (Must Have)
1. **Resume parsing** - Single upload, extract core info
2. **Student profile visualization** - Radar chart with 7 dimensions
3. **Basic job matching** - Score + simple explanation
4. **Simple report generation** - Fill-in-the-blank template with export

### Phase 2: Differentiators (Competitive Edge)
1. **Gap analysis with learning paths** - The "what am I missing, how do I fix it" loop
2. **4-dimension competency matching** - Deep analysis per requirements
3. **Interactive job graph** - Visual promotion/transfer paths
4. **AI-powered report polish** - Per REPORT-04 requirement

### Features to Defer

| Feature | Reason to Defer |
|---------|-----------------|
| Multi-session progress tracking | Requires user auth, out of scope |
| Salary trajectory projection | Requires market data not in dataset |
| Career simulation scenarios | High complexity, lower priority |
| Learning resource database | External data required |

---

## 6. Market Feature Comparison

| Feature | 智联招聘AI | 猎聘简历优化 | BOSS直聘 | 本项目 |
|---------|-----------|-------------|----------|--------|
| Resume parsing | Yes | Yes | Yes | Yes |
| Capability profiling | Basic | Advanced | Basic | Advanced (7 dim) |
| Skill gap analysis | No | Yes | No | Yes |
| Job graph visualization | No | No | No | Yes (key diff) |
| 4-dimension matching | No | No | No | Yes (per reqs) |
| Career path planning | Basic | Yes | Basic | Yes |
| Report generation | No | Yes | No | Yes |
| Report polish/export | No | Yes | No | Yes |
| Learning recommendations | Limited | Yes | Limited | Yes |

**Key insight:** The combination of job graph visualization + 4-dimension matching + gap analysis + report polish is not fully implemented by major platforms. This is the competitive whitespace.

---

## 7. Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Table stakes identification | MEDIUM | Based on product knowledge; would benefit from current competitor analysis |
| Differentiator assessment | MEDIUM | Same - market position can shift quickly |
| Anti-features list | HIGH | Based on explicit project constraints |
| Dependency mapping | HIGH | Technical dependencies are clear |
| Feature complexity ratings | MEDIUM | Estimates based on typical implementation |

---

## Sources

*Unable to verify via web search tools. Analysis based on domain knowledge of:*
- Chinese recruitment platform ecosystem (智联招聘, 猎聘, BOSS直聘, 前程无忧, 牛客)
- Global AI career tools (LinkedIn, Zety, Kickresume, Teal, FlowCV, MeetFrank)
- Career development theory and competency modeling
- PROJECT.md requirements specification

*Recommended verification:* Conduct user interviews with 5-10 college students to validate feature priorities before implementation.
