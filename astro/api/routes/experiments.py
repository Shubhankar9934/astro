from __future__ import annotations

from fastapi import APIRouter

from astro.api.dependencies import ROOT, get_config
from astro.api.schemas.requests import ExperimentLogRequest
from astro.storage.database import MetadataDB

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("/log")
def log_experiment(req: ExperimentLogRequest):
    cfg = get_config()
    dr = cfg.data_root_path(ROOT)
    db = MetadataDB(dr / "cache" / "astro_meta.sqlite")
    eid = db.log_experiment(req.model_version, req.schema_id, req.payload)
    db.close()
    return {"experiment_id": eid, "status": "logged"}
