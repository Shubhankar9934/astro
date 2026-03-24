from __future__ import annotations

import numpy as np
import pandas as pd


def sharpe_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
    r = returns.dropna()
    if len(r) < 2:
        return 0.0
    return float(np.sqrt(periods_per_year) * r.mean() / (r.std() + 1e-12))


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(dd.min())


def calmar_ratio(equity: pd.Series, periods_per_year: int = 252) -> float:
    mdd = abs(max_drawdown(equity))
    if mdd < 1e-12 or len(equity) < 2:
        return 0.0
    years = (len(equity) - 1) / periods_per_year
    if years < 1e-12:
        return 0.0
    tot = float(equity.iloc[-1] / equity.iloc[0])
    cagr = tot ** (1.0 / years) - 1.0 if tot > 0 else -1.0
    return float(cagr / mdd)


def turnover_from_positions(positions: pd.Series) -> float:
    if len(positions) < 2:
        return 0.0
    return float(positions.diff().abs().mean())


def win_rate_when_long(returns: pd.Series, positions: pd.Series) -> float:
    """Share of bars with positive return while position is long (1)."""
    r = returns.reindex(positions.index).fillna(0.0)
    p = positions.fillna(0.0)
    mask = p.shift(1).fillna(0.0) > 0.5
    sub = r[mask]
    if len(sub) == 0:
        return 0.0
    return float((sub > 0).mean())


def max_consecutive_losses(returns: pd.Series) -> int:
    r = returns.dropna()
    if len(r) == 0:
        return 0
    losses = (r < 0).astype(int)
    streak = mx = 0
    for v in losses:
        if v:
            streak += 1
            mx = max(mx, streak)
        else:
            streak = 0
    return int(mx)
