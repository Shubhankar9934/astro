from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pandas as pd


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_trade_date(s: str) -> pd.Timestamp:
    return pd.Timestamp(s)


def bar_timestamp_to_str(ts: Optional[pd.Timestamp]) -> str:
    if ts is None:
        return utc_now_iso()
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.isoformat()
