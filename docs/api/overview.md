# API overview

## Design philosophy

The HTTP layer is a **thin control plane**: it validates inputs, resolves **`ROOT`** and **`data_root`**, builds **`DecisionContext`**, and delegates to the same classes scripts use (`FeatureService`, `DecisionExecutor`, `MetadataDB`). That means **behavior parity** between batch and API—at the cost of requiring a **consistent deployment layout** (see [System design](../architecture/system_design.md)).

**Deliberate split:** `POST /decision/run` does **not** auto-place broker orders. Execution is a **separate** call so humans or risk systems can interpose.

## Base URL and versioning

| Item | Value |
|------|-------|
| REST prefix | `/api/v1` |
| WebSocket path | `/ws/stream` (no `/api/v1` prefix) |
| Default local base | `http://localhost:8000` |

## Interactive documentation

When the server is running, OpenAPI UI is served by FastAPI:

| UI | URL |
|----|-----|
| Swagger | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |

Use these for **authoritative** request/response models if they differ from static examples after code changes.

## Authentication

| Mechanism | Scope |
|-----------|-------|
| **`X-API-Key`** | Only enforced on **`POST /api/v1/execution/order`** when environment variable **`ASTRO_API_KEY`** is set (`astro/api/dependencies.py::require_api_key`). |
| Other routes | No API key in current code. |

## Error model

FastAPI returns standard **JSON** bodies:

| Status | Typical cause |
|--------|----------------|
| **400** | Bad request (e.g. replay missing params; backtest schema failure as string) |
| **401** | Invalid or missing `X-API-Key` when key auth enabled |
| **403** | Live trading blocked (`ibkr.paper` not true on execution route) |
| **404** | Missing fused file, decision id, or log file |
| **422** | Pydantic validation error on body or query |
| **501** | Not implemented (`replay?recompute=true`) |
| **503** | Model checkpoint/scaler missing on predict; execution failure; **decision** `model_required` under strict governance |

## Rate limiting

**Not implemented** in this repository—no middleware or gateway configuration is bundled.

## Postman

Import **`postman/Astro_Trading_API.postman_collection.json`** for a curated flow.

## Next

[HTTP endpoints reference](endpoints.md)
