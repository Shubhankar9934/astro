from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Literal, Optional

from astro.execution.trade_executor import TradeExecutor

Side = Literal["BUY", "SELL"]


class OrderManager:
    """Idempotent order submission via SQLite-backed keys."""

    def __init__(self, executor: TradeExecutor, db_path: Path):
        self.executor = executor
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS sent (idempotency_key TEXT PRIMARY KEY, status TEXT)"
        )
        self._conn.commit()

    def submit_market(
        self,
        idempotency_key: str,
        symbol: str,
        side: Side,
        qty: float,
    ) -> Optional[Any]:
        cur = self._conn.execute(
            "SELECT status FROM sent WHERE idempotency_key=?", (idempotency_key,)
        )
        if cur.fetchone():
            return None
        if side == "BUY":
            trade = self.executor.market_buy(symbol, qty)
        else:
            trade = self.executor.market_sell(symbol, qty)
        self._conn.execute(
            "INSERT INTO sent (idempotency_key, status) VALUES (?, ?)",
            (idempotency_key, "submitted"),
        )
        self._conn.commit()
        return trade
