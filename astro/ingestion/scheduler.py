from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Optional

from astro.ingestion.ibkr.client import IBKRClient, IBKRConnectionConfig
from astro.ingestion.ibkr.market_stream import BarEvent, MarketStream
from astro.utils.logger import get_logger

LOG = get_logger("astro.scheduler")

OnBar = Callable[[BarEvent], Awaitable[None]]


class IngestionScheduler:
    """Async supervisor: IBKR stream + optional bar handlers (features, decisions)."""

    def __init__(
        self,
        ibkr: IBKRClient,
        market: MarketStream,
        on_bar: Optional[OnBar] = None,
    ):
        self.ibkr = ibkr
        self.market = market
        self.on_bar = on_bar

    async def run_stream_loop(self, symbol: str) -> None:
        self.market.subscribe_ibkr_bars(symbol)

        async def drain():
            while True:
                bar = await self.market.queue.get()
                if self.on_bar:
                    await self.on_bar(bar)

        await drain()

    async def run_periodic(self, coro_factory: Callable[[], Awaitable[None]], seconds: float):
        while True:
            await coro_factory()
            await asyncio.sleep(seconds)


def default_scheduler(
    cfg: dict, symbol: str, on_bar: Optional[OnBar] = None
) -> IngestionScheduler:
    ic = IBKRConnectionConfig.from_dict(cfg)
    client = IBKRClient(ic)
    return IngestionScheduler(client, MarketStream(), on_bar=on_bar)
