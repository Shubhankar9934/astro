from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: List[dict]


def run_signal_backtest(
    features: pd.DataFrame,
    signal_col: str,
    ret_col: str = "ret_1",
    initial: float = 100_000.0,
) -> BacktestResult:
    """Simple long-only: hold when signal>0."""
    eq = [initial]
    trades = []
    pos = 0.0
    for i in range(1, len(features)):
        sig = features[signal_col].iloc[i - 1]
        r = features[ret_col].iloc[i]
        if pd.isna(r):
            r = 0.0
        if sig > 0 and pos == 0:
            pos = 1.0
            trades.append({"i": i, "action": "ENTER"})
        elif sig <= 0 and pos > 0:
            pos = 0.0
            trades.append({"i": i, "action": "EXIT"})
        eq.append(eq[-1] * (1 + pos * r))
    return BacktestResult(
        equity_curve=pd.Series(eq, index=range(len(eq))),
        trades=trades,
    )
