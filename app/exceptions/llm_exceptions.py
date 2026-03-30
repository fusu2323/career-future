"""Custom exception types for LLM service errors."""


class LLMServiceError(Exception):
    """Base exception for all LLM service errors."""

    pass


class LLMTimeoutError(LLMServiceError):
    """Raised when asyncio.timeout fires for a task."""

    pass


class LLMJSONParseError(LLMServiceError):
    """Raised when JSON parse fails after max retries."""

    pass


class LLMRetryExhaustedError(LLMServiceError):
    """Raised when all 3 HTTP retries fail."""

    pass


class LLMValidationError(LLMServiceError):
    """Raised when LLM returns invalid structure despite successful JSON parse."""

    pass
