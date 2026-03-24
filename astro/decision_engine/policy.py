from __future__ import annotations

from typing import Any, Dict, Literal, Optional, Tuple

from astro.decision_engine.state_manager import ModelPrediction

Signal = Literal["BUY", "SELL", "HOLD"]


def _norm(sig: str) -> Signal:
    s = (sig or "HOLD").strip().upper()
    if s in ("BUY", "SELL", "HOLD"):
        return s  # type: ignore[return-value]
    return "HOLD"


def apply_model_governance_detailed(
    llm_signal: str,
    model: Optional[ModelPrediction],
    governance_cfg: Dict[str, Any],
) -> Tuple[Signal, Dict[str, Any]]:
    """Return final signal and audit metadata (provenance for API / logs)."""
    meta: Dict[str, Any] = {
        "governance_enabled": bool(governance_cfg.get("enabled", True)),
        "model_present": model is not None,
        "raw_llm_signal": _norm(llm_signal),
        "reason": "",
        "min_edge_for_directional": float(governance_cfg.get("min_edge_for_directional", 0.08)),
        "edge_achieved": None,
    }
    if not governance_cfg.get("enabled", True):
        sig = _norm(llm_signal)
        meta["reason"] = "governance_disabled"
        return sig, meta

    allow_llm = bool(governance_cfg.get("allow_llm_only_without_model", False))
    override = bool(governance_cfg.get("agents_can_override_direction", False))
    llm = _norm(llm_signal)
    meta["raw_llm_signal"] = llm

    if model is None:
        meta["reason"] = "no_model_llm_allowed" if allow_llm else "no_model_forced_hold"
        return (llm if allow_llm else "HOLD"), meta

    strong = float(governance_cfg.get("min_edge_for_directional", 0.08))
    weak_raw = governance_cfg.get("min_edge_weak")
    weak = float(weak_raw) if weak_raw is not None else strong
    if weak > strong:
        weak = strong
    meta["min_edge_weak"] = weak
    meta["min_edge_strong"] = strong

    dev = abs(model.p_up - 0.5)
    meta["edge_achieved"] = dev

    if dev < weak:
        meta["edge_band"] = "none"
        meta["reason"] = "below_min_edge_weak_hold"
        return "HOLD", meta

    if dev < strong:
        meta["edge_band"] = "weak"
        if bool(governance_cfg.get("allow_llm_in_weak_band", False)):
            meta["reason"] = "weak_band_llm_direction"
            return llm, meta
        meta["reason"] = "weak_band_hold"
        return "HOLD", meta

    meta["edge_band"] = "strong"
    mdir: Signal = "BUY" if model.p_up > 0.5 else "SELL"
    meta["model_direction"] = mdir
    if not override:
        meta["reason"] = "model_primary_no_override"
        return mdir, meta
    if llm == "HOLD":
        meta["reason"] = "model_primary_llm_hold"
        return mdir, meta
    if llm == mdir:
        meta["reason"] = "model_aligns_with_llm"
        return llm, meta
    meta["reason"] = "model_overrides_llm_conflict"
    return mdir, meta


def apply_model_governance(
    llm_signal: str,
    model: Optional[ModelPrediction],
    governance_cfg: Dict[str, Any],
) -> Signal:
    """Enforce transformer-primary policy when enabled."""
    sig, _ = apply_model_governance_detailed(llm_signal, model, governance_cfg)
    return sig


def should_upgrade_fast_to_full(
    model: Optional[ModelPrediction],
    agents_cfg: Dict[str, Any],
) -> bool:
    """High uncertainty triggers full research pipeline even when user asked for fast."""
    if model is None:
        return False
    thr = float(agents_cfg.get("uncertainty_debate_threshold", 0.15))
    return float(model.uncertainty) > thr


def should_skip_research_debate(
    model: Optional[ModelPrediction],
    agents_cfg: Dict[str, Any],
) -> bool:
    if model is None:
        return False
    if not bool(agents_cfg.get("skip_debate_if_certain", False)):
        return False
    mx = float(agents_cfg.get("uncertainty_certainty_max", 0.05))
    return float(model.uncertainty) <= mx
