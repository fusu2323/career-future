from functools import lru_cache
from openai import OpenAI


@lru_cache
def get_deepseek_client() -> OpenAI:
    """Return a cached OpenAI client configured for DeepSeek API."""
    from app.config import Settings

    settings = Settings()
    return OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        timeout=60.0,
    )
