"""Position sizing from signal confidence and volatility."""


def size_from_p_up(p_up: float, nav: float, risk_budget: float) -> float:
    edge = abs(p_up - 0.5)
    return nav * risk_budget * (edge / 0.5)


def size_with_vol_signal(
    signal: str,
    p_up: float,
    nav: float,
    risk_cfg: dict,
    atr: float,
    price: float,
) -> float:
    if signal.upper() != "BUY":
        return 0.0
    max_frac = float(risk_cfg.get("max_position_fraction", 0.25))
    base = nav * max_frac
    vol_ratio = (atr / price) if price else 0.02
    vol_scale = min(1.0, 0.02 / max(vol_ratio, 1e-8))
    edge = abs(p_up - 0.5) * 2.0
    return base * vol_scale * edge
