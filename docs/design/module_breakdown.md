# Module breakdown

## How packages fit together

Think of `astro/` as **layers you can reason about independently**:

- **Edges:** `ingestion` and `api` talk to the outside world (files, brokers, HTTP).
- **Core data plane:** `pipelines` and `features` produce **trusted** Parquet.
- **Model plane:** `models` turns Parquet windows into **`ModelPrediction`**.
- **Reasoning plane:** `agents` + `decision_engine` consume **`DecisionContext`** and emit **signals**.
- **Persistence plane:** `storage` and on-disk logs make outcomes **durable**.
- **Cross-cutting:** `utils` (config, logging, LLM factory) and `services` (glue used by API and scripts).

The per-module pages below focus on **public-ish interfaces** and **failure impact**, not every helper function—see source for exhaustive detail.

Top-level packages under `astro/` (import root). Each has a dedicated page under **Modules**.

| Module | Purpose (summary) |
|--------|---------------------|
| [agents](../modules/agents.md) | LLM analysts, researchers, trader, risk debators/judge, shared memory |
| [api](../modules/api.md) | FastAPI app, routes, schemas, dependencies, lifespan |
| [backtesting](../modules/backtesting.md) | Signal backtest engine, simulator, metrics |
| [configs](../modules/configs.md) | YAML contracts (no Python package logic) |
| [decision_engine](../modules/decision_engine.md) | State, executor, policy, routing, workflow |
| [evaluation](../modules/evaluation.md) | Evaluation runner CLI package |
| [execution](../modules/execution.md) | Trade executor, order manager, slippage |
| [features](../modules/features.md) | Indicators, validation, schema registry JSON |
| [ingestion](../modules/ingestion.md) | IBKR, news, sentiment, scheduler |
| [models](../modules/models.md) | Transformer and ensemble stubs |
| [monitoring](../modules/monitoring.md) | Dashboard / monitoring placeholders |
| [pipelines](../modules/pipelines.md) | Market, news, sentiment, fusion pipelines |
| [services](../modules/services.md) | FeatureService, context builder, model readiness |
| [storage](../modules/storage.md) | SQLite MetadataDB, optional vector store |
| [utils](../modules/utils.md) | Config loader, logger, LLM factory, time helpers |

**Repository root** (not under `astro/`): `scripts/`, `tests/`, `postman/`, `data/` layout—see [Developer guide](../guides/developer_guide.md).
