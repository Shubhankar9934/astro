from __future__ import annotations

from typing import Any, Callable, Dict, List

AnalystKey = str
StepFn = Callable[[Dict[str, Any]], Dict[str, Any]]


def build_analyst_chain(
    selected: List[AnalystKey],
    factories: Dict[AnalystKey, StepFn],
) -> List[StepFn]:
    chain = []
    for key in selected:
        if key not in factories:
            raise ValueError(f"Unknown analyst: {key}")
        chain.append(factories[key])
    return chain
