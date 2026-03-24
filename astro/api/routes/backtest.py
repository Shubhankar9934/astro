from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from astro.api.dependencies import ROOT, get_config
from astro.api.schemas.requests import BacktestRequest
from astro.backtesting.engine import run_signal_backtest
from astro.backtesting.metrics import max_drawdown, sharpe_ratio
from astro.services.feature_service import FeatureService

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("/run")
def run_backtest(req: BacktestRequest):
    cfg = get_config()
    fs = FeatureService(cfg, cwd=ROOT)
    p = Path(req.fused_path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        df = fs.load_fused(req.symbol, path=p)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
    rep = fs.validate_for_schema(df)
    if not rep.ok:
        raise HTTPException(400, "; ".join(rep.errors))
    if req.signal_col not in df.columns:
        df[req.signal_col] = 0.0
    res = run_signal_backtest(df, req.signal_col)
    rets = res.equity_curve.pct_change()
    return {
        "sharpe": sharpe_ratio(rets),
        "max_drawdown": max_drawdown(res.equity_curve),
        "n_trades": len(res.trades),
    }
