"""
FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.neo4j_db import init_neo4j_database, close_neo4j_driver
from app.api import health
from app.api import jobs
from app.api import graph
from app.api import resume
from app.api import student
from app.api import matching
from app.api import report


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting up Career Planning AI Agent API...")
    print(f"Environment: {settings.APP_ENV}")

    # Initialize Neo4j database (create constraints and indexes)
    try:
        init_neo4j_database()
        print("Neo4j database initialized successfully")
    except Exception as e:
        print(f"Warning: Neo4j initialization failed: {e}")

    print("Startup complete!")

    yield

    # Shutdown
    print("Shutting down...")
    close_neo4j_driver()
    print("Shutdown complete!")


app = FastAPI(
    title="Career Planning AI Agent",
    description="基于 AI 的大学生职业规划智能体 - Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health")
app.include_router(jobs.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(resume.router, prefix="/api")
app.include_router(student.router, prefix="/api")
app.include_router(matching.router, prefix="/api")
app.include_router(report.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "Career Planning AI Agent API",
        "version": "1.0.0",
        "port": 9090,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "port": 9090}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9090)
