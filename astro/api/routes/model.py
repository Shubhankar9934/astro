from __future__ import annotations

import math
from pathlib import Path

from fastapi import APIRouter, HTTPException

from astro.api.dependencies import ROOT, get_config, get_feature_service
from astro.api.schemas.requests import PredictRequest
from astro.models.transformer.inference import load_inference_optional

router = APIRouter(prefix="/model", tags=["model"])


@router.post("/predict")
def predict(req: PredictRequest):
    cfg = get_config()
    fs = get_feature_service()
    fused = fs.fused_path(req.symbol)
    if not fused.exists():
        raise HTTPException(404, "Fused features not found")
    ckpt = ROOT / "models" / "checkpoints" / "best.pt"
    scaler = ROOT / "models" / "checkpoints" / "scaler.npz"
    inf = load_inference_optional(ckpt, scaler)
    if inf is None:
        raise HTTPException(503, "Model checkpoint or scaler missing")
    seq_len = int(cfg.model.get("seq_len", 32))
    pred = inf.predict_latest_from_parquet(fused, seq_len)
    p_up = pred.p_up if math.isfinite(pred.p_up) else 0.5
    unc = pred.uncertainty if math.isfinite(pred.uncertainty) else 1.0
    degenerate = abs(p_up - 0.5) < 1e-3 and unc >= 0.95
    return {
        "prediction": {
            "p_up": p_up,
            "uncertainty": unc,
            "direction": "UP" if p_up >= 0.5 else "DOWN",
            "degenerate": degenerate,
        },
        "model_version": str(ckpt.name),
        "schema_id": inf.schema_id,
    }
