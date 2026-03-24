from __future__ import annotations

import json
from pathlib import Path
from typing import List

from astro.ingestion.news.news_stream import NewsItem


def parse_news_jsonl(path: Path) -> List[NewsItem]:
    out: List[NewsItem] = []
    if not path.exists():
        return out
    from datetime import datetime

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out.append(
                NewsItem(
                    published_at=datetime.fromisoformat(d["published_at"]),
                    headline=d.get("headline", ""),
                    symbol=d.get("symbol"),
                    source=d.get("source", ""),
                )
            )
    return out
