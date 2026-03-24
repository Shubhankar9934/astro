from __future__ import annotations

import os
from typing import Any, Dict, Literal

GovernanceMode = Literal["strict", "degraded", "dev"]


def resolve_governance_mode(agents_cfg: Dict[str, Any]) -> GovernanceMode:
    """Env ASTRO_GOVERNANCE_MODE overrides YAML model_governance.governance_mode."""
    env = (os.environ.get("ASTRO_GOVERNANCE_MODE") or "").strip().lower()
    if env in ("strict", "degraded", "dev"):
        return env  # type: ignore[return-value]
    mg = agents_cfg.get("model_governance") or {}
    m = str(mg.get("governance_mode", "strict")).strip().lower()
    if m in ("strict", "degraded", "dev"):
        return m  # type: ignore[return-value]
    return "strict"


def model_missing_would_violate_governance(ctx_model, gov_cfg: Dict[str, Any]) -> bool:
    return bool(gov_cfg.get("enabled", True)) and not bool(
        gov_cfg.get("allow_llm_only_without_model", False)
    ) and (ctx_model is None)
