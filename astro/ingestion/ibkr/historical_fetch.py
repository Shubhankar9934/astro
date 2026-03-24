from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from astro.ingestion.ibkr.client import IBKRClient


def fetch_historical_to_csv(
    client: IBKRClient,
    symbol: str,
    end_datetime: str,
    duration: str = "1 Y",
    bar_size: str = "1 day",
    what_to_show: str = "TRADES",
    use_rth: bool = True,
    out_path: Optional[Path] = None,
) -> Path:
    """Request historical bars from IBKR and write CSV to raw/market.

    duration: IBKR duration string e.g. '1 Y', '60 D'
    bar_size: '1 day', '1 hour', '5 mins', etc.
    """
    from ib_async import Stock  # type: ignore

    ib = client.connect()
    contract = Stock(symbol, "SMART", "USD")
    ib.qualifyContracts(contract)
    bars = ib.reqHistoricalData(
        contract,
        endDateTime=end_datetime,
        durationStr=duration,
        barSizeSetting=bar_size,
        whatToShow=what_to_show,
        useRTH=use_rth,
        formatDate=1,
    )
    if not bars:
        raise RuntimeError(f"No historical bars returned for {symbol}")
    rows: List[Dict[str, Any]] = []
    for b in bars:
        rows.append(
            {
                "Date": pd.Timestamp(b.date),
                "Open": b.open,
                "High": b.high,
                "Low": b.low,
                "Close": b.close,
                "Volume": b.volume,
            }
        )
    df = pd.DataFrame(rows)
    if out_path is None:
        raise ValueError("out_path required")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path


def csv_to_interim_ohlcv(raw_csv: Path, interim_csv: Path) -> Path:
    """Normalize raw IBKR/yfinance-style CSV to interim schema."""
    df = pd.read_csv(raw_csv)
    colmap = {c.lower(): c for c in df.columns}
    date_col = colmap.get("date") or "Date"
    if date_col not in df.columns:
        raise ValueError(f"No date column in {raw_csv}")
    df = df.rename(columns={date_col: "Date"})
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    for c in ["Open", "High", "Low", "Close", "Volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Close"])
    interim_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(interim_csv, index=False)
    return interim_csv


def synthetic_ohlcv_csv(path: Path, n: int = 120, seed: int = 42) -> Path:
    """Write deterministic synthetic OHLCV for tests/offline dev."""
    rng = __import__("numpy").random.default_rng(seed)
    close = 100 + rng.standard_normal(n).cumsum() * 0.5
    path.parent.mkdir(parents=True, exist_ok=True)
    idx = pd.date_range("2020-01-02", periods=n, freq="B")
    df = pd.DataFrame(
        {
            "Date": idx,
            "Open": close + rng.standard_normal(n) * 0.2,
            "High": close + abs(rng.standard_normal(n) * 0.5),
            "Low": close - abs(rng.standard_normal(n) * 0.5),
            "Close": close,
            "Volume": rng.integers(1_000_000, 5_000_000, n),
        }
    )
    df.to_csv(path, index=False)
    return path
