from __future__ import annotations

from typing import Any, Dict, Tuple

from astro.agents.risk.exposure_manager import ExposureManager
from astro.agents.risk.position_sizer import size_with_vol_signal


def clamp_signal_for_portfolio(
    signal: str,
    exposure: ExposureManager,
    risk_cfg: Dict[str, Any],
    *,
    nav: float = 1_000_000.0,
) -> str:
    """Reduce BUY to HOLD if gross exposure exceeds configured cap."""
    s = (signal or "HOLD").upper()
    max_gross = float(risk_cfg.get("max_gross_exposure_fraction", 1.0))
    if s == "BUY" and exposure.notional_fraction(nav) >= max_gross:
        return "HOLD"
    max_conc = float(risk_cfg.get("max_concentration", 0.4))
    if s == "BUY" and max_conc < 0.01:
        return "HOLD"
    return s if s in ("BUY", "SELL", "HOLD") else "HOLD"


def proposed_position_size(
    signal: str,
    p_up: float,
    risk_cfg: Dict[str, Any],
    atr: float,
    price: float,
    nav: float,
) -> float:
    return size_with_vol_signal(signal, p_up, nav, risk_cfg, atr, price)


def apply_post_decision_risk(
    final_signal: str,
    exposure: ExposureManager,
    risk_cfg: Dict[str, Any],
    *,
    nav: float = 1_000_000.0,
    p_up: float = 0.5,
    atr: float = 0.02,
    price: float = 100.0,
) -> Tuple[str, float]:
    sig = clamp_signal_for_portfolio(final_signal, exposure, risk_cfg, nav=nav)
    qty_usd = proposed_position_size(sig, p_up, risk_cfg, atr, price, nav)
    return sig, qty_usd
