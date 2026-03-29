# Domain Pitfalls: AI职业规划智能体

**Domain:** AI Career Planning / Human-Resource Matching
**Researched:** 2026-03-29
**Confidence:** LOW (WebSearch unavailable; based on training knowledge)

---

## Critical Pitfalls

Mistakes that cause rewrites, failed accuracy metrics, or harmful career advice.

---

### Pitfall 1: LLM Hallucination in Professional Career Advice

**What goes wrong:** The LLM generates confident but factually incorrect career advice, such as claiming a skill is in demand when it is not, inventing non-existent job titles, or suggesting obsolete certification paths.

**Why it happens:**
- LLMs generate plausible-sounding text without grounding in current labor market data
- Career advice requires real-time labor market information that static LLM training cannot provide
- System prompt instructions are insufficient to prevent hallucination on specific Chinese job markets

**Consequences:**
- Students make poor career decisions based on false information
- 80% matching accuracy requirement may be missed if hallucinations propagate to match results
- Trust erosion if users discover factual errors

**Prevention:**
1. **Ground all career advice in the 10,000-job dataset** - Never let LLM invent information outside the dataset
2. **Use retrieval-augmented generation (RAG)** - Always retrieve relevant job/career data before generating advice
3. **Add factual assertions to prompts** - "Based on the available job data showing X, recommend Y"
4. **Implement confidence scoring** - Flag advice that cannot be grounded in retrieved data
5. **Add disclaimer layer** - Distinguish between data-grounded recommendations vs. LLM-generated suggestions

**Detection (Warning Signs):**
- LLM outputs job titles not in the database
- Recommendations reference skills/certifications not present in job requirements
- Career paths suggest promotions that do not exist in the knowledge graph

**Phase to Address:** Phase 2 (Matching System) - The RAG pipeline must be built before any LLM advice generation.

---

### Pitfall 2: Resume Parsing Failure on Varied Chinese Resume Formats

**What goes wrong:** The resume parser fails to correctly extract information from resumes with non-standard layouts, unusual formatting, or domain-specific abbreviations common in Chinese resumes.

**Why it happens:**
- Chinese resumes vary widely in structure (timeline format, table format, free-form)
- Academic/skill sections use inconsistent terminology
- Scanned PDFs introduce OCR errors
- The parser was likely trained on limited resume templates

**Consequences:**
- Student profile accuracy below 90% threshold
- Downstream matching uses incomplete/wrong data
- User trust issues when they see incorrect parsed data

**Prevention:**
1. **Implement multiple parsing strategies** - Table extraction, section header detection, line-item recognition
2. **Validate parsed data against expected schemas** - Reject profiles with >30% missing required fields
3. **Use LLM for structure inference** - Prompt GLM-4 to identify sections and normalize unstructured text
4. **Build a "low confidence" flag system** - If parsing confidence < threshold, prompt user to verify/correct
5. **Test with diverse resume formats** - Create test set of at least 20 different Chinese resume templates

**Detection (Warning Signs):**
- Parser outputs empty fields for clearly-present information
- Skills extracted do not match resume text
- Timeline gaps or ordering errors in education/experience

**Phase to Address:** Phase 1 (Profile Generation) - Resume parsing must be robust before matching.

---

### Pitfall 3: Matching Algorithm Produces Biased or Unfair Results

**What goes wrong:** The matching algorithm systematically disadvantages certain student profiles due to training data bias or algorithmic design flaws.

**Why it happens:**
- Job data reflects existing hiring biases (e.g., over-weighting prestigious companies, specific学历 requirements)
- Four-dimension matching weights may inadvertently penalize non-traditional backgrounds
- Cold-start students with sparse resumes get worse matches due to data gaps

**Consequences:**
- Underserved students receive poor recommendations
- Violates fairness expectations for a career guidance product
- May miss 80% accuracy target on edge cases

