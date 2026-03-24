from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

import pandas as pd

from astro.ingestion.ibkr.client import IBKRClient


@dataclass
class BarEvent:
    symbol: str
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketStream:
    """Real-time bars: pushes BarEvent into an asyncio.Queue."""

    def __init__(self, client: IBKRClient, queue: Optional[asyncio.Queue] = None):
        self.client = client
        self.queue = queue or asyncio.Queue(maxsize=500)
        self._handlers: List[Callable[[BarEvent], None]] = []

    def on_bar(self, fn: Callable[[BarEvent], None]) -> None:
        self._handlers.append(fn)

    async def emit(self, bar: BarEvent) -> None:
        for fn in self._handlers:
            fn(bar)
        await self.queue.put(bar)

    def subscribe_ibkr_bars(
        self,
        symbol: str,
        bar_size_seconds: int = 5,
        what_to_show: str = "TRADES",
        use_rth: bool = True,
    ) -> Any:
        """Subscribe to 5s (default) real-time bars via ib_async. Returns RealTimeBarList."""
        from ib_async import Stock  # type: ignore

        ib = self.client.connect()
        contract = Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(contract)
        bars = ib.reqRealTimeBars(contract, bar_size_seconds, what_to_show, use_rth)

        def on_update(bars_list, has_new_bar):
            if not has_new_bar or not bars_list:
                return
            b = bars_list[-1]
            ev = BarEvent(
                symbol=symbol,
                timestamp=pd.Timestamp(b.time, unit="s", tz="UTC"),
                open=b.open_,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=float(b.volume),
            )
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.emit(ev))
            except RuntimeError:
                for fn in self._handlers:
                    fn(ev)

        bars.updateEvent += on_update
        return bars


def append_bar_to_parquet(bar: BarEvent, path: Path) -> None:
    row = pd.DataFrame(
        [
            {
                "Date": bar.timestamp,
                "Open": bar.open,
                "High": bar.high,
                "Low": bar.low,
                "Close": bar.close,
                "Volume": bar.volume,
            }
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = pd.read_parquet(path)
        pd.concat([old, row], ignore_index=True).to_parquet(path, index=False)
    else:
        row.to_parquet(path, index=False)
