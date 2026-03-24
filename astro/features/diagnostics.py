from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


def correlation_report(
    df: pd.DataFrame,
    feature_cols: List[str],
    *,
    max_corr: float = 0.95,
) -> Dict[str, Any]:
    """Pairwise absolute correlation on numeric columns; flag pairs above max_corr."""
    cols = [c for c in feature_cols if c in df.columns]
    if len(cols) < 2:
        return {"ok": True, "pairs": [], "n_features": len(cols)}
    sub = df[cols].apply(pd.to_numeric, errors="coerce").dropna(how="all")
    if len(sub) < 5:
        return {"ok": True, "pairs": [], "n_features": len(cols), "warning": "too_few_rows"}
    cmat = sub.corr().abs()
    pairs: List[Tuple[str, str, float]] = []
    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            v = cmat.loc[a, b] if a in cmat.index and b in cmat.columns else np.nan
            if pd.notna(v) and float(v) >= max_corr:
                pairs.append((a, b, float(v)))
    return {
        "ok": len(pairs) == 0,
        "pairs": [{"a": a, "b": b, "corr": v} for a, b, v in pairs],
        "n_features": len(cols),
        "max_corr_threshold": max_corr,
    }
