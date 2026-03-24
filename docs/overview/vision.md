# Vision

## Why this project exists

Institutional and serious retail quant teams increasingly combine **classical features**, **deep learning**, and **LLMs**. Without architectural discipline, that combination becomes a **single undifferentiated script** where nobody can answer: *what data did we see?*, *what did the model believe?*, *what did the LLM actually decide?*, *why was an order blocked?* Astro exists to make those questions **answerable** by construction—through artifacts, typed context, explicit phases, and persisted decisions.

Astro Trading (`astro-trading`) is a **modular trading intelligence platform** designed around four commitments:

1. **Separation of data and reasoning** — Market, news, and sentiment data are ingested and engineered into versioned feature artifacts (Parquet, schema registry). LLM agents consume a **`DecisionContext`** built from those artifacts (and optional model scores), not ad-hoc tool calls embedded in an opaque graph runtime.

2. **First-class quantitative signal** — A **transformer** path provides `p_up`, uncertainty, and related metadata. **Policy** (`decision_engine/policy.py`, `model_governance` in `agents.yaml`) can constrain or blend LLM-extracted signals with model output.

3. **Explicit orchestration** — The **`DecisionExecutor`** implements analyst → research → trader → risk flows as **plain Python control flow** with configurable fast/full modes and routing helpers aligned with legacy LangGraph semantics (`routing.py`).

4. **Operational control plane** — Optional **FastAPI** exposes health, data inspection, model predict, partial agent runs, full decisions, backtest, IBKR execution (paper-gated), replay, and experiment logging.

The system is **IBKR-first** in its ingestion and execution paths but remains usable offline with CSV/Parquet workflows documented in [Data flow](../architecture/data_flow.md).