**Prevention:**
1. **Audit matching results for demographic parity** - Test whether similar-profile students get similar results
2. **Use explainable matching** - Each match dimension should be traceable to specific resume/job data
3. **Weight fairness adjustment** - Add re-ranking step that boosts under-represented dimensions
4. **Handle sparse data explicitly** - Use collaborative filtering or content-similarity for cold-start students
5. **Document bias limitations** - Be transparent that recommendations reflect job data biases

**Detection (Warning Signs):**
- Students with strong practical experience but low学历 get poor matches
- Students with non-standard resumes consistently get low match scores
- Same resume gets different results on re-run (non-deterministic matching)

**Phase to Address:** Phase 2 (Matching System) - Algorithm audit and fairness testing should be part of matching development.

---

### Pitfall 4: Cold Start Problem - New Users with No Resume Data

**What goes wrong:** New students with incomplete or missing resume data receive poor/vague recommendations, making the system useless for its primary use case.

**Why it happens:**
- Matching algorithm requires rich student profile data
- Students early in their career have limited experiences to input
- System treats "no data" the same as "low ability"

**Consequences:**
- Poor user experience for the target audience (college students early in career)
- Low engagement rates
- Cannot validate 80% accuracy on cold-start cases

**Prevention:**
1. **Implement progressive profiling** - Start with basic questions, refine over time
2. **Use job data to bootstrap profiles** - Suggest typical skills/attributes for students at each year level
3. **Build a "capability gap" mode** - Instead of matching, suggest what skills to develop
4. **Set minimum profile completeness threshold** - Do not run matching until profile is >50% complete
5. **Design "exploration mode"** - Allow students to browse job categories without full profile

**Detection (Warning Signs):**
- New users immediately get "no matching jobs" or generic results
- Profile completeness scores remain at 0% after resume upload
- System cannot generate reports for incomplete profiles

**Phase to Address:** Phase 1 (Profile Generation) - Must design cold-start handling alongside profile generation.

---

### Pitfall 5: Generated Reports Are Vague and Non-Actionable

**What goes wrong:** Career reports contain generic advice like "improve your communication skills" without specific, measurable actions.

**Why it happens:**
- LLM defaults to high-level career platitudes when not given specific grounding data
- Reports are not tied to the specific gap analysis from matching results
- No mechanism to verify actionability before report delivery

**Consequences:**
- Students cannot use reports to make decisions
- Fails the "可操作的行动计划" (actionable action plan) requirement
- No way to measure report quality or improvement over time

**Prevention:**
1. **Ground every recommendation in matching gaps** - Each section must reference specific missing skills from gap analysis
2. **Use structured report templates** - Define sections that MUST contain: current state, target state, specific actions, success metrics
3. **Implement actionability scoring** - Rate recommendations on specificity (1-5) before finalizing
4. **Include timeline and resources** - Every action should have estimated time and learning resources
5. **Add verification prompt** - Ask LLM "Could a student act on this recommendation without additional research?"

**Detection (Warning Signs):**
- Report contains only generic advice without specific details
- Recommendations could apply to any student in any field
- No specific courses, certifications, or actions listed

**Phase to Address:** Phase 3 (Report Generation) - Report structure and grounding must be architected, not left to LLM default behavior.

---

### Pitfall 6: Targeting 80%/90% Accuracy Without Defining It Precisely

**What goes wrong:** The project aims for "80% matching accuracy" and "90% profile accuracy" without specifying what these metrics actually measure, leading to validation disputes.

**Why it happens:**
- Accuracy definitions are ambiguous (precision? recall? F1? hit rate?)
- No ground truth dataset to validate against
- Different stakeholders interpret "accurate" differently

**Consequences:**
- Cannot objectively measure if requirements are met
- Potential for false confidence (system seems accurate on happy-path tests)
- Competition judging may use different accuracy definitions

