from functools import lru_cache
from openai import OpenAI
from app.config import Settings

_settings = Settings()


@lru_cache
def get_deepseek_client() -> OpenAI:
    """Return a cached OpenAI client configured for DeepSeek API."""
    return OpenAI(
        api_key=_settings.deepseek_api_key,
        base_url=_settings.deepseek_base_url,
        timeout=60.0,
    )
