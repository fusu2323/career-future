"""
Database Initialization Script

Run this script to initialize the Neo4j database with constraints and indexes.
Usage: python scripts/init_db.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.neo4j_db import init_neo4j_database, verify_neo4j_connection
from app.services.chroma_db import get_chroma_client


def main():
    print("=" * 50)
    print("Database Initialization Script")
    print("=" * 50)

    # Initialize Neo4j
    print("\n[1/2] Initializing Neo4j database...")
    try:
        init_neo4j_database()
        print("Neo4j initialization completed!")
    except Exception as e:
        print(f"Neo4j initialization failed: {e}")
        return 1

    # Verify Neo4j connection
    print("\n[2/2] Verifying database connections...")

    neo4j_status = verify_neo4j_connection()
    print(f"\nNeo4j Status:")
    for key, value in neo4j_status.items():
        print(f"  {key}: {value}")

    # Verify Chroma connection
    print(f"\nChroma Status:")
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        print(f"  Connected: True")
        print(f"  Collections: {[c.name for c in collections]}")
    except Exception as e:
        print(f"  Connected: False")
        print(f"  Error: {e}")

    print("\n" + "=" * 50)
    print("Database initialization completed!")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    exit(main())
