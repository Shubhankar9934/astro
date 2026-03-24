# Problem statement

## The underlying pain

Quantitative and LLM-assisted trading stacks often entangle **data acquisition**, **feature logic**, and **agent orchestration** in ways that are hard to test, replay, and govern in production. The failure mode is subtle: the system “works” in a notebook yet **fails silently** in production when schemas drift, keys leak into prompts, or a model file is missing—because no layer owned **verification** before spend (GPU, LLM tokens, broker calls).

## What Astro changes

- **Opaque graphs** — Replacing a monolithic LangGraph-style loop with **`DecisionExecutor`** makes branching (fast/full, skip debate, risk rounds) inspectable and unit-testable.
- **Train/serve skew** — Centralizing fused Parquet loading and validation in **`FeatureService`** and aligning paths with **`AstroConfig.data_root_path(cwd)`** reduces “works on my laptop” path bugs (still: callers must use a consistent **current working directory**).
- **Unbounded LLM risk** — **`model_governance`** and **`resolve_governance_mode`** (YAML + `ASTRO_GOVERNANCE_MODE`) define when the system must refuse a decision without a model (**strict** → HTTP 503 on the decision route).
- **Broker integration fragility** — IBKR connection is **optional** at API startup (`ASTRO_SKIP_IBKR_CONNECT`); health can optionally probe IBKR (`ASTRO_HEALTH_CHECK_IBKR=1`). Execution reuses `app.state.ibkr_client` or connects ad hoc.

**Residual limitations** (honest scope):

- Horizontal scaling of the API assumes shared filesystem or externalizing SQLite and artifacts; **IBKR** is effectively a **singleton** session per API process.
- **Monitoring** and **ensemble** modules contain stubs; see [Future scope](../roadmap/future_scope.md).
