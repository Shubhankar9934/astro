import os
from typing import Any, Optional

from langchain_openai import ChatOpenAI

from astro.utils.llm.base_client import BaseLLMClient
from astro.utils.llm.validators import validate_model


class UnifiedChatOpenAI(ChatOpenAI):
    def __init__(self, **kwargs):
        if "gpt-5" in kwargs.get("model", "").lower():
            kwargs.pop("temperature", None)
            kwargs.pop("top_p", None)
        super().__init__(**kwargs)


class OpenAIClient(BaseLLMClient):
    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        provider: str = "openai",
        **kwargs,
    ):
        super().__init__(model, base_url, **kwargs)
        self.provider = provider.lower()

    def get_llm(self) -> Any:
        llm_kwargs = {"model": self.model}
        if self.provider == "xai":
            llm_kwargs["base_url"] = "https://api.x.ai/v1"
            api_key = os.environ.get("XAI_API_KEY")
            if api_key:
                llm_kwargs["api_key"] = api_key
        elif self.provider == "openrouter":
            llm_kwargs["base_url"] = "https://openrouter.ai/api/v1"
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if api_key:
                llm_kwargs["api_key"] = api_key
        elif self.provider == "ollama":
            llm_kwargs["base_url"] = "http://localhost:11434/v1"
            llm_kwargs["api_key"] = "ollama"
        elif self.base_url:
            llm_kwargs["base_url"] = self.base_url
        for key in (
            "timeout",
            "max_retries",
            "reasoning_effort",
            "api_key",
            "callbacks",
            "http_client",
            "http_async_client",
            "temperature",
            "top_p",
        ):
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]
        if self.provider == "openai" and not llm_kwargs.get("api_key"):
            k = os.environ.get("OPENAI_API_KEY")
            if k:
                llm_kwargs["api_key"] = k
        return UnifiedChatOpenAI(**llm_kwargs)

    def validate_model(self) -> bool:
        return validate_model(self.provider, self.model)
