from __future__ import annotations

import os

from fastapi import APIRouter, Request

from astro.api.dependencies import ROOT, get_config
from astro.ingestion.ibkr.client import IBKRClient, IBKRConnectionConfig
from astro.services.model_readiness import model_inference_status

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
def health(request: Request):
    cfg = get_config()
    ibkr_ok: bool | None = None
    ibkr_err = getattr(request.app.state, "ibkr_connect_error", None)
    shared = getattr(request.app.state, "ibkr_client", None)
    if shared is not None:
        try:
            ibkr_ok = bool(shared.ib.isConnected())
        except Exception:
            ibkr_ok = False
    elif os.environ.get("ASTRO_HEALTH_CHECK_IBKR") == "1":
        ibkr_ok = False
        try:
            ic = IBKRConnectionConfig.from_dict(cfg.ibkr)
            c = IBKRClient(ic)
            c.connect()
            ibkr_ok = c.ib.isConnected()
            c.disconnect()
        except Exception:
            ibkr_ok = False
    mr = model_inference_status(ROOT)
    return {
        "status": "ok",
        "ibkr_connected": ibkr_ok,
        "ibkr_connect_error": ibkr_err,
        "model_loaded": mr["inference_loadable"],
        "model": {
            "checkpoint_exists": mr["checkpoint_exists"],
            "scaler_exists": mr["scaler_exists"],
            "inference_loadable": mr["inference_loadable"],
            "inference_ready": mr["inference_ready"],
            "inference_smoke_ok": mr["inference_smoke_ok"],
            "load_error": mr["load_error"],
            "schema_id": mr["schema_id"],
        },
    }


@router.get("/config")
def merged_config():
    cfg = get_config()
    return {
        "system": cfg.system,
        "agents": cfg.agents,
        "model": cfg.model,
        "risk": cfg.risk,
        "ibkr": {k: v for k, v in cfg.ibkr.items() if "password" not in k.lower()},
    }
