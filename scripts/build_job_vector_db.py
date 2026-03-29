"""
Build job vector index - Phase 2
Loads jobs_cleaned.json, embeds with BGE-m3 via SiliconFlow API, stores in ChromaDB.

Implementation per 02-CONTEXT.md decisions:
- D-02: Concatenated text: {job_title} | {company_name} | {industry_tags} | {job_detail}
- D-05: Collection = job_postings with specific metadata fields
- D-06: Input = data/processed/jobs_cleaned.json
- Embedding: SiliconFlow API with BAAI/bge-m3 model (~1024 dimensions)
"""
import json
import time
from pathlib import Path
import requests
import chromadb

# Config
JOBS_CLEANED_PATH = "data/processed/jobs_cleaned.json"
VECTOR_DB_PATH = "data/vector_db"
COLLECTION_NAME = "job_postings"
SILICONFLOW_API_KEY = "sk-inhxcgiznrjsgevgcttsuifahalqzlmmrmylbeueepmoxrvl"
SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1/embeddings"
EMBEDDING_MODEL = "BAAI/bge-m3"
BATCH_SIZE = 16  # API batch size (records per request)


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


def get_embedding(text, retry=3):
    """Get embedding for a single text via SiliconFlow API."""
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": EMBEDDING_MODEL,
        "input": text,
    }
    for attempt in range(retry):
        try:
            resp = requests.post(SILICONFLOW_API_URL, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return data["data"][0]["embedding"]
            elif resp.status_code == 429:
                # Rate limited, wait and retry
                time.sleep(2 ** attempt)
                continue
            else:
                raise Exception(f"API error {resp.status_code}: {resp.text}")
        except requests.exceptions.RequestException as e:
            if attempt < retry - 1:
                time.sleep(1)
                continue
            raise
    raise Exception("Max retries exceeded")


def get_embeddings_batch(texts, retry=3):
    """Get embeddings for multiple texts in one API call.
    SiliconFlow API accepts array input for batch embedding.
    """
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json",
    }
    # Try batch API first (array input)
    payload = {
        "model": EMBEDDING_MODEL,
        "input": texts,  # Array of strings
    }
    for attempt in range(retry):
        try:
            resp = requests.post(SILICONFLOW_API_URL, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                # Sort by index to maintain order
                embeddings = sorted(data["data"], key=lambda x: x["index"])
                return [e["embedding"] for e in embeddings]
            elif resp.status_code == 400 or resp.status_code == 20015:
                # Batch not supported, fall back to individual calls
                break
            elif resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            else:
                raise Exception(f"API error {resp.status_code}: {resp.text}")
        except requests.exceptions.RequestException as e:
            if attempt < retry - 1:
                time.sleep(1)
                continue
            raise
    # Fall back to individual calls
    embeddings = []
    for text in texts:
        embeddings.append(get_embedding(text, retry))
        time.sleep(0.05)  # Rate limiting
    return embeddings


def main():
    # Load data
    jobs = load_jobs(JOBS_CLEANED_PATH)
    print(f"Loaded {len(jobs)} job records")

    # Build texts and metadata
    texts = [build_job_text(j) for j in jobs]
    job_ids = [j.get("岗位编码") for j in jobs]
    metadatas = [build_metadata(j) for j in jobs]

    # Encode in batches via API
    print(f"Encoding {len(texts)} job texts via SiliconFlow BGE-m3 API...")
    all_embeddings = []
    total = len(texts)
    start_time = time.time()

    for i in range(0, total, BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_embeddings = get_embeddings_batch(batch)
        all_embeddings.extend(batch_embeddings)
        elapsed = time.time() - start_time
        progress = min(i + BATCH_SIZE, total)
        rate = progress / elapsed if elapsed > 0 else 0
        eta = (total - progress) / rate if rate > 0 else 0
        print(f"  Encoded {progress}/{total} ({progress/total*100:.1f}%) - ETA: {eta:.0f}s")

    encode_time = time.time() - start_time
    print(f"Encoding complete in {encode_time:.1f}s")

    # Persist ChromaDB
    Path(VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

    # Delete existing collection if present (safe re-run)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    # BGE-m3 uses cosine similarity internally, store with cosine metric
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    print("Inserting vectors into ChromaDB...")
    INSERT_BATCH = 200  # ChromaDB max batch is ~5461, use smaller for safety
    for i in range(0, len(job_ids), INSERT_BATCH):
        chunk_end = min(i + INSERT_BATCH, len(job_ids))
        chunk_ids = job_ids[i:chunk_end]
        chunk_embs = all_embeddings[i:chunk_end]
        chunk_docs = texts[i:chunk_end]
        chunk_metas = metadatas[i:chunk_end]
        print(f"  Chunk {i}: {len(chunk_ids)} records (total {len(job_ids)})")
        collection.add(
            ids=chunk_ids,
            embeddings=chunk_embs,
            documents=chunk_docs,
            metadatas=chunk_metas,
        )
        print(f"  Inserted chunk {i}, collection count: {collection.count()}")
    print(f"Indexed {collection.count()} records in collection '{COLLECTION_NAME}'")


if __name__ == "__main__":
    main()
