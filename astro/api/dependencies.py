from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import Header, HTTPException

from astro.decision_engine.executor import DecisionExecutor
from astro.services.feature_service import FeatureService
from astro.utils.config_loader import AstroConfig, load_all_configs

ROOT = Path(__file__).resolve().parents[2]


@lru_cache
def get_config_cached() -> AstroConfig:
    return load_all_configs()


def get_config() -> AstroConfig:
    return get_config_cached()


def get_feature_service() -> FeatureService:
    return FeatureService(get_config(), cwd=ROOT)


def get_executor() -> DecisionExecutor:
    cfg = get_config()
    dr = cfg.data_root_path(ROOT)
    return DecisionExecutor.from_config(cfg, log_dir=dr / "cache" / "decision_logs")


async def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    expected = os.environ.get("ASTRO_API_KEY")
    if not expected:
        return
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
