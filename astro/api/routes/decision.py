from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

from astro.api.dependencies import ROOT, get_config, get_executor
from astro.api.schemas.requests import DecisionRequest
from astro.decision_engine.governance_mode import (
    model_missing_would_violate_governance,
    resolve_governance_mode,
)
from astro.services.context_builder import build_decision_context
from astro.storage.database import MetadataDB

router = APIRouter(prefix="/decision", tags=["decision"])


def _positions_stale(max_updated: str | None, warn_minutes: float) -> bool:
    if not max_updated or warn_minutes <= 0:
        return False
    try:
        dt = datetime.fromisoformat(max_updated.replace("Z", "+00:00"))
    except ValueError:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    age_m = (datetime.now(timezone.utc) - dt).total_seconds() / 60.0
    return age_m > warn_minutes


@router.post("/run")
def run_decision(req: DecisionRequest):
    cfg = get_config()
    ex = get_executor()
    data_root = cfg.data_root_path(ROOT)
    fused = data_root / "features" / f"{req.symbol}_fused.parquet"
    ckpt = ROOT / "models" / "checkpoints" / "best.pt"
    scaler = ROOT / "models" / "checkpoints" / "scaler.npz"
    ctx = build_decision_context(
        req.symbol,
        req.trade_date,
        fused if fused.exists() else None,
        config=cfg,
        schema_id=str(cfg.model.get("schema_id", "fused_v1")),
        checkpoint=ckpt if ckpt.exists() else None,
        scaler_path=scaler if scaler.exists() else None,
        seq_len=int(cfg.model.get("seq_len", 32)),
        risk=dict(cfg.risk),
    )
    db_path_early = data_root / "cache" / "astro_meta.sqlite"
    if db_path_early.exists():
        db0 = MetadataDB(db_path_early)
        try:
            mx = db0.positions_max_updated_at()
            ctx.extra["positions_max_updated_at"] = mx
            wm = float(cfg.risk.get("positions_stale_warn_minutes", 0) or 0)
            ctx.extra["portfolio_state_stale"] = _positions_stale(mx, wm)
        finally:
            db0.close()
    if ctx.extra.get("schema_validation_errors"):
        pass  # allow run; errors visible in response
    gov_cfg = dict(cfg.agents.get("model_governance", {}))
    gov_mode = resolve_governance_mode(cfg.agents)
    strict_violation = model_missing_would_violate_governance(ctx.model, gov_cfg)
    if gov_mode == "strict" and strict_violation:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "model_required",
                "message": "Model inference is required by model_governance but no prediction was produced.",
                "model_predict_error": ctx.extra.get("model_predict_error"),
                "governance_mode": gov_mode,
                "hint": "Ensure models/checkpoints/best.pt and scaler.npz exist and fused features match the trained schema. Or set governance_mode: degraded|dev or ASTRO_GOVERNANCE_MODE.",
            },
        )
    degraded = gov_mode == "degraded" and strict_violation
    degraded_reason = (
        "model_required_but_missing" if degraded else None
    )
    state, sig, run_meta = ex.run(req.symbol, req.trade_date, ctx, mode=req.mode)
    db_path = data_root / "cache" / "astro_meta.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = MetadataDB(db_path)
    did = db.insert_decision(
        req.symbol,
        req.trade_date,
        sig,
        {"mode": req.mode, "final_snippet": state.final_trade_decision[:500]},
    )
    db.close()
    return {
        "decision_id": did,
        "symbol": req.symbol,
        "decision": sig,
        "governance_mode": gov_mode,
        "degraded": degraded,
        "degraded_reason": degraded_reason,
        "dev_model_bypass": gov_mode == "dev" and strict_violation,
        "governance": run_meta.get("governance"),
        "suggested_size_usd": run_meta.get("suggested_size_usd"),
        "sizing": run_meta.get("sizing"),
        "model_output": (
            {
                "p_up": ctx.model.p_up,
                "uncertainty": ctx.model.uncertainty,
                "degenerate": bool(ctx.extra.get("model_degenerate")),
            }
            if ctx.model
            else None
        ),
        "model_predict_error": ctx.extra.get("model_predict_error"),
        "analyst_summary": {
            "technical": state.market_report[:2000],
            "sentiment": state.sentiment_report[:2000],
            "news": state.news_report[:2000],
            "fundamentals": state.fundamentals_report[:2000],
            "macro": state.macro_report[:2000],
        },
        "structured_market_facts": ctx.extra.get("structured_market_facts"),
        "research_summary": state.investment_plan[:4000],
        "risk_summary": state.final_trade_decision[:4000],
        "schema_validation": {
            "ok": ctx.extra.get("schema_validation_ok"),
            "errors": ctx.extra.get("schema_validation_errors"),
        },
        "positions_max_updated_at": ctx.extra.get("positions_max_updated_at"),
        "portfolio_state_stale": bool(ctx.extra.get("portfolio_state_stale")),
    }
