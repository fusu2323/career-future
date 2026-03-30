"""LLM router with three POST endpoints for profile/match/report generation."""

from openai import OpenAI
from fastapi import APIRouter, Depends, HTTPException

from app.models.llm_models import LLMGenerateRequest, LLMGenerateResponse
from app.clients.deepseek import get_deepseek_client
from app.services.llm_service import generate_structured
from app.exceptions.llm_exceptions import (
    LLMTimeoutError,
    LLMJSONParseError,
    LLMRetryExhaustedError,
)


router = APIRouter(prefix="/llm", tags=["LLM"])


def _handle_llm_error(e: Exception) -> HTTPException:
    """Map LLM exception types to HTTP status codes."""
    if isinstance(e, LLMTimeoutError):
        return HTTPException(status_code=504, detail=str(e))
    if isinstance(e, LLMJSONParseError):
        return HTTPException(status_code=422, detail=str(e))
    if isinstance(e, LLMRetryExhaustedError):
        return HTTPException(status_code=502, detail=str(e))
    return HTTPException(status_code=500, detail=f"LLM service error: {e}")


@router.post("/profile/generate", response_model=LLMGenerateResponse)
async def generate_profile(
    request: LLMGenerateRequest,
    client: OpenAI = Depends(get_deepseek_client),
) -> LLMGenerateResponse:
    """Generate a profile (student or job) using the LLM."""
    try:
        result = await generate_structured(
            "profile", client, request.prompt, request.temperature, request.max_tokens
        )
        return LLMGenerateResponse(success=True, data=result, task_type="profile", attempt_count=1)
    except Exception as e:
        raise _handle_llm_error(e)


@router.post("/match/analyze", response_model=LLMGenerateResponse)
async def analyze_match(
    request: LLMGenerateRequest,
    client: OpenAI = Depends(get_deepseek_client),
) -> LLMGenerateResponse:
    """Analyze person-job match using the LLM."""
    try:
        result = await generate_structured(
            "match", client, request.prompt, request.temperature, request.max_tokens
        )
        return LLMGenerateResponse(success=True, data=result, task_type="match", attempt_count=1)
    except Exception as e:
        raise _handle_llm_error(e)


@router.post("/report/generate", response_model=LLMGenerateResponse)
async def generate_report(
    request: LLMGenerateRequest,
    client: OpenAI = Depends(get_deepseek_client),
) -> LLMGenerateResponse:
    """Generate a career planning report using the LLM."""
    try:
        result = await generate_structured(
            "report", client, request.prompt, request.temperature, request.max_tokens
        )
        return LLMGenerateResponse(success=True, data=result, task_type="report", attempt_count=1)
    except Exception as e:
        raise _handle_llm_error(e)
