# Phase 2: 岗位向量数据库构建 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-29
**Phase:** 02-job-vector-db
**Areas discussed:** Embedding Model, Text Preparation Strategy, Metadata Filtering, Retrieval Strategy

## Embedding Model

| Option | Description | Selected |
|--------|-------------|----------|
| BGE-large-zh (recommended) | Best Chinese semantic performance, open-source FlagEmbedding, ~1024 dimensions | ✓ |
| text-embedding-3-small | OpenAI model, general purpose, 1536 dims | |
| M3E | Faster inference, good Chinese, lighter model | |

**User's choice:** BGE-large-zh (recommended)
**Notes:** Best Chinese performance, aligns with project stack

---

## Text Preparation Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Concatenated full record (recommended) | Combine title + company + industry + detail into one text | ✓ |
| Separate field embeddings | Embed key fields separately, multiple vectors per job | |
| Structured prompt template | Format as '岗位: X, 公司: Y, 要求: Z' | |

**User's choice:** Concatenated full record (recommended)
**Notes:** Simple and effective with BGE

---

## Metadata Filtering

| Option | Description | Selected |
|--------|-------------|----------|
| ChromaDB metadata filter (recommended) | Store city/salary/industry as ChromaDB metadata, filter at query time | ✓ |
| Pre-filter then vector search | Query JSON first, then vector search within subset | |
| Pure semantic only | No filtering, just vector similarity | |

**User's choice:** ChromaDB metadata filter (recommended)
**Notes:** Simple and native to ChromaDB

---

## Retrieval Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Pure vector ANN (recommended) | ChromaDB default HNSW, fast approximate nearest neighbor | ✓ |
| Exact brute force | Brute force exact search, higher accuracy but slower | |
| Hybrid search | Combine keyword BM25 + vector similarity | |

**User's choice:** Pure vector ANN (recommended)
**Notes:** Good balance for 10K scale

---

## Claude's Discretion

No items — all decisions were explicitly made by user.

## Deferred Ideas

None
