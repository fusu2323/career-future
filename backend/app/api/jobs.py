"""
Job Positions API

Endpoints for job search, profiles, and related operations.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from pathlib import Path

from app.services.chroma_db import get_chroma_client, get_chroma_collection

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobSearchRequest(BaseModel):
    query: str
    top_k: int = 10
    category: Optional[str] = None


class JobSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total: int


@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest):
    """
    Search jobs by text query using vector similarity.

    - **query**: Search text (e.g., "Java 后端开发")
    - **top_k**: Number of results to return (default: 10)
    - **category**: Optional filter by job category
    """
    try:
        # Use job_profiles collection (built by build_knowledge_graph.py)
        client = get_chroma_client()
        collection = client.get_or_create_collection(name="job_profiles")

        # Query Chroma
        results = collection.query(
            query_texts=[request.query],
            n_results=request.top_k,
            include=["documents", "metadatas", "distances"]
        )

        # Format results
        job_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0

                job_results.append({
                    "document": doc,
                    "category": metadata.get('category', ''),
                    "skills": metadata.get('skills', '').split(',') if metadata.get('skills') else [],
                    "distance": round(distance, 4),
                    "relevance_score": round(1 / (1 + distance), 4)
                })

        return {
            "results": job_results,
            "total": len(job_results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/profiles", response_model=List[Dict[str, Any]])
async def get_job_profiles(
    category: Optional[str] = Query(None, description="Filter by job category"),
    limit: int = Query(20, description="Max results to return")
):
    """
    Get job profiles list.

    - **category**: Optional filter by category (e.g., "前端开发")
    - **limit**: Maximum number of results (default: 20)
    """
    try:
        import json

        profiles_path = PROJECT_ROOT / "data" / "processed" / "job_profiles.json"
        if not profiles_path.exists():
            raise HTTPException(status_code=404, detail="Job profiles not found")

        with open(profiles_path, 'r', encoding='utf-8') as f:
            all_profiles = json.load(f)

        # Filter by category if provided
        if category:
            filtered = [p for p in all_profiles if p.get('job_category') == category]
        else:
            filtered = all_profiles

        # Return sample (group by category for aggregated view)
        categories_path = PROJECT_ROOT / "data" / "processed" / "job_categories.json"
        if categories_path.exists():
            with open(categories_path, 'r', encoding='utf-8') as f:
                categories = json.load(f)

            # Return category-level profiles
            if category and category in categories:
                return [categories[category]]
            elif not category:
                return list(categories.values())[:limit]

        # Fallback to individual profiles
        return filtered[:limit]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profiles: {str(e)}")


@router.get("/categories")
async def get_categories():
    """Get all job categories with summary stats."""
    try:
        import json

        categories_path = PROJECT_ROOT / "data" / "processed" / "job_categories.json"
        if not categories_path.exists():
            return {"categories": [], "total": 0}

        with open(categories_path, 'r', encoding='utf-8') as f:
            categories = json.load(f)

        # Format summary
        summary = []
        for cat_name, cat_data in categories.items():
            summary.append({
                "name": cat_name,
                "job_count": cat_data.get('job_count', 0),
                "top_skills": cat_data.get('top_skills', [])[:5],
                "avg_salary": cat_data.get('avg_salary', 0),
                "top_cities": cat_data.get('top_cities', [])[:3]
            })

        return {
            "categories": sorted(summary, key=lambda x: -x['job_count']),
            "total": len(summary)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")
