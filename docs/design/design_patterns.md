# Design patterns

Patterns below are **observed** in code—not marketing labels. Use them when extending the system so new code stays consistent with existing boundaries (especially **policy** and **repository**).

| Pattern | Where | Role |
|---------|-------|------|
| **Strategy** | `utils/llm/factory.py` — `create_llm_client(provider, model, ...)` | Swap OpenAI / Anthropic / Google clients without changing agent constructors. |
| **Policy / rules engine** | `decision_engine/policy.py` — `apply_model_governance_detailed` | Encode `model_governance` thresholds and overrides on top of raw LLM-extracted signal. |
| **Repository (lightweight)** | `storage/database.py` — `MetadataDB` | Encapsulate SQLite access for decisions, experiments, positions, orders. |
| **Pipeline** | `pipelines/*.py`, `fusion_pipeline.py` | Deterministic stages producing versioned Parquet outputs. |
| **Template method** | `DecisionExecutor` — `_run_full_pipeline` / `_run_fast_pipeline` | Fixed phase ordering with configurable analyst lists and debate skips. |
| **Idempotent command** | `execution/order_manager.py` + `ExecutionOrderRequest.idempotency_key` | Duplicate submits return `status: duplicate` without double execution. |
| **Dependency injection (FastAPI)** | `Depends(require_api_key)`, `get_config`, `get_executor` | Testable route surfaces; cached config. |
| **Lifespan resource** | `api/lifecycle.py` | Acquire IBKR client on startup, release on shutdown. |

## Anti-patterns avoided (by design)

- **Implicit graph execution** — Replaced with explicit loops and `routing.py` helpers for parity with legacy graphs while remaining readable in Python.

## Trade-offs

- **Global config cache** (`lru_cache` on `get_config_cached`) speeds requests but requires process restart to pick up YAML edits.
- **CWD-sensitive paths** — Documented in [System design](../architecture/system_design.md); operators must standardize launch directory or use absolute `data_root`.
