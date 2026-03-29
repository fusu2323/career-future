import pytest
import json
from pathlib import Path


@pytest.fixture
def jobs_cleaned_path():
    return Path("data/processed/jobs_cleaned.json")


@pytest.fixture
def vector_db_path():
    return Path("data/vector_db")


@pytest.fixture
def collection(vector_db_path):
    import chromadb
    client = chromadb.PersistentClient(path=str(vector_db_path))
    return client.get_collection("job_postings")


@pytest.fixture
def sample_job_record(jobs_cleaned_path):
    with open(jobs_cleaned_path, encoding="utf-8") as f:
        jobs = json.load(f)
    return jobs[0]
