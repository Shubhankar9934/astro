# Debugging

This guide connects **symptoms** to **code paths** and **configuration**. Use it under incident pressure: start from the HTTP status or log line, then narrow to a subsystem.

## Logging (`astro/utils/logger.py`)

| Function | Role |
|----------|------|
| `setup_logging(level, json_format=False)` | Configure root handler to stdout; optional JSON lines for centralized log stacks. |
| `get_logger(name)` | Module-scoped logger (`astro.executor`, etc.). |
| `log_extra(logger, msg, **fields)` | Structured fields appended as JSON for grep-friendly ops. |

**Practice:** In long-running scripts (`run_live`, custom schedulers), call `setup_logging` at startup with `log_level` from `system.yaml` (wire this explicitly—not all entrypoints do today).

## Symptom → cause → fix

### Data and features

| Symptom | Likely cause | What to verify |
|---------|--------------|----------------|
| **404** on `/data/*` | Missing `{symbol}_fused.parquet` | `data_root` resolution with `ROOT` + cwd; file name spelling |
| Empty or nonsense analyst text | Stale or all-NaN tail rows | Open Parquet in pandas; check date column continuity |
| `schema_validation` errors in decision response | Registry vs file mismatch | `features/schema_registry.json`, re-run fusion |

### Model

| Symptom | Likely cause | What to verify |
|---------|--------------|----------------|
| **503** on `/model/predict` | Missing `best.pt` / `scaler.npz` | Paths under `models/checkpoints/` relative to `ROOT` |
| `model_predict_error` populated | Load exception or column mismatch | Logs from inference; compare `feature_columns` in `model.yaml` to Parquet |
| `degenerate: true` in predict response | Near-random classifier output | Retrain, check labels, check class balance |

### Governance and decisions

| Symptom | Likely cause | What to verify |
|---------|--------------|----------------|
| **503** `model_required` | Strict governance without `context.model` | `agents.yaml` `model_governance`, env `ASTRO_GOVERNANCE_MODE`, checkpoint presence |
| Unexpected **HOLD** or muted signal | Policy thresholds | `min_edge_for_directional`, `allow_llm_in_weak_band` |
| Zero `suggested_size_usd` | Risk / exposure rejection | `risk.yaml`, SQLite positions, `sizing_rejected_reason` in executor meta |

### LLM

| Symptom | Likely cause | What to verify |
|---------|--------------|----------------|
| 401/429 from provider | Keys, quotas, wrong model name | `agents.yaml` models match provider dashboard |
| Hangs | Blocking call inside async context | Prefer async patterns for future routes; check network |

### IBKR

| Symptom | Likely cause | What to verify |
|---------|--------------|----------------|
| `ibkr_connect_error` on health | Gateway down, wrong port, missing `ib_async` | `ibkr.yaml`, `ASTRO_SKIP_IBKR_CONNECT`, logs from `lifecycle.py` |
| **503** on `/execution/order` | Broker exception inside `submit_market` | Paper account permissions, symbol mapping |

### Auth

| Symptom | Likely cause | What to verify |
|---------|--------------|----------------|
| **401** on execution | `ASTRO_API_KEY` set but header missing/wrong | `X-API-Key` header |
| **403** on execution | Live trading blocked | `paper: true` in `ibkr.yaml` |

## SQLite and concurrency

Multiple processes writing **`astro_meta.sqlite`** without a proper locking strategy can cause **database is locked** or corruption. Run **one writer** process for production, or migrate metadata to a server-grade database.

## Interactive inspection

FastAPI **`/docs`** is the fastest way to see exact **422** validation payloads for malformed JSON.

## Cache cleanup

If behavior seems “stuck” after config or data changes, see **`CLEAR_CACHE.md`** at the repository root for cache locations and safe deletion steps.
