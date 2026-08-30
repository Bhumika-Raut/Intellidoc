from functools import lru_cache

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockProvider
from app.llm.openai_provider import OpenAICompatibleProvider

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    name = settings.llm_provider.lower().strip()
    if name == "mock":
        return MockProvider()
    if name == "groq":
        return OpenAICompatibleProvider(
            api_key=settings.groq_api_key or settings.openai_api_key,
            model=settings.llm_model,
            base_url=GROQ_BASE_URL,
        )
    if name == "openai":
        return OpenAICompatibleProvider(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            base_url=settings.openai_base_url or None,
        )
    # Any other value is treated as OpenAI-compatible with optional custom base URL.
    return OpenAICompatibleProvider(
        api_key=settings.openai_api_key or settings.groq_api_key,
        model=settings.llm_model,
        base_url=settings.openai_base_url or None,
    )
