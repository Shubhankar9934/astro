# Developer guide

This guide is for engineers who will **change behavior**, not only run scripts. It explains **where to plug in**, **what breaks when you do**, and how the **control flow** shifts.

## Repository layout

| Area | Role |
|------|------|
| `astro/` | Installable Python package—all production logic |
| `scripts/` | CLI entry scripts (`run_api`, `run_decision`, `train_model`, …) |
| `tests/` | `pytest` unit and integration tests |
| `postman/` | HTTP collection for manual or CI smoke |
| `docs/` | MkDocs site (this documentation) |

## How the flow changes when you add a new analyst

1. **Implement** a factory callable under `astro/agents/` (follow existing analysts: returns a function that accepts a state dict and returns patches).
2. **Register** the string key in `DecisionExecutor._analyst_factories` (`decision_engine/executor.py`).
3. **Configure** `selected_analysts` and/or `fast_mode_analysts` in `agents.yaml`.

**Flow impact:**

- **Full mode** will invoke your analyst whenever its key appears in `selected_analysts` (order matters—`build_analyst_chain` is sequential).
- **Fast mode** includes your analyst **only** if you add its key to `fast_mode_analysts`; otherwise full runs see it but fast runs skip it.
- **Latency and cost** increase linearly with extra LLM calls unless you gate your analyst behind cheap heuristics inside the callable.

**If your analyst fails:** Exceptions bubble from the chain; the API may return **500** unless caught—wrap and return a patch with an error string in the relevant report field for softer degradation.

## How the flow changes when you add a new HTTP route

1. Create `astro/api/routes/<name>.py` with an `APIRouter`.
2. `include_router` in `astro/api/app.py` with prefix `/api/v1` (or attach WebSocket routes at app root like `stream`).
3. Reuse **`get_config`**, **`get_executor`**, **`get_feature_service`** from `dependencies.py` instead of reloading YAML per request.

**Contract tip:** Add Pydantic models to `api/schemas/requests.py` for consistent **422** errors.

## How the system behaves when the model is missing

| Mode / config | `/model/predict` | `/decision/run` |
|---------------|------------------|-----------------|
| Artifacts absent | **503** (predict route) | Depends: **503** `model_required` if **strict** governance and `allow_llm_only_without_model` is false |
| Artifacts present but load fails | **503** or error in `model_predict_error` on decision | Same governance rules; `context.extra` carries diagnostics |

**Developer takeaway:** Never assume `context.model` is non-None—read `model_governance` and `resolve_governance_mode` when adding new routes that imply automated trading.

## Path and CWD rules

- Run CLI and `uvicorn` from the **project root** unless `data_root` and checkpoint paths are absolute.
- **`ROOT`** in `api/dependencies.py` is computed from source layout—it is **not** `os.getcwd()`. Changing packaging layout breaks artifact resolution.

## Testing

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

| Test area | Files |
|-----------|--------|
| API smoke | `tests/test_api.py` |
| Policy / governance assumptions | `tests/unit/test_policy.py` |
| Routing / debate loops | `tests/unit/test_routing.py` |

## LLM providers

Configure `quick_think` / `deep_think` in `agents.yaml` and export provider keys. Factory entry: `astro/utils/llm/factory.py`.

## Feature schema changes

1. Update `astro/features/schema_registry.json`.
2. Adjust `model.yaml` `feature_columns` and retrain.
3. Regenerate fused Parquet and invalidate old checkpoints if columns changed materially.

## Related

- [LLD](../design/lld.md) — executor lifecycle and governance  
- [Module breakdown](../design/module_breakdown.md) — package map  
- [Debugging](debugging.md) — operational failures
