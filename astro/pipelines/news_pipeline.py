from __future__ import annotations

"""News pipeline contract: fused features must use aggregates only (daily counts, rolling stats).

Do not persist raw headline arrays in model-facing Parquet; keep raw text in JSONL sidecars
for optional UI / analyst digests only.
"""

from pathlib import Path

import pandas as pd

from astro.ingestion.news.news_parser import parse_news_jsonl
from astro.ingestion.news.news_stream import news_items_to_daily_counts


def build_news_counts_parquet(jsonl_path: Path, feature_dates: pd.Series, out: Path) -> Path:
    items = parse_news_jsonl(jsonl_path)
    g = news_items_to_daily_counts(items, feature_dates)
    full = pd.DataFrame({"Date": pd.to_datetime(feature_dates).dt.normalize()})
    full = full.merge(g, on="Date", how="left")
    full["news_event_count"] = full["news_event_count"].fillna(0.0)
    out.parent.mkdir(parents=True, exist_ok=True)
    full.to_parquet(out, index=False)
    return out
