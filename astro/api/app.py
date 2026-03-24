from __future__ import annotations

from pathlib import Path

try:
    from dotenv import load_dotenv

    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from astro.api.lifecycle import lifespan
from astro.api.routes import agents, backtest, data, decision, execution, experiments, model, replay, stream, system

app = FastAPI(title="Astro Trading API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")
app.include_router(model.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(decision.router, prefix="/api/v1")
app.include_router(backtest.router, prefix="/api/v1")
app.include_router(execution.router, prefix="/api/v1")
app.include_router(replay.router, prefix="/api/v1")
app.include_router(experiments.router, prefix="/api/v1")
app.include_router(stream.router)
