from __future__ import annotations


def apply_slippage_bps(price: float, bps: float, side: str) -> float:
    adj = bps / 10000.0 * price
    if side.upper() == "BUY":
        return price + adj
    return price - adj
