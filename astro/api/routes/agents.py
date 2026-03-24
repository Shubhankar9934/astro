from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from astro.api.dependencies import ROOT, get_config, get_executor
from astro.api.schemas.requests import RiskRequest, SymbolDateRequest
from astro.services.context_builder import build_decision_context

router = APIRouter(prefix="/agents", tags=["agents"])


def _context(symbol: str, trade_date: str):
    cfg = get_config()
    data_root = cfg.data_root_path(ROOT)
    fused = data_root / "features" / f"{symbol}_fused.parquet"
    ckpt = ROOT / "models" / "checkpoints" / "best.pt"
    scaler = ROOT / "models" / "checkpoints" / "scaler.npz"
    return build_decision_context(
        symbol,
        trade_date,
        fused if fused.exists() else None,
        config=cfg,
        schema_id=str(cfg.model.get("schema_id", "fused_v1")),
        checkpoint=ckpt if ckpt.exists() else None,
        scaler_path=scaler if scaler.exists() else None,
        seq_len=int(cfg.model.get("seq_len", 32)),
    )


@router.post("/analysts")
def run_analysts(req: SymbolDateRequest):
    ctx = _context(req.symbol, req.trade_date)
    ex = get_executor()
    reports = ex.run_analysts_only(req.symbol, req.trade_date, ctx)
    return {"symbol": req.symbol, "reports": reports}


@router.post("/research")
def run_research(req: SymbolDateRequest):
    ctx = _context(req.symbol, req.trade_date)
    ex = get_executor()
    out = ex.run_research_only(req.symbol, req.trade_date, ctx)
    return {"symbol": req.symbol, **out}


@router.post("/risk")
def run_risk(body: RiskRequest):
    ex = get_executor()
    try:
        out = ex.run_risk_only(body.model_dump())
    except Exception as e:
        raise HTTPException(400, str(e)) from e
    return out
