"""
GLM-5 LLM Client
"""
from zhipuai import ZhipuAI
from app.config import settings
from typing import Optional, List, Dict, Any


_client: Optional[ZhipuAI] = None


def get_glm_client() -> ZhipuAI:
    """Get or create GLM client instance"""
    global _client
    if _client is None:
        _client = ZhipuAI(api_key=settings.GLM_API_KEY)
    return _client


def chat_completion(
    messages: List[Dict[str, str]],
    model: str = "glm-4",
    temperature: float = 0.7,
    **kwargs
) -> str:
    """
    Call GLM chat completion API

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name (glm-4, glm-4-flash, etc.)
        temperature: Sampling temperature
        **kwargs: Additional arguments to pass to API

    Returns:
        Generated text response
    """
    client = get_glm_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        **kwargs
    )
    return response.choices[0].message.content


def generate_with_json(
    prompt: str,
    system_prompt: str = "你是一个专业的 AI 助手。请始终以 JSON 格式返回响应。",
    **kwargs
) -> Any:
    """
    Call GLM with JSON output requirement

    Args:
        prompt: User prompt
        system_prompt: System instruction
        **kwargs: Additional arguments

    Returns:
        Parsed JSON response
    """
    import json

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    response = chat_completion(
        messages=messages,
        temperature=0.3,  # Lower temperature for more consistent JSON
        **kwargs
    )

    # Try to parse as JSON
    try:
        # Clean up potential markdown code blocks
        clean_response = response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()
        return json.loads(clean_response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}\nRaw response: {response}")
