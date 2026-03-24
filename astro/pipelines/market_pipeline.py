from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from astro.features.technical.indicators import ohlcv_to_feature_table


def write_feature_manifest(
    path: Path,
    *,
    schema_version: str,
    symbol: str,
    bar_range: str,
    config_hashes: Optional[Dict[str, str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Path:
    payload = {
        "feature_schema_version": schema_version,
        "symbol": symbol,
        "bar_range": bar_range,
        "config_hashes": config_hashes or {},
        "extra": extra or {},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    return path


def _file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


class MarketPipeline:
    """OHLCV (interim) → technical features → Parquet."""

    def __init__(self, features_dir: Path, schema_version: str = "1"):
        self.features_dir = features_dir
        self.schema_version = schema_version

    def run(self, interim_csv: Path, symbol: str) -> Path:
        df = pd.read_csv(interim_csv)
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        feat = ohlcv_to_feature_table(df)
        if "Date" not in feat.columns and "Date" in df.columns:
            n = min(len(feat), len(df))
            feat = feat.iloc[:n].copy()
            feat.insert(0, "Date", df["Date"].values[:n])
        out = self.features_dir / f"{symbol}_features.parquet"
        self.features_dir.mkdir(parents=True, exist_ok=True)
        feat.to_parquet(out, index=False)
        br = ""
        if "Date" in feat.columns and len(feat):
            br = f"{feat['Date'].min()}..{feat['Date'].max()}"
        write_feature_manifest(
            out.with_suffix(".manifest.json"),
            schema_version=self.schema_version,
            symbol=symbol,
            bar_range=br,
            config_hashes={"interim_csv": _file_sha256(interim_csv)},
            extra={"rows": len(feat)},
        )
        return out
