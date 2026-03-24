"""Execution simulator (fills at close + slippage)."""

from astro.execution.slippage_model import apply_slippage_bps


def fill_price(bar_close: float, side: str, slippage_bps: float) -> float:
    return apply_slippage_bps(bar_close, slippage_bps, side)
