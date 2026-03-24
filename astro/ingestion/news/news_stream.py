from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd


@dataclass
class NewsItem:
    published_at: datetime
    headline: str
    symbol: Optional[str] = None
    source: str = ""


class NewsStream:
    """Async news queue; bridge IBKR or vendor feeds here."""

    def __init__(self, queue: Optional[asyncio.Queue] = None):
        self.queue = queue or asyncio.Queue(maxsize=2000)

    async def publish(self, item: NewsItem) -> None:
        await self.queue.put(item)

    async def iter_items(self) -> AsyncIterator[NewsItem]:
        while True:
            yield await self.queue.get()


def news_items_to_daily_counts(items: List[NewsItem], dates: pd.Series) -> pd.DataFrame:
    """Aggregate news counts per calendar date for fusion join."""
    df = pd.DataFrame(
        [{"Date": pd.Timestamp(i.published_at).normalize(), "n": 1} for i in items]
    )
    if df.empty:
        return pd.DataFrame({"Date": dates, "news_event_count": 0.0})
    g = df.groupby("Date", as_index=False)["n"].sum().rename(columns={"n": "news_event_count"})
    return g


def append_news_jsonl(path: Path, item: NewsItem) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    import json

    rec = {
        "published_at": item.published_at.isoformat(),
        "headline": item.headline,
        "symbol": item.symbol,
        "source": item.source,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")
