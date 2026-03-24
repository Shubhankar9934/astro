from typing import Optional

from astro.utils.llm.anthropic_client import AnthropicClient
from astro.utils.llm.base_client import BaseLLMClient
from astro.utils.llm.google_client import GoogleClient
from astro.utils.llm.openai_client import OpenAIClient


def create_llm_client(
    provider: str,
    model: str,
    base_url: Optional[str] = None,
    **kwargs,
) -> BaseLLMClient:
    provider_lower = provider.lower()
    if provider_lower in ("openai", "ollama", "openrouter"):
        return OpenAIClient(model, base_url, provider=provider_lower, **kwargs)
    if provider_lower == "xai":
        return OpenAIClient(model, base_url, provider="xai", **kwargs)
    if provider_lower == "anthropic":
        return AnthropicClient(model, base_url, **kwargs)
    if provider_lower == "google":
        return GoogleClient(model, base_url, **kwargs)
    raise ValueError(f"Unsupported LLM provider: {provider}")
