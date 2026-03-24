from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from astro.backtesting.metrics import (
    calmar_ratio,
    max_consecutive_losses,
    max_drawdown,
    sharpe_ratio,
    turnover_from_positions,
    win_rate_when_long,
)
from astro.decision_engine.policy import apply_model_governance_detailed
from astro.models.transformer.inference import TransformerInference, load_inference_optional


def _equity_long_only(df: pd.DataFrame, ret_col: str, long_indicator: List[float]) -> pd.Series:
    """long_indicator[i] = 1 if long entering bar i+1 (same convention as signal backtest)."""
    eq = [100_000.0]
    for i in range(1, len(df)):
        r = df[ret_col].iloc[i]
        if pd.isna(r):
            r = 0.0
        pos = float(long_indicator[i - 1]) if i - 1 < len(long_indicator) else 0.0
        pos = 1.0 if pos > 0.5 else 0.0
        eq.append(eq[-1] * (1 + pos * r))
    return pd.Series(eq, index=df.index[: len(eq)])


def _metrics_bundle(equity: pd.Series, positions: pd.Series, rets: pd.Series) -> Dict[str, float]:
    er = equity.pct_change()
    return {
        "sharpe": sharpe_ratio(er),
        "max_drawdown": max_drawdown(equity),
        "calmar": calmar_ratio(equity),
        "turnover": turnover_from_positions(positions),
        "win_rate_long": win_rate_when_long(rets, positions),
        "max_consecutive_losses": float(max_consecutive_losses(rets)),
    }


def run_model_governance_series(
    df: pd.DataFrame,
    inf: TransformerInference,
    seq_len: int,
    gov_cfg: Dict[str, Any],
    *,
    synthetic_llm_signal: str = "HOLD",
) -> List[float]:
    cols = list(inf.feature_columns)
    d = df.copy()
    for c in cols:
        if c not in d.columns:
            d[c] = 0.0
    n = len(d)
    out: List[float] = [0.0] * n
    for i in range(seq_len, n):
        tail = d.iloc[i - seq_len : i][cols].to_numpy(dtype=np.float64)
        pred = inf.predict_window(tail)
        sig, _ = apply_model_governance_detailed(synthetic_llm_signal, pred, gov_cfg)
        out[i - 1] = 1.0 if sig == "BUY" else 0.0
    return out


def run_evaluation_report(
    fused_parquet: Path,
    checkpoint: Path,
    scaler: Path,
    *,
    seq_len: int = 32,
    gov_cfg: Optional[Dict[str, Any]] = None,
    signal_col: str = "sentiment_proxy_momentum",
    ret_col: str = "ret_1",
    out_dir: Optional[Path] = None,
    cwd: Optional[Path] = None,
) -> Dict[str, Any]:
    """Compare model+governance long-only path vs baselines; write JSON report if out_dir set."""
    gov_cfg = dict(gov_cfg or {})
    df = pd.read_parquet(fused_parquet)
    if ret_col not in df.columns:
        raise ValueError(f"DataFrame missing return column {ret_col!r}")
    inf = load_inference_optional(checkpoint, scaler)
    if inf is None:
        raise FileNotFoundError("checkpoint or scaler missing")

    n = len(df)
    pos_model = pd.Series(run_model_governance_series(df, inf, seq_len, gov_cfg), index=df.index, dtype=float)
    eq_m = _equity_long_only(df, ret_col, pos_model.tolist())
    rets = pd.to_numeric(df[ret_col], errors="coerce").fillna(0.0)

    pos_bh = pd.Series(1.0, index=df.index)
    eq_bh = _equity_long_only(df, ret_col, [1.0] * (len(df) - 1))
    pos_flat = pd.Series(0.0, index=df.index)
    eq_flat = _equity_long_only(df, ret_col, [0.0] * (len(df) - 1))

    if signal_col in df.columns:
        sc = pd.to_numeric(df[signal_col], errors="coerce").fillna(0.0)
        sig_long = (sc > 0).astype(float).tolist()[: max(0, len(df) - 1)]
        while len(sig_long) < len(df) - 1:
            sig_long.append(0.0)
        eq_sig = _equity_long_only(df, ret_col, sig_long)
        pos_sig = (sc.shift(1).fillna(0.0) > 0).astype(float)
    else:
        eq_sig = eq_flat
        pos_sig = pos_flat

    results = {
        "model_governance": _metrics_bundle(eq_m, pos_model, rets),
        "buy_hold": _metrics_bundle(eq_bh, pos_bh, rets),
        "always_flat": _metrics_bundle(eq_flat, pos_flat, rets),
        "signal_column": _metrics_bundle(eq_sig, pos_sig, rets),
    }

    ckpt_sha = ""
    if checkpoint.exists():
        h = hashlib.sha256()
        h.update(checkpoint.read_bytes())
        ckpt_sha = h.hexdigest()[:16]

    git_sha = ""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd or Path.cwd(),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0:
            git_sha = r.stdout.strip()[:12]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    report = {
        "fused_parquet": str(fused_parquet.resolve()),
        "checkpoint": str(checkpoint.resolve()),
        "checkpoint_sha256_prefix": ckpt_sha,
        "schema_id": inf.schema_id,
        "git_rev": git_sha,
        "seq_len": seq_len,
        "rows": n,
        "baselines": results,
    }

    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        outp = out_dir / f"eval_{checkpoint.stem}_{ckpt_sha}.json"
        with open(outp, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        report["report_path"] = str(outp)

    return report
