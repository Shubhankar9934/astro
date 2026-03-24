from typing import Any, Callable, Dict, Protocol


class AgentNode(Protocol):
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]: ...
