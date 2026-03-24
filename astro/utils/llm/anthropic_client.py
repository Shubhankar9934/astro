from typing import Any, Optional

from astro.utils.llm.base_client import BaseLLMClient
from astro.utils.llm.validators import validate_model


class AnthropicClient(BaseLLMClient):
    def __init__(self, model: str, base_url: Optional[str] = None, **kwargs):
        super().__init__(model, base_url, **kwargs)

    def get_llm(self) -> Any:
        from langchain_anthropic import ChatAnthropic

        llm_kwargs = {"model": self.model}
        for key in (
            "timeout",
            "max_retries",
            "api_key",
            "max_tokens",
            "callbacks",
            "http_client",
            "http_async_client",
            "temperature",
        ):
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]
        return ChatAnthropic(**llm_kwargs)

    def validate_model(self) -> bool:
        return validate_model("anthropic", self.model)
