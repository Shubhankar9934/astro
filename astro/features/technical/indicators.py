from __future__ import annotations

import pandas as pd
from stockstats import wrap


def _clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "Date" in out.columns:
        out["Date"] = pd.to_datetime(out["Date"], errors="coerce")
    out = out.dropna(subset=["Date"])
    for c in ["Open", "High", "Low", "Close", "Volume"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.dropna(subset=["Close"])
    cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in out.columns]
    out[cols] = out[cols].ffill().bfill()
    return out


def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add returns, RSI, MACD, Bollinger (via stockstats) to OHLCV DataFrame."""
    data = _clean_ohlcv(df)
    data = data.rename(
        columns={
            k: v
            for k, v in {
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
                "Date": "date",
            }.items()
            if k in data.columns
        }
    )
    wrapped = wrap(data.copy())
    for col in ["rsi_14", "macd", "macds", "macdh", "boll", "boll_ub", "boll_lb", "atr"]:
        try:
            _ = wrapped[col]
        except Exception:
            pass
    wrapped["ret_1"] = wrapped["close"].pct_change()
    out = wrapped.copy()
    out["ret_1"] = out["ret_1"].fillna(0.0)
    if "date" in out.columns:
        out["Date"] = pd.to_datetime(out["date"], errors="coerce")
    return out


def ohlcv_to_feature_table(df: pd.DataFrame) -> pd.DataFrame:
    """Feature table with Date column for Parquet."""
    feat = add_technical_features(df)
    if "Date" not in feat.columns and "date" in feat.columns:
        feat["Date"] = pd.to_datetime(feat["date"], errors="coerce")
    return feat
