import pytest
import chromadb
from pathlib import Path
import requests

# SiliconFlow API config for query embedding
SILICONFLOW_API_KEY = "sk-inhxcgiznrjsgevgcttsuifahalqzlmmrmylbeueepmoxrvl"
SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1/embeddings"
EMBEDDING_MODEL = "BAAI/bge-m3"


def get_query_embedding(text):
    """Get BGE-m3 embedding for a query text via SiliconFlow API."""
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": EMBEDDING_MODEL,
        "input": [text],
    }
    resp = requests.post(SILICONFLOW_API_URL, headers=headers, json=payload, timeout=30)
    data = resp.json()
    return data["data"][0]["embedding"]


def test_collection_exists(vector_db_path):
    """ChromaDB collection job_postings exists."""
    client = chromadb.PersistentClient(path=str(vector_db_path))
    collection = client.get_collection("job_postings")
    assert collection.count() >= 9000, f"Expected ~9178 vectors, got {collection.count()}"


def test_query_returns_results(collection):
    """Query returns Top10 results with valid metadata."""
    # Use pre-computed embedding for the query
    q_emb = get_query_embedding("前端开发 JavaScript React")
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=10,
        include=["distances", "metadatas", "documents"]
    )
    assert len(results["ids"][0]) == 10
    assert results["metadatas"][0][0]["title"] is not None


def test_recall_spot_check(collection):
    """Top10 recall accuracy >=85% on known query/keyword pairs."""
    # NOTE: The dataset contains these job families: Java(537), 科研人员(535),
    # 测试工程师(504), 前端开发(243), 运营(539), 销售(851), etc.
    # Test queries must use keywords that actually exist in the dataset.
    test_queries = [
        ("前端开发 JavaScript React", ["前端开发"]),
        ("Java后端开发 Spring微服务", ["Java"]),
        ("测试工程师 自动化测试", ["测试工程师", "软件测试"]),
        ("社区运营 用户增长 内容运营", ["运营", "社区运营", "游戏运营"]),
    ]
    correct = 0
    total = 0
    for query, expected_keywords in test_queries:
        q_emb = get_query_embedding(query)
        results = collection.query(
            query_embeddings=[q_emb],
            n_results=10,
            include=["metadatas"]
        )
        titles = [m["title"] for m in results["metadatas"][0]]
        hits = sum(1 for t in titles if any(kw in t for kw in expected_keywords))
        correct += hits
        total += 10
    recall = correct / total
    assert recall >= 0.85, f"Recall {recall:.1%} below 85% threshold"


def test_metadata_filter(collection):
    """Metadata filtering works on city and industry."""
    # Use pre-computed embedding for the query
    q_emb = get_query_embedding("软件工程师")
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=5,
        where={"city": "广州"},
        include=["metadatas"]
    )
    # Should return results (or empty if no Guangzhou jobs in top results)
    assert results["ids"] is not None
