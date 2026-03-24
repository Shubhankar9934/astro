# System design (deployment view)

## Configuration loading

All YAML is loaded from **`astro/configs/`** (package-relative) unless `load_all_configs(override_path=...)` is used with a custom directory (`astro/utils/config_loader.py`).

| File | Loaded into `AstroConfig` field |
|------|----------------------------------|
| `system.yaml` | `system` |
| `agents.yaml` | `agents` |
| `model.yaml` | `model` |
| `risk.yaml` | `risk` |
| `ibkr.yaml` | `ibkr` |

`AstroConfig.data_root_path(cwd)` resolves `system.data_root` (default `"data"`). If the path is relative, it is resolved as **`(cwd or Path.cwd()) / data_root`** then **`.resolve()`**. API code passes **`ROOT`** (`astro/api/dependencies.py`: parent of package root used for repo-relative artifacts) for data paths while model checkpoints use **`ROOT`** explicitly.

**Implication:** Running scripts or `uvicorn` from a directory that is **not** the project root will place `data/` and resolve checkpoints incorrectly unless paths are absolute in YAML.

## API application composition

- **Entry:** `astro.api.app:app` — `FastAPI(..., lifespan=lifespan)`.
- **CORS:** Permissive defaults (`allow_origins=["*"]`) suitable for local dev only; tighten for production behind a known UI origin.
- **Routers:** All REST routes mounted under **`/api/v1`** except the WebSocket router (`/ws/stream` on app root).

## Process boundaries

| Process | Typical command | Role |
|---------|-----------------|------|
| API | `python scripts/run_api.py` or `uvicorn astro.api.app:app --host 0.0.0.0 --port 8000` | HTTP + optional IBKR session |
| Decision CLI | `python scripts/run_decision.py ...` | Batch decision without HTTP |
| Training | `python scripts/train_model.py ...` | Writes checkpoints (requires `[train]`) |

## Security notes (in-repo behavior)

- **`GET /api/v1/system/config`** strips keys whose name contains `password` (case-insensitive) from the `ibkr` blob before JSON response (`system.py`).
- **`ASTRO_API_KEY`:** When set, `require_api_key` enforces `X-API-Key` on **`POST /api/v1/execution/order`** only (see `dependencies.py`).

## Related

- [HLD](hld.md) — component map  
- [Configuration](../setup/configuration.md) — keys and environment variables  
- [Deployment](../setup/deployment.md) — runtime and gaps (no Docker in repo)
