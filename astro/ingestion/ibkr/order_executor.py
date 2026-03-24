from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional

from astro.ingestion.ibkr.client import IBKRClient


@dataclass
class OrderRequest:
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: float
    order_type: Literal["MKT", "LMT"] = "MKT"
    limit_price: Optional[float] = None


class OrderExecutor:
    """Thin IBKR order placement."""

    def __init__(self, client: IBKRClient):
        self.client = client

    def place(self, req: OrderRequest) -> Any:
        from ib_async import LimitOrder, MarketOrder, Stock  # type: ignore

        ib = self.client.connect()
        contract = Stock(req.symbol, "SMART", "USD")
        ib.qualifyContracts(contract)
        if req.order_type == "MKT":
            order = MarketOrder(req.side, req.quantity)
        else:
            if req.limit_price is None:
                raise ValueError("limit_price required for LMT")
            order = LimitOrder(req.side, req.quantity, req.limit_price)
        trade = ib.placeOrder(contract, order)
        return trade
