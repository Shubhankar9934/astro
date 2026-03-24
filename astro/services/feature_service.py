from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from astro.features.validation import ValidationReport, validate_fused_frame
from astro.utils.config_loader import AstroConfig


class FeatureService:
    """Single path for loading / validating fused features (backtest, API, live)."""

    def __init__(self, config: AstroConfig, cwd: Optional[Path] = None):
        self.config = config
        self.cwd = cwd or Path.cwd()
        self.data_root = config.data_root_path(self.cwd)

    def fused_path(self, symbol: str) -> Path:
        return self.data_root / "features" / f"{symbol}_fused.parquet"

    def technical_path(self, symbol: str) -> Path:
        return self.data_root / "features" / f"{symbol}_features.parquet"

    def load_fused(self, symbol: str, path: Optional[Path] = None) -> pd.DataFrame:
        p = path or self.fused_path(symbol)
        if not p.exists():
            raise FileNotFoundError(f"Fused features not found: {p}")
        return pd.read_parquet(p)

    def validate_for_schema(
        self, df: pd.DataFrame, schema_id: Optional[str] = None
    ) -> ValidationReport:
        return validate_fused_frame(df, schema_id)

    def latest_feature_row(
        self, symbol: str, path: Optional[Path] = None
    ) -> Dict[str, Any]:
        df = self.load_fused(symbol, path)
        row = df.iloc[-1].to_dict()
        for k, v in list(row.items()):
            if hasattr(v, "isoformat"):
                row[k] = v.isoformat()
        return row

    def latest_model_window(
        self,
        symbol: str,
        feature_columns: list[str],
        seq_len: int,
        path: Optional[Path] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        df = self.load_fused(symbol, path)
        tail = df.iloc[-seq_len:].copy()
        return tail, tail[feature_columns]
