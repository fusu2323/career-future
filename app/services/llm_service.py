"""LLM service with retry, timeout, and JSON parse retry logic."""

import asyncio
import json
from openai import APITimeoutError, APIStatusError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.exceptions.llm_exceptions import LLMTimeoutError, LLMJSONParseError, LLMRetryExhaustedError


TIMEOUTS = {"profile": 15.0, "match": 20.0, "report": 45.0, "resume": 20.0}


def is_retryable_http_error(exc: Exception) -> bool:
    """Return True for retryable HTTP errors (5xx/503/timeout), False for 400/401."""
    if isinstance(exc, APITimeoutError):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code >= 500 or exc.status_code in (429, 503)
    return False


def _retry_if_retryable_http_error(exc: Exception) -> bool:
    """Tenacity retry predicate: only retry if is_retryable_http_error returns True."""
    return isinstance(exc, (APITimeoutError, APIStatusError)) and is_retryable_http_error(exc)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=_retry_if_retryable_http_error,
    reraise=True,
)
def _call_with_retry_sync(client, messages: list, timeout: float, **kwargs):
    """Synchronous LLM call with tenacity retry (3x, 1s/2s/4s backoff)."""
    return client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        response_format={"type": "json_object"},
        timeout=timeout,
        **kwargs,
    )


async def generate_structured(
    task_type: str,
    client,
    prompt: str,
    temperature: float = 0.1,
    max_tokens: int | None = None,
    timeout_override: float | None = None,
) -> dict:
    """
    Generate structured JSON from LLM with retry, timeout, and JSON parse retry.

    - HTTP retry: 3x with exponential backoff (1s/2s/4s)
    - Timeout: per task type (profile=15s, match=20s, report=45s, resume=20s)
    - JSON parse retry: up to 2 additional calls on parse failure
    """
    messages = [{"role": "user", "content": prompt}]
    kwargs = {"temperature": temperature}
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    timeout_seconds = timeout_override if timeout_override is not None else TIMEOUTS[task_type]

    for attempt in range(3):
        try:
            async with asyncio.timeout(timeout_seconds):
                response = await asyncio.to_thread(
                    _call_with_retry_sync, client, messages, timeout_seconds, **kwargs
                )
            content = response.choices[0].message.content
            return json.loads(content)
        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"Task {task_type} exceeded {timeout_seconds}s limit")
        except (APITimeoutError, APIStatusError) as e:
            if not is_retryable_http_error(e):
                raise LLMRetryExhaustedError(f"Non-retryable HTTP error: {e}")
            if attempt == 2:
                raise LLMRetryExhaustedError(f"HTTP retry exhausted after 3 attempts: {e}")
            # Retry on next attempt
        except json.JSONDecodeError as e:
            if attempt == 2:
                raise LLMJSONParseError(
                    f"Failed after 3 parse attempts, raw: {content[:200]}"
                )
            # Retry on next attempt