**Prevention:**
1. **Define precision metrics explicitly** - e.g., "80% of top-5 recommended jobs are genuinely suitable for the student"
2. **Create validation dataset** - Manually label 100 student-job pairs as correctly/incorrectly matched
3. **Define profile accuracy as field-level match** - e.g., 90% of extracted skills must match manually-annotated skills
4. **Separate evaluation from generation** - Build evaluation module that scores existing outputs
5. **Report confidence intervals** - Don't claim a single accuracy number without variance

**Detection (Warning Signs):**
- No measurable way to distinguish a 79% vs 81% accurate system
- Validation results vary significantly across different student profiles
- "Accuracy" only measured on easy cases (students with clear matches)

**Phase to Address:** Phase 0 (Planning) - Metric definitions must be locked before development begins.

---

### Pitfall 7: Chinese Language Nuances Breaking LLM Understanding

**What goes wrong:** The LLM misinterprets Chinese professional terminology, fails to understand Chinese resume conventions, or produces unnatural Chinese output.

**Why it happens:**
- Chinese career terminology has specific meanings that vary by region/industry
- Abbreviations in Chinese resumes (e.g., "985", "211" for university tiers) may confuse the model
- Professional terms like "抗压能力" (pressure resistance) need careful prompt framing
- GLM-4 may default to simplified Chinese conventions inappropriate for traditional career contexts

**Consequences:**
- Incorrect extraction of 能力维度 (capability dimensions)
- Career advice sounds robotic or inappropriate
- Confusion around certifications and credentials specific to Chinese market

**Prevention:**
1. **Create Chinese domain glossary** - Define key terms with explicit examples in prompts
2. **Use Chinese-optimized prompts** - Include few-shot examples of expected Chinese resume structures
3. **Handle tier abbreviations** - Explicitly expand "985", "211", "C9" in parsing prompts
4. **Include regional labor market context** - Chinese job markets vary by city tier
5. **Test with authentic Chinese resumes** - Ensure training/test data reflects actual Chinese resume styles

**Detection (Warning Signs):**
- LLM produces English explanations when asked about Chinese career concepts
- Parsed skills do not match Chinese terminology in source resume
- Report output uses mainland simplified but target audience expects traditional

**Phase to Address:** Phase 1 (Profile Generation) - Chinese language handling must be built into parsing prompts.

---

### Pitfall 8: Over-Engineering the Knowledge Graph When Simple Matching Suffices

**What goes wrong:** The team spends excessive time building complex岗位晋升图谱 and 换岗路径图谱 instead of delivering working matching and reporting.

**Why it happens:**
- The 5 job profile and graph requirements (JOB-PROFILE-01, -02, -03) are ambitious
- Building Neo4j knowledge graphs is technically interesting but time-consuming
- Competition judged on matching accuracy first, graph complexity second

**Consequences:**
- Matching core (which determines the 80% accuracy) is under-developed
- Report generation (scored explicitly in REPORT-*) is rushed
- Graph features work but matching does not

**Prevention:**
1. **Prioritize matching accuracy over graph depth** - If matching fails, the graph is irrelevant
2. **Build minimum viable graph first** - Simple job-to-skill mappings before complex pathfinding
3. **Define graph scope explicitly** - Limit to the "5 job transitions with 2 paths each" minimum
4. **Use graph only for recommendation explanation** - Graph complexity should serve matching, not be an end itself
5. **Time-box graph development** - Set hard deadlines for graph features separate from matching features

**Detection (Warning Signs):**
- Graph construction takes more than 30% of total development time
- Matching accuracy still below 80% while graph features are complete
- Team excitement about graph visibility exceeds matching performance

**Phase to Address:** Phase 2 (Matching System) - Graph features should not delay matching development.

---

## Moderate Pitfalls

Issues that cause delays or degraded quality but do not require full rewrites.

---

### Pitfall 9: Report Exports Fail or Produce Inconsistent Formatting

**What goes wrong:** The "一键导出" (one-click export) feature produces broken PDFs or inconsistent formatting across different browsers/devices.

