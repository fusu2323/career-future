"""
Chroma Vector Database Client
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings


_chroma_client = None


def get_chroma_client() -> chromadb.Client:
    """Get or create Chroma client instance"""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
    return _chroma_client


def get_chroma_collection(name: str = "job_positions") -> chromadb.Collection:
    """Get or create Chroma collection for job positions"""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=name,
        metadata={"description": "Job position embeddings for career planning", "hnsw:space": "cosine"}
    )
    return collection
