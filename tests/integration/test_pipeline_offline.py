from pathlib import Path

import pandas as pd

from astro.ingestion.ibkr.historical_fetch import csv_to_interim_ohlcv, synthetic_ohlcv_csv
from astro.pipelines.fusion_pipeline import fuse_features
from astro.pipelines.market_pipeline import MarketPipeline


def test_synthetic_to_fused(tmp_path: Path):
    raw = tmp_path / "raw.csv"
    synthetic_ohlcv_csv(raw, n=80)
    interim = tmp_path / "interim.csv"
    csv_to_interim_ohlcv(raw, interim)
    feat_dir = tmp_path / "features"
    mp = MarketPipeline(feat_dir, schema_version="1")
    tech_out = mp.run(interim, "TEST")
    fused = fuse_features(tech_out, tmp_path / "TEST_fused.parquet", symbol="TEST", schema_version="1")
    df = pd.read_parquet(fused)
    assert len(df) >= 50
    assert "close" in df.columns or "Close" in df.columns
