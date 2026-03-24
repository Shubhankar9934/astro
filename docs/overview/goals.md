# Goals

## How to read these goals

Each row below ties a **product principle** to **concrete mechanisms in code**. If a deployment cannot satisfy a goal, the fix is usually **config**, **data layout**, or **YAML policy**—not a rewrite of business logic.

| Goal | Target outcome |
|------|----------------|
| **Reproducibility** | Same fused feature files and configs drive training, inference, API predict, and decision runs where applicable (`FeatureService`, `build_decision_context`). |
| **Schema safety** | `astro/features/schema_registry.json` and `features/validation.py` define required columns; trainer, inference, and backtest routes validate before heavy work. |
| **Latency control** | `fast` vs `full` decision modes; automatic upgrade from fast to full when model uncertainty exceeds `uncertainty_debate_threshold` (`DecisionExecutor.run`). |
| **Risk-aware outputs** | Post-decision sizing and constraints via `ExposureManager`, `apply_post_decision_risk`, and SQLite-backed positions (`astro_meta.sqlite`). |
| **Safe execution API** | Live trading disabled when `paper` is not `true` in `ibkr.yaml`; optional API key on order submission. |
| **Observability hooks** | Decision JSON logs under `data/cache/decision_logs/`; SQLite rows for decisions and experiments; structured health including model readiness (`system/health`). |

Non-goals for this repository (as shipped): hosted multi-tenant SaaS, built-in Docker/CI for docs or deploy, and guaranteed production market-data SLAs—see [Future scope](../roadmap/future_scope.md).
