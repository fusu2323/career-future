"""
Build job vector index - Phase 2
Loads jobs_cleaned.json, embeds with BGE-large-zh, stores in ChromaDB.

Implementation per 02-CONTEXT.md decisions:
- D-01: BGE-large-zh (~1024 dimensions)
- D-02: Concatenated text: {job_title} | {company_name} | {industry_tags} | {job_detail}
- D-05: Collection = job_postings with specific metadata fields
- D-06: Input = data/processed/jobs_cleaned.json
"""
import json
from pathlib import Path
from FlagEmbedding import BGEM3FlagModel
import chromadb

# Config
JOBS_CLEANED_PATH = "data/processed/jobs_cleaned.json"
VECTOR_DB_PATH = "data/vector_db"
COLLECTION_NAME = "job_postings"
BATCH_SIZE = 32
MAX_LENGTH = 512


def load_jobs(path):
    """Load cleaned job records from JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_job_text(record):
    """Concatenate full record per D-02.
    Format: {job_title} | {company_name} | {industry_tags joined by comma} | {job_detail}
    """
    title = record.get("岗位名称", "")
    company = record.get("公司名称", "")
    industries = ",".join(record.get("industry_tags", []) or [])
    detail = record.get("job_detail_cleaned", "") or ""
    return f"{title} | {company} | {industries} | {detail}"


def build_metadata(record):
    """Build metadata dict per D-05, omitting None values (ChromaDB requirement)."""
    meta = {}
    if record.get("岗位编码"):
        meta["job_id"] = record["岗位编码"]
    if record.get("岗位名称"):
        meta["title"] = record["岗位名称"]
    if record.get("公司名称"):
        meta["company_name"] = record["公司名称"]
    if record.get("city"):
        meta["city"] = record["city"]
    if record.get("district"):
        meta["district"] = record["district"]
    if record.get("industry_primary"):
        meta["industry_primary"] = record["industry_primary"]
    if record.get("salary_min_monthly") is not None:
        meta["salary_min_monthly"] = record["salary_min_monthly"]
    if record.get("salary_max_monthly") is not None:
        meta["salary_max_monthly"] = record["salary_max_monthly"]
    if record.get("company_size_min") is not None:
        meta["company_size_min"] = record["company_size_min"]
    if record.get("company_size_max") is not None:
        meta["company_size_max"] = record["company_size_max"]
    return meta


def main():
    # Load data
    jobs = load_jobs(JOBS_CLEANED_PATH)
    print(f"Loaded {len(jobs)} job records")

    # Build texts and metadata
    texts = [build_job_text(j) for j in jobs]
    job_ids = [j.get("岗位编码") for j in jobs]
    metadatas = [build_metadata(j) for j in jobs]

    # Encode in batches with progress
    print("Loading BGE-large-zh model...")
    model = BGEM3FlagModel("BAAI/bge-large-zh-v1.5", use_fp16=True)

    print("Encoding job texts...")
    all_embeddings = []
    total = len(texts)
    for i in range(0, total, BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        encoded = model.encode(batch, max_length=MAX_LENGTH, batch_size=len(batch))
        all_embeddings.extend(encoded["dense_vecs"])
        print(f"  Encoded {min(i + BATCH_SIZE, total)}/{total}")

    # Persist ChromaDB
    Path(VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

    # Delete existing collection if present (safe re-run)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    print("Inserting vectors into ChromaDB...")
    collection.add(
        ids=job_ids,
        embeddings=all_embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    print(f"Indexed {collection.count()} records in collection '{COLLECTION_NAME}'")


if __name__ == "__main__":
    main()
