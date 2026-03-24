from __future__ import annotations

from typing import Optional

from astro.storage.database import MetadataDB


class ExposureManager:
    """Tracks book notionals via MetadataDB positions table."""

    def __init__(self, db: Optional[MetadataDB] = None):
        self.db = db

    def gross_notional(self) -> float:
        if self.db is None:
            return 0.0
        return self.db.gross_notional()

    def notional_fraction(self, nav: float) -> float:
        if nav <= 0:
            return 0.0
        return self.gross_notional() / nav

    def set_position(self, symbol: str, qty: float, avg_price: float) -> None:
        if self.db:
            self.db.set_position(symbol, qty, avg_price)