**Prevention:** Use established PDF generation libraries (weasyprint, pdfkit) with templates; test exports on multiple browsers.

**Phase to Address:** Phase 3 (Report Generation) - Late phase feature, but needs early library selection.

---

### Pitfall 10: Matching Weights Are Tuned to Test Data, Not General Students

**What goes wrong:** The 四维匹配 algorithm weights (基础要求, 职业技能, 职业素养, 发展潜力) are optimized for a small test set and perform poorly on diverse students.

**Prevention:** Use cross-validation; hold out 20% of student profiles for final testing only.

**Phase to Address:** Phase 2 (Matching System) - Weight tuning should use separate validation set.

---

### Pitfall 11: Student Profile Completeness Scoring Is Gamed

**What goes wrong:** Students discover that adding more skills improves their profile score, leading to inflated profiles that distort matching.

**Prevention:** Weight skill relevance over skill count; penalize skill inflation in scoring.

**Phase to Address:** Phase 1 (Profile Generation) - Profile scoring should reward quality over quantity.

---

## Minor Pitfalls

---

### Pitfall 12: LLM Rate Limits Cause Timeouts During Peak Usage

**What goes wrong:** GLM-4 API rate limits cause matching/report generation to fail during demos or testing.

**Prevention:** Implement caching; batch requests; have fallback responses for rate limit errors.

**Phase to Address:** Phase 2 (Matching System) - API resilience should be built into integration layer.

---

### Pitfall 13: Chinese PDF Resume OCR Quality Is Poor

**What goes wrong:** Uploaded PDF resumes that are scanned images (not digital text) produce garbled text.

**Prevention:** If OCR confidence is low, prompt user to upload digital version; flag low-confidence OCR for review.

**Phase to Address:** Phase 1 (Profile Generation) - Handle OCR failures explicitly.

---

## Phase-Specific Warnings

| Phase | Primary Pitfall Risk | Mitigation |
|-------|---------------------|------------|
| Phase 1: Profile Generation | Resume parsing failures (Pitfall 2), Chinese language issues (Pitfall 7), Cold start (Pitfall 4) | Build robust parsing with validation; design progressive profiling |
| Phase 2: Matching System | Hallucination (Pitfall 1), Bias (Pitfall 3), Weight over-tuning (Pitfall 10), Over-engineering graphs (Pitfall 8) | RAG pipeline first; audit fairness; prioritize matching accuracy over graph complexity |
| Phase 3: Report Generation | Vague reports (Pitfall 5), Export failures (Pitfall 9), Accuracy definition (Pitfall 6) | Structured templates; actionability scoring; lock metrics before generation |
| All Phases | Ambiguous accuracy metrics (Pitfall 6) | Define metrics in Phase 0 before any development |

---

## Key Research Gaps

The following areas need verification through actual user testing or domain experts:

1. **Actual resume format diversity** - What Chinese resume formats are most common? Which cause parsing failures?
2. **Student expectations for report actionability** - What granularity of advice do Chinese college students expect?
3. **Real cold-start patterns** - Do students actually engage with incomplete profiles, or abandon the system?
4. **GLM-4 hallucination rates on career advice** - How often does GLM-4 generate factually incorrect career information?

**Confidence note:** This analysis is based on general knowledge of AI career systems and LLM limitations. Web search verification was unavailable. Claims should be validated with user research before finalizing roadmap priorities.

---

## Sources

No external sources could be verified due to WebSearch unavailability. This document relies on training knowledge about:
- LLM hallucination patterns and mitigation (RAG, grounding)
- Resume parsing challenges for non-English languages
- Bias in algorithmic matching systems
- Cold start problem in recommendation systems
- Report generation best practices for AI-assisted career guidance

For verification, consider:
- Academic papers on AI career counseling systems (IEEE, ACM)
- Open-source resume parsing projects (e.g., ResumeParser, PyResparser)
- GLM-4 documentation and known limitations
