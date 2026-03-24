from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from astro.api.dependencies import ROOT, get_config
from astro.storage.database import MetadataDB

router = APIRouter(prefix="/replay", tags=["replay"])


def _sanitize_for_json(obj: Any) -> Any:
    """Replace NaN/inf so Starlette/FastAPI json.dumps succeeds (RFC-compliant JSON)."""
    if obj is None or isinstance(obj, (str, bool)):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj, tuple):
        return [_sanitize_for_json(v) for v in obj]
    return obj


@router.get("")
def replay_decision(
    decision_id: int | None = None,
    log_file: str | None = Query(default=None),
    recompute: bool = Query(default=False),
):
    if recompute:
        raise HTTPException(501, "recompute=true not implemented")
    cfg = get_config()
    dr = cfg.data_root_path(ROOT)
    if decision_id is not None:
        db = MetadataDB(dr / "cache" / "astro_meta.sqlite")
        row = db.get_decision(decision_id)
        db.close()
        if not row:
            raise HTTPException(404, "decision not found")
        return {"source": "database", "record": _sanitize_for_json(row)}
    if log_file:
        p = Path(log_file)
        if not p.is_absolute():
            p = dr / "cache" / "decision_logs" / log_file
        if not p.exists():
            raise HTTPException(404, str(p))
        with open(p, encoding="utf-8") as f:
            record = json.load(f)
        return {"source": "file", "record": _sanitize_for_json(record)}
    raise HTTPException(400, "Provide decision_id or log_file")
