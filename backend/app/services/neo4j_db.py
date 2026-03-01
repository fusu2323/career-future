"""
Neo4j Graph Database Client
"""
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from app.config import settings
from typing import Optional


_driver: Optional[GraphDatabase.driver] = None


def get_neo4j_driver() -> GraphDatabase.driver:
    """Get or create Neo4j driver instance"""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
    return _driver


def close_neo4j_driver():
    """Close Neo4j driver connection"""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def init_neo4j_database():
    """
    Initialize Neo4j database with constraints and indexes.
    Uses the default 'neo4j' database (Community Edition compatible).
    """
    driver = get_neo4j_driver()

    try:
        # Use default 'neo4j' database for Community Edition compatibility
        with driver.session() as session:
            # Create unique constraint for Job nodes
            session.run("""
                CREATE CONSTRAINT job_id_unique IF NOT EXISTS
                FOR (j:Job) REQUIRE j.job_id IS UNIQUE
            """)
            print("Created constraint: job_id_unique")

            # Create index for job name searches
            session.run("""
                CREATE INDEX job_name_index IF NOT EXISTS
                FOR (j:Job) ON (j.name)
            """)
            print("Created index: job_name_index")

            # Create index for company searches
            session.run("""
                CREATE INDEX job_company_index IF NOT EXISTS
                FOR (j:Job) ON (j.company)
            """)
            print("Created index: job_company_index")

            # Create index for industry searches
            session.run("""
                CREATE INDEX job_industry_index IF NOT EXISTS
                FOR (j:Job) ON (j.industry)
            """)
            print("Created index: job_industry_index")

        print("Neo4j database initialization completed successfully")

    except ServiceUnavailable as e:
        print(f"Neo4j connection failed: {e}")
        raise
    except Exception as e:
        print(f"Error initializing Neo4j: {e}")
        raise


def verify_neo4j_connection() -> dict:
    """Verify Neo4j connection and database status"""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            record = result.single()
            node_count = record["node_count"] if record else 0

        return {
            "connected": True,
            "node_count": node_count,
            "uri": settings.NEO4J_URI
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }
