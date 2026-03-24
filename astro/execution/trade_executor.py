from __future__ import annotations

from typing import Any

from astro.ingestion.ibkr.client import IBKRClient
from astro.ingestion.ibkr.order_executor import OrderExecutor, OrderRequest


class TradeExecutor:
    """Live execution wrapper around IBKR."""

    def __init__(self, client: IBKRClient):
        self._inner = OrderExecutor(client)

    def market_buy(self, symbol: str, qty: float) -> Any:
        return self._inner.place(OrderRequest(symbol=symbol, side="BUY", quantity=qty))

    def market_sell(self, symbol: str, qty: float) -> Any:
        return self._inner.place(OrderRequest(symbol=symbol, side="SELL", quantity=qty))
