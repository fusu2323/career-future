"""
Database Health Check API
"""
from fastapi import APIRouter
from app.services.neo4j_db import verify_neo4j_connection
from app.services.chroma_db import get_chroma_client

router = APIRouter(tags=["health"])


@router.get("/db")
async def database_health():
    """Check database connections status"""
    neo4j_status = verify_neo4j_connection()

    chroma_status = {"connected": False}
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        chroma_status = {
            "connected": True,
            "collection_count": len(collections),
            "collections": [c.name for c in collections]
        }
    except Exception as e:
        chroma_status["error"] = str(e)

    return {
        "neo4j": neo4j_status,
        "chroma": chroma_status
    }
