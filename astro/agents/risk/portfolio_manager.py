"""Portfolio-level constraints (reads configs/risk.yaml via executor)."""


def clip_notional(desired: float, max_fraction: float, nav: float) -> float:
    cap = max_fraction * nav
    return min(desired, cap)
