"""
LLM service — factory for creating configured LLM clients.
"""
from langchain_openai import ChatOpenAI
from app.config import get_settings

settings = get_settings()


def get_llm(temperature: float = None, max_tokens: int = None) -> ChatOpenAI:
    """Return a configured ChatOpenAI instance (works with OpenRouter or OpenAI)."""
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=temperature if temperature is not None else settings.llm_temperature,
        max_tokens=max_tokens or settings.llm_max_tokens,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )
