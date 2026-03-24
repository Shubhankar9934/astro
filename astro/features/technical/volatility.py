from __future__ import annotations

import pandas as pd


def realized_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
    return returns.rolling(window).std() * (252**0.5)
