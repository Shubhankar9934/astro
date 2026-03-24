#!/usr/bin/env python3
"""Build synthetic OHLCV → technical → fused parquet under data_root (for local API / dev).

Example:
  python scripts/bootstrap_fused_features.py --symbol SPY
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from astro.ingestion.ibkr.historical_fetch import csv_to_interim_ohlcv, synthetic_ohlcv_csv
from astro.pipelines.fusion_pipeline import fuse_features
from astro.pipelines.market_pipeline import MarketPipeline
from astro.utils.config_loader import load_all_configs


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--symbol", default="SPY", help="Ticker / basename for *_features.parquet and *_fused.parquet")
    p.add_argument("--rows", type=int, default=120, help="Synthetic daily bars (business days)")
    p.add_argument("--seed", type=int, default=42, help="RNG seed for synthetic prices")
    args = p.parse_args()

    cfg = load_all_configs()
    data_root = cfg.data_root_path(ROOT)
    feat_dir = data_root / "features"

    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        raw = tdir / "raw.csv"
        interim = tdir / "interim.csv"
        synthetic_ohlcv_csv(raw, n=args.rows, seed=args.seed)
        csv_to_interim_ohlcv(raw, interim)
        mp = MarketPipeline(feat_dir, schema_version="1")
        tech_out = mp.run(interim, args.symbol)
        fused_out = feat_dir / f"{args.symbol}_fused.parquet"
        fuse_features(
            tech_out,
            fused_out,
            symbol=args.symbol,
            schema_version="1",
            use_market_proxies=True,
        )

    print(f"Wrote {tech_out}")
    print(f"Wrote {fused_out}")


if __name__ == "__main__":
    main()
