#!/usr/bin/env python3
"""Feature-only or signal backtest on fused Parquet."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from astro.backtesting.engine import run_signal_backtest
from astro.backtesting.metrics import max_drawdown, sharpe_ratio
from astro.services.feature_service import FeatureService
from astro.utils.config_loader import load_all_configs


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--fused", type=Path, required=True)
    p.add_argument("--signal-col", default="sentiment_score")
    p.add_argument("--symbol", default="TEST", help="For FeatureService path defaults")
    args = p.parse_args()
    cfg = load_all_configs()
    fs = FeatureService(cfg, cwd=ROOT)
    df = fs.load_fused(args.symbol, path=args.fused)
    rep = fs.validate_for_schema(df)
    if not rep.ok:
        raise SystemExit("Feature schema validation failed: " + "; ".join(rep.errors))
    if args.signal_col not in df.columns:
        df[args.signal_col] = 0.0
    res = run_signal_backtest(df, args.signal_col)
    rets = res.equity_curve.pct_change()
    print("Sharpe:", sharpe_ratio(rets))
    print("MaxDD:", max_drawdown(res.equity_curve))


if __name__ == "__main__":
    main()
