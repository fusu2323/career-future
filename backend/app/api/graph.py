"""
Career Graph API

Endpoints for knowledge graph queries (promotion paths, transition paths).
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional, Literal

from app.services.neo4j_db import get_neo4j_driver


router = APIRouter(prefix="/graph", tags=["Graph"])


@router.get("/career-path")
async def get_career_path(
    category: str = Query(..., description="Job category (e.g., '前端开发', '后端开发')"),
    path_type: Literal["vertical", "horizontal"] = Query("vertical", description="Path type")
):
    """
    Get career path information.

    - **category**: Job category name
    - **path_type**: "vertical" for promotion path, "horizontal" for transition options
    """
    try:
        driver = get_neo4j_driver()

        if path_type == "vertical":
            # Query vertical promotion path
            with driver.session() as session:
                result = session.run("""
                    MATCH (jc:JobCategory {name: $category})
                    OPTIONAL MATCH (jl:JobLevel {category: $category})
                    WITH jc, jl
                    ORDER BY jl.level ASC
                    RETURN
                        jc.name AS category,
                        jc.job_count AS job_count,
                        jc.top_skills AS top_skills,
                        jc.avg_salary AS avg_salary,
                        COLLECT(jl.name) AS promotion_levels
                """, {"category": category})

                record = result.single()

                if not record:
                    raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

                return {
                    "category": record["category"],
                    "job_count": record["job_count"],
                    "top_skills": record["top_skills"] or [],
                    "avg_salary": record["avg_salary"] or 0,
                    "path_type": "vertical",
                    "path": record["promotion_levels"] or []
                }

        else:  # horizontal
            # Query horizontal transition options
            with driver.session() as session:
                result = session.run("""
                    MATCH (jc:JobCategory {name: $category})
                    OPTIONAL MATCH (jc)-[t:TRANSITION_TO]->(target:JobCategory)
                    RETURN
                        jc.name AS category,
                        COLLECT({
                            target: target.name,
                            required_skills: t.required_skills
                        }) AS transitions
                """, {"category": category})

                record = result.single()

                if not record:
                    raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

                return {
                    "category": record["category"],
                    "path_type": "horizontal",
                    "transitions": record["transitions"] or []
                }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph query failed: {str(e)}")


@router.get("/categories")
async def get_all_categories():
    """Get all job categories in the graph."""
    try:
        driver = get_neo4j_driver()

        with driver.session() as session:
            result = session.run("""
                MATCH (jc:JobCategory)
                RETURN jc.name AS name, jc.job_count AS job_count
                ORDER BY jc.job_count DESC
            """)

            categories = []
            for record in result:
                categories.append({
                    "name": record["name"],
                    "job_count": record["job_count"]
                })

            return {
                "categories": categories,
                "total": len(categories)
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.get("/stats")
async def get_graph_stats():
    """Get knowledge graph statistics."""
    try:
        driver = get_neo4j_driver()

        with driver.session() as session:
            stats = {}

            # Count nodes
            node_result = session.run("""
                MATCH (n)
                RETURN
                    COUNT(DISTINCT n) AS total_nodes,
                    COUNT(DISTINCT n:JobCategory) AS category_nodes,
                    COUNT(DISTINCT n:JobLevel) AS level_nodes
            """)
            node_record = node_result.single()
            stats["nodes"] = {
                "total": node_record["total_nodes"] or 0,
                "categories": node_record["category_nodes"] or 0,
                "levels": node_record["level_nodes"] or 0
            }

            # Count relationships
            rel_result = session.run("""
                MATCH ()-[r]->()
                RETURN
                    COUNT(r) AS total_rels,
                    COUNT(r:PROMOTE_TO) AS promote_rels,
                    COUNT(r:TRANSITION_TO) AS transition_rels
            """)
            rel_record = rel_result.single()
            stats["relationships"] = {
                "total": rel_record["total_rels"] or 0,
                "promotions": rel_record["promote_rels"] or 0,
                "transitions": rel_record["transition_rels"] or 0
            }

            return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
