from typing import Literal, Optional
from pydantic import BaseModel, Field


class LLMGenerateRequest(BaseModel):
    """Request model for LLM generation endpoints."""

    task_type: Literal["profile", "match", "report"] = Field(
        ..., description="Task type determines timeout and routing"
    )
    prompt: str = Field(..., min_length=1, description="LLM prompt text")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)


class LLMGenerateResponse(BaseModel):
    """Response model for LLM generation endpoints."""

    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    task_type: str
    attempt_count: int = 1


class HealthResponse(BaseModel):
    """Response model for health check endpoints."""

    status: str
    service: str = "llm-service"
