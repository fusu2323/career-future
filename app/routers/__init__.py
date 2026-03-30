# app.routers package

from app.routers.llm import router as llm_router
from app.routers.health import router as health_router
from app.routers.resume import router as resume_router

__all__ = ["llm_router", "health_router", "resume_router"]
