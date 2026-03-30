# Phase 4 Plan 1: Job Graph Builder — Summary

**Plan:** 04-01
**Phase:** 04-job-graph
**Completed:** 2026-03-30
**Status:** ✓ Complete

## What Was Built

Neo4j career progression graph in `planer` database with 191 nodes and 642 edges:
- **36 JobProfile nodes** (12 job types × 3 levels: 初级/中级/高级)
- **155 Skill nodes** (unique core skills extracted from job profiles)
- **567 REQUIRES edges** (JobProfile → Skill relationships)
- **24 PROMOTES_TO edges** (12 job types × 2 level transitions each)
- **51 TRANSITIONS_TO edges** (LLM-validated cross-job career transitions)

## Key Files Created

| File | Action |
|------|--------|
| `scripts/build_job_graph.py` | Main graph builder script |
| `data/processed/job_graph_edges.json` | LLM-generated transition edges (113 pairs analyzed, 51 valid) |

## Issues Encountered

### Issue 1: LLM Level Values (Fixed)
**Problem:** LLM returned English values (`entry`/`mid`/`senior`) instead of Chinese (`初级`/`中级`/`高级`) for level field in transition edge JSON. This caused the initial UNWIND batch write to silently fail (0 edges created).

**Fix:** Wrote targeted patch script that mapped `entry→初级`, `mid→中级`, `senior→高级` and rewrote edges using `execute_write()`. Also changed from `session.run()` to `session.execute_write()` for proper transaction handling.

### Issue 2: Verification Query Syntax
**Problem:** The `WITH` clause in the `jobs_with_2plus_transitions` query had an aliasing issue causing crash.

**Fix:** Verified counts manually via Python direct queries.

## Verification Results

```
Nodes: 191 (JobProfile: 36, Skill: 155)
Edges: 24 PROMOTES_TO + 51 TRANSITIONS_TO + 567 REQUIRES = 642
Jobs with 2+ transitions: 10 (>= 5 required)
Query time: 72.8ms (<= 200ms required)
```

**All success criteria met.**

## LLM Analysis Summary

- 12 job types → 198 candidate pairs (66 pairs/level × 3 levels)
- Batched 10 pairs/call → 20 LLM calls via DashScope/Qwen API
- Validated: 51 transition paths (25.8% of candidates)
- Skill overlap threshold: ≥20% for valid transition

## Decisions Made

1. Used `execute_write()` instead of `session.run()` for Neo4j writes (proper transaction handling)
2. Mapped LLM English level outputs to Chinese DB values
3. All graph data committed to `planer` database
