# Module: `astro.decision_engine`

## Why this module exists

This is the **orchestration brain**: it turns a static `DecisionContext` into a **time-ordered conversation** among agents, then converts natural-language output into a **trade signal** subject to **numeric governance** and **portfolio rules**. Centralizing that logic here avoids duplicating fragile control flow in every script and API route.

## Where it fits in the system

- **Input:** `DecisionContext` (+ `AstroConfig` for thresholds and analyst lists).  
- **Output:** Final signal string, `AstroState` for auditing, `run_meta` for sizing/governance, optional JSON log on disk.  
- **Peers:** Calls into `astro.agents`, reads/writes `astro.storage.database`, uses `astro.decision_engine.policy` and `routing`.

## What happens if it fails

| Failure | System impact |
|---------|----------------|
| Misconfigured `agents.yaml` | Wrong models, temperatures, or analyst keys—silent “quality” failure |
| Exception mid-pipeline | Partial state; API may 500; check logs under `astro.executor` |
| Policy mis-tuned | Signals always flattened to HOLD or opposite of LLM—tune `model_governance` |

## Module overview

| | |
|--|--|
| **Purpose** | Core orchestration: state types, executor, policy, routing, workflow helpers, governance mode resolution. |
| **Responsibilities** | Run fast/full decision pipelines; apply model governance and portfolio risk; persist decision logs when configured. |
| **Dependencies** | `agents`, `storage.database`, `utils.config_loader`, `utils.llm`, validation context via `services`. |

## Key classes

| Class | Role |
|-------|------|
| `DecisionContext` | Input snapshot for agents (`state_manager.py`). |
| `ModelPrediction` | Numeric model output attached to context. |
| `AstroState` | Mutable graph-like state for one decision run. |
| `DecisionExecutor` | Main orchestrator (`executor.py`). |

## Key functions

| Function | Role |
|----------|------|
| `DecisionExecutor.from_config` | Build executor with LLMs and memories. |
| `DecisionExecutor.run` | Full decision; returns `(AstroState, signal, run_meta)`. |
| `DecisionExecutor.run_analysts_only` | Partial pipeline for API. |
| `DecisionExecutor.run_research_only` | Analysts + research. |
| `DecisionExecutor.run_risk_only` | Risk cycle from dict / `RiskRequest` body. |
| `resolve_governance_mode` | `governance_mode.py` — env/YAML. |
| `model_missing_would_violate_governance` | Predicate for strict 503. |
| `should_continue_debate` / `should_continue_risk_analysis` | `routing.py`. |
| `apply_model_governance_detailed` | `policy.py`. |
| `build_analyst_chain` | `workflow.py`. |

For a narrative walkthrough of `run`, see [LLD](../design/lld.md).
