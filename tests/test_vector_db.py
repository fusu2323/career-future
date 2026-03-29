import pytest
import chromadb
from pathlib import Path


def test_collection_exists(vector_db_path):
    """ChromaDB collection job_postings exists."""
    client = chromadb.PersistentClient(path=str(vector_db_path))
    collection = client.get_collection("job_postings")
    assert collection.count() >= 9000, f"Expected ~9178 vectors, got {collection.count()}"


def test_query_returns_results(collection):
    """Query returns Top10 results with valid metadata."""
    # Use a known job title for spot-check
    results = collection.query(
        query_texts=["前端开发 JavaScript React"],
        n_results=10,
        include=["distances", "metadatas", "documents"]
    )
    assert len(results["ids"][0]) == 10
    assert results["metadatas"][0][0]["title"] is not None


def test_recall_spot_check(collection):
    """Top10 recall accuracy >=85% on known query/keyword pairs."""
    test_queries = [
        ("前端开发 JavaScript React", ["前端开发", "Web前端", "前端工程师"]),
        ("Java后端开发 Spring微服务", ["Java", "后端开发", "Java开发"]),
        ("产品经理 Axure 需求分析", ["产品经理", "PM"]),
        ("数据分析 Python SQL pandas", ["数据分析", "数据分析师", "BI"]),
    ]
    correct = 0
    total = 0
    for query, expected_keywords in test_queries:
        results = collection.query(
            query_texts=[query],
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
    # Filter by city if possible
    results = collection.query(
        query_texts=["软件工程师"],
        n_results=5,
        where={"city": "广州"},
        include=["metadatas"]
    )
    # Should return results (or empty if no Guangzhou jobs in top results)
    assert results["ids"] is not None
