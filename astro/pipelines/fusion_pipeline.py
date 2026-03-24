from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from astro.features.validation import get_schema, load_schema_registry
from astro.pipelines.market_pipeline import write_feature_manifest


def _apply_market_proxies(tech: pd.DataFrame) -> pd.DataFrame:
    """When no real news/sentiment feeds are joined, add explicit proxy columns (not social/news).

    - ``sentiment_proxy_momentum``: rolling mean of sign(returns); price momentum only.
    - ``news_intensity_proxy``: binary vol/ATR spike flag; not headline counts.

    ``sentiment_score`` / ``news_event_count`` stay for real pipeline merges only (typically 0).
    """
    out = tech.copy()
    close = None
    for c in ("close", "Close"):
        if c in out.columns:
            close = pd.to_numeric(out[c], errors="coerce")
            break
    if close is None or close.notna().sum() < 2:
        out["sentiment_proxy_momentum"] = 0.0
        out["news_intensity_proxy"] = 0.0
        return out
    ret = close.pct_change()
    sign_mean = np.sign(ret).rolling(5, min_periods=1).mean()
    out["sentiment_proxy_momentum"] = sign_mean.fillna(0.0).clip(-1.0, 1.0)
    if "atr" in out.columns:
        atr = pd.to_numeric(out["atr"], errors="coerce").fillna(0.0)
        med = atr.rolling(20, min_periods=1).median()
        out["news_intensity_proxy"] = (atr > med * 1.2).astype(float)
    else:
        vol = ret.abs().rolling(10, min_periods=1).mean()
        med_v = vol.rolling(20, min_periods=1).median()
        out["news_intensity_proxy"] = (vol > med_v * 1.2).astype(float)
    return out


def fuse_features(
    technical_parquet: Path,
    out_path: Path,
    *,
    symbol: str,
    schema_version: str,
    schema_id: str = "fused_v1",
    news_counts: Optional[pd.DataFrame] = None,
    sentiment_series: Optional[pd.DataFrame] = None,
    use_market_proxies: bool = False,
) -> Path:
    """Join technical features with optional news/sentiment columns on Date."""
    tech = pd.read_parquet(technical_parquet)
    if "Date" not in tech.columns and "date" in tech.columns:
        tech = tech.rename(columns={"date": "Date"})
    if "Date" not in tech.columns:
        raise ValueError("technical parquet must have Date column")
    tech = tech.copy()
    if "news_event_count" not in tech.columns:
        tech["news_event_count"] = 0.0
    if "sentiment_score" not in tech.columns:
        tech["sentiment_score"] = 0.0
    if news_counts is not None and len(news_counts):
        tech = tech.drop(columns=["news_event_count"], errors="ignore")
        tech = tech.merge(news_counts, on="Date", how="left")
        tech["news_event_count"] = tech["news_event_count"].fillna(0.0)
    if sentiment_series is not None and len(sentiment_series):
        tech = tech.drop(columns=["sentiment_score"], errors="ignore")
        tech = tech.merge(sentiment_series, on="Date", how="left")
        tech["sentiment_score"] = tech["sentiment_score"].fillna(0.0)
    if use_market_proxies and news_counts is None and sentiment_series is None:
        tech = _apply_market_proxies(tech)
    for _proxy_col in ("sentiment_proxy_momentum", "news_intensity_proxy"):
        if _proxy_col not in tech.columns:
            tech[_proxy_col] = 0.0
    reg = load_schema_registry()
    sch = get_schema(reg, schema_id)
    lower = {str(c).lower(): c for c in tech.columns}
    for col in sch.get("required_columns", []):
        if str(col).lower() == "date":
            continue
        if str(col).lower() not in lower:
            tech[col] = 0.0
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tech.to_parquet(out_path, index=False)
    br = f"{tech['Date'].min()}..{tech['Date'].max()}" if len(tech) else ""
    write_feature_manifest(
        out_path.with_suffix(".manifest.json"),
        schema_version=schema_version,
        symbol=symbol,
        bar_range=br,
        extra={
            "fused": True,
            "rows": len(tech),
            "schema_id": schema_id,
            "use_market_proxies": use_market_proxies,
        },
    )
    return out_path
