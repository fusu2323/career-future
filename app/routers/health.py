"""Health check router with liveness and readiness probes."""

from openai import OpenAI
from fastapi import APIRouter, Depends, HTTPException

from app.models.llm_models import HealthResponse
from app.clients.deepseek import get_deepseek_client


router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_liveness() -> HealthResponse:
    """Lightweight liveness check — returns immediately without calling DeepSeek."""
    return HealthResponse(status="ok", service="llm-service")


@router.get("/health/ready", response_model=HealthResponse)
async def health_readiness(client: OpenAI = Depends(get_deepseek_client)) -> HealthResponse:
    """Readiness probe — calls DeepSeek with a minimal request to verify connectivity."""
    try:
        client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
            timeout=5.0,
        )
        return HealthResponse(status="ready", service="llm-service")
    except Exception:
        raise HTTPException(status_code=503, detail="DeepSeek not ready")
