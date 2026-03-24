# Low-level design (LLD)

This page explains **how** the core runtime behaves—not only **what** types exist. Read it alongside [Sequence diagrams](../architecture/sequence_diagrams.md) and [Decision flow narrative](../architecture/data_flow.md#decision-execution-narrative).

**Orchestration ownership:** All multi-step LLM work for a full decision runs under **`DecisionExecutor`** (`run` or `run_analysts_only` / `run_research_only` / `run_risk_only`). The HTTP layer **does not** implement its own agent graph; routes build context and delegate.

## Core types (contracts)

### `ModelPrediction` (`decision_engine/state_manager.py`)

| Field | Meaning |
|-------|---------|
| `p_up` | Probability of upward move (classifier head) |
| `expected_return` | Optional regression-style output |
| `uncertainty` | Derived uncertainty (e.g. entropy-related in inference) |
| `raw` | Arbitrary diagnostic payload |

**Why it matters:** Downstream code treats `uncertainty` as a **control knob**—high uncertainty can **upgrade** fast mode to full (`should_upgrade_fast_to_full`) or **skip** expensive debate (`should_skip_research_debate`). Missing `ModelPrediction` entirely is different from “degenerate” numeric output; governance uses **presence** for strict mode.

### `DecisionContext`

Typed snapshot passed into agents and the executor.

| Field | Meaning |
|-------|---------|
| `symbol`, `as_of` | Instrument and decision date |
| `market_summary`, `sentiment_summary`, `news_summary`, `fundamentals_summary` | Text inputs for LLM prompts |
| `feature_version`, `bar_timestamp` | Lineage |
| `model` | Optional `ModelPrediction` |
| `extra` | Schema validation flags, paths, sizing hints (`sizing_atr`, `sizing_price`), structured facts, `model_predict_error`, checkpoint path for hashing |

**Contract:** Agents should **not** re-read Parquet; they consume summaries in the context. That keeps **train/live** alignment and makes API responses **explainable** (snippets + `structured_market_facts`).

### `AstroState`

Mutable workflow state: analyst reports, debate dicts, `investment_plan`, `trader_investment_plan`, `final_trade_decision`, embedded `context`.

**State transitions (conceptual):**

1. Empty reports → **analyst chain** fills `market_report`, etc.
2. Research phase mutates **`investment_debate_state`** and finally **`investment_plan`**.
3. Trader writes **`trader_investment_plan`** and contributes to **`final_trade_decision`** path via risk cycle output.
4. Risk phase fills **`risk_debate_state`** and ultimately **`final_trade_decision`** (narrative).

## Context building (`services/context_builder.py`)

**`build_decision_context(symbol, trade_date, fused_parquet, ...)`** is the **bridge** from files to LLMs.

- **Loads** fused DataFrame when path exists; builds human-readable tails and **`structured_market_facts`** (numeric last-bar audit) from the final row.
- **Inference:** If checkpoint and scaler exist, **`load_inference_optional`** runs; on success, **`context.model`** is populated; on failure, errors are **non-fatal** for the builder but may trigger **503** later when governance demands a model.
- **Validation:** **`validate_fused_frame`** records pass/fail in `extra` so the API can return **schema_validation** without blocking every path.

**Failure lens:** Missing Parquet does not always abort the API route—check **`decision.py`** vs **`model.py`** behavior. Operators should treat **404** on data routes as “artifact gap,” not “bug.”

## `DecisionExecutor` (`decision_engine/executor.py`)

### Construction

**`from_config(config, log_dir)`** loads `AstroConfig`, builds **two** LLM handles (`quick_think`, `deep_think` from `agents.yaml`), and allocates **role-scoped** `FinancialSituationMemory` for bull, bear, trader, judges. This is intentional: **debate roles** must not share unbounded cross-talk memory unless you extend the implementation.

### `run` — execution lifecycle (step-by-step)

1. **Resolve requested mode** — `mode` argument or `decision_mode_default` from YAML.
2. **Auto-upgrade** — If user asked **fast** but model uncertainty is above **`uncertainty_debate_threshold`**, effective mode becomes **full** (logged at INFO). *Why:* low model confidence should not skip deep risk discussion.
3. **Debate skip flag** — `should_skip_research_debate` can bypass bull/bear when the model is **very** certain (configurable).
4. **Initialize `AstroState`** with fresh debate dicts from **`initial_invest_debate`** / **`initial_risk_debate`**.
5. **Branch pipeline:**
   - **Full:** run all **`selected_analysts`** → research (maybe skipped) → trader → **three-way** risk debators → judge loop (`routing.py` drives turns).
   - **Fast:** run **`fast_mode_analysts`** only → synthesize a compressed **`investment_plan`** (optionally inject model line) → trader → **single** risk judge path (`_risk_cycle(fast=True)`).
6. **Signal extraction** — `extract_signal_from_text(final_trade_decision)` yields a **string** signal (e.g. BUY/SELL/HOLD semantics—see signal generator).
7. **Governance** — `apply_model_governance_detailed` may **override or hold** the LLM signal using `model_governance` thresholds; returns metadata for API consumers.
8. **Portfolio layer** — Opens **`MetadataDB`**, builds **`ExposureManager`**, runs **`apply_post_decision_risk`** with NAV, `p_up`, ATR/price hints from `context.extra`. *Side effect:* may zero suggested size when constraints reject exposure.
9. **Logging** — If `log_dir` set, writes a **rich JSON** artifact including raw vs final signal, governance record, checkpoint hash, schema ids, and **serialized state**.

**Returns:** `(AstroState, final_signal: str, run_meta: dict)` — API maps these into JSON and inserts a **decision row**.

### Pseudocode (structure only)

```text
function run(symbol, trade_date, context, mode):
    requested = mode or config.agents.decision_mode_default
    effective = upgrade_if_uncertain(requested, context.model)
    state = fresh_state(symbol, trade_date, context)
    if effective == full:
        run_all_analysts(state)
        research(state, skip=should_skip_debate(context.model))
        trader(state)
        risk_multiway(state)
    else:
        run_fast_analysts(state)
        synthesize_fast_plan(state, context.model)
        trader(state)
        risk_single_judge(state)
    raw_sig = extract_signal(state.final_trade_decision)
    final_sig, gov_meta = governance(raw_sig, context.model, config.model_governance)
    final_sig, size_usd = portfolio_constraints(final_sig, sqlite, config.risk, context)
    maybe_write_json_log(...)
    return state, final_sig, {governance: gov_meta, suggested_size_usd: size_usd, ...}
```

### Partial runs (API)

| Method | Use |
|--------|-----|
| `run_analysts_only` | `POST /api/v1/agents/analysts` — cheaper **diagnostics** of prompts and data |
| `run_research_only` | `POST /api/v1/agents/research` — analysts + debate without risk |
| `run_risk_only` | `POST /api/v1/agents/risk` — supply reports from an external system; **400** if internal exception |

## Governance (`decision_engine/governance_mode.py`)

| Mode | Env / YAML |
|------|------------|
| `strict` | Default; `ASTRO_GOVERNANCE_MODE` overrides |
| `degraded` | Allows run when model missing but governance would require it; response flags |
| `dev` | Development bypass semantics per route response |

**`model_missing_would_violate_governance`:** `model_governance.enabled` and not `allow_llm_only_without_model` and `ctx.model is None`.

**API:** Before `executor.run`, if `strict` and violation → **HTTP 503** with structured `detail` (`api/routes/decision.py`). *Rationale:* fail **closed** for automated consumers that must not trade without a model when policy says so.

## Storage (`storage/database.py`)

**`MetadataDB`** — SQLite connection; methods used by API include `insert_decision`, `get_decision`, `positions_max_updated_at`, `log_experiment`, and order-related paths via execution layer.

## Routing (`decision_engine/routing.py`)

**`should_continue_debate`**, **`should_continue_risk_analysis`** — Drive bull/bear and aggressive/conservative/neutral loops up to `max_debate_rounds` / `max_risk_discuss_rounds`. Changing these functions changes **latency** and **cost** without touching agent prompts.

## Related diagrams

- [Class diagrams](class_diagrams.md)  
- [Sequence diagrams](../architecture/sequence_diagrams.md)  
- [Design patterns](design_patterns.md)
