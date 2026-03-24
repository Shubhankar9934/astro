# Module: `astro.api`

## Why this module exists

Operators and integrators need a **stable HTTP contract** to drive the same logic developers run in scripts. FastAPI provides OpenAPI, validation, and async lifespan hooks (IBKR) without embedding transport concerns inside `DecisionExecutor`.

## Where it fits

**Outermost layer** for HTTP/WebSocket; depends inward on services, decision engine, storage, execution. Not imported by core algorithms (avoid cycles).

## If it fails

Misconfigured routes surface as **422**; broker lifecycle failures still leave API up but populate `ibkr_connect_error`—distinguish “API down” vs “broker down” via `/health`.

## Overview

| | |
|--|--|
| **Purpose** | FastAPI application, HTTP/WebSocket routes, Pydantic request schemas, dependency injection, startup/shutdown IBKR lifecycle. |
| **Responsibilities** | Expose control plane for health, data, model, agents, decisions, backtest, execution, replay, experiments, stream. |
| **Dependencies** | `fastapi`, `uvicorn` (optional extra); `decision_engine`, `services`, `storage`, `execution`, `ingestion.ibkr.client`. |

## Key classes / objects

| Symbol | Role |
|--------|------|
| `app` (`api/app.py`) | `FastAPI` instance with CORS and included routers. |
| `lifespan` (`api/lifecycle.py`) | Async context manager: IBKR connect/disconnect. |

## Key functions / dependencies

| Symbol | Role |
|--------|------|
| `get_config` / `get_config_cached` | Return `AstroConfig` (`lru_cache`). |
| `get_feature_service` | `FeatureService(config, cwd=ROOT)`. |
| `get_executor` | `DecisionExecutor.from_config(..., log_dir=...)`. |
| `require_api_key` | FastAPI dependency: optional `X-API-Key` check. |

## Routes

| File | Prefix (under `/api/v1` unless noted) |
|------|----------------------------------------|
| `routes/system.py` | `/system` |
| `routes/data.py` | `/data` |
| `routes/model.py` | `/model` |
| `routes/agents.py` | `/agents` |
| `routes/decision.py` | `/decision` |
| `routes/backtest.py` | `/backtest` |
| `routes/execution.py` | `/execution` |
| `routes/replay.py` | `/replay` |
| `routes/experiments.py` | `/experiments` |
| `routes/stream.py` | `/ws/stream` on app |

Schemas: `api/schemas/requests.py`.
