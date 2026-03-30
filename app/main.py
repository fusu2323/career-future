"""FastAPI application entry point for LLM service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.routers import llm_router, health_router
from app.config import Settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    logger.info("Starting LLM service")
    try:
        settings = Settings()
    except ValidationError:
        raise RuntimeError("DEEPSEEK_API_KEY environment variable is not set")
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY environment variable is not set")
    logger.info("DEEPSEEK_API_KEY validated")
    yield
    logger.info("Shutting down LLM service")


app = FastAPI(
    title="LLM Service",
    version="1.0.0",
    description="DeepSeek API wrapper for career planning agent",
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Ensure HTTP exceptions return consistent {"detail": ...} JSON format."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/")
async def root():
    """Root endpoint with service metadata."""
    return {"service": "llm-service", "version": "1.0.0", "docs": "/docs"}


app.include_router(llm_router)
app.include_router(health_router)
