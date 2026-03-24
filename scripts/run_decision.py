#!/usr/bin/env python3
"""Run full Astro decision pipeline once (requires LLM API keys)."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from astro.decision_engine.executor import DecisionExecutor
from astro.decision_engine.governance_mode import (
    model_missing_would_violate_governance,
    resolve_governance_mode,
)
from astro.services.context_builder import build_decision_context
from astro.storage.database import MetadataDB
from astro.utils.config_loader import load_all_configs
from astro.utils.logger import setup_logging


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--symbol", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--fused", type=Path, default=None)
    p.add_argument("--checkpoint", type=Path, default=None)
    p.add_argument("--scaler", type=Path, default=None)
    p.add_argument("--mode", choices=["fast", "full"], default=None)
    args = p.parse_args()
    cfg = load_all_configs()
    setup_logging(cfg.system.get("log_level", "INFO"))
    data_root = cfg.data_root_path(ROOT)
    fused = args.fused or (data_root / "features" / f"{args.symbol}_fused.parquet")
    ckpt = args.checkpoint or (ROOT / "models" / "checkpoints" / "best.pt")
    scaler = args.scaler or (ROOT / "models" / "checkpoints" / "scaler.npz")
    ctx = build_decision_context(
        args.symbol,
        args.date,
        fused if fused.exists() else None,
        config=cfg,
        feature_version=str(cfg.system.get("feature_schema_version", "1")),
        schema_id=str(cfg.model.get("schema_id", "fused_v1")),
        checkpoint=ckpt if ckpt.exists() else None,
        scaler_path=scaler if scaler.exists() else None,
        seq_len=int(cfg.model.get("seq_len", 32)),
        risk=dict(cfg.risk),
    )
    gov_cfg = dict(cfg.agents.get("model_governance", {}))
    if resolve_governance_mode(cfg.agents) == "strict" and model_missing_would_violate_governance(
        ctx.model, gov_cfg
    ):
        print(
            "ERROR: model required by model_governance but no prediction was produced.",
            ctx.extra.get("model_predict_error") or "",
            file=sys.stderr,
        )
        raise SystemExit(2)
    ex = DecisionExecutor.from_config(cfg, log_dir=data_root / "cache" / "decision_logs")
    mode = args.mode
    state, sig, run_meta = (
        ex.run(args.symbol, args.date, ctx, mode=mode)
        if mode
        else ex.run(args.symbol, args.date, ctx)
    )
    db = MetadataDB(data_root / "cache" / "astro_meta.sqlite")
    db.insert_decision(args.symbol, args.date, sig, {"final": state.final_trade_decision[:500]})
    db.close()
    print("Signal:", sig)
    print("Suggested size USD:", run_meta.get("suggested_size_usd"))
    print("Governance:", run_meta.get("governance"))


if __name__ == "__main__":
    main()
