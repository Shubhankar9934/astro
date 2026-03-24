# Module: `astro.agents`

## Why this module exists

LLMs excel at **synthesis and critique** when given **bounded, well-structured inputs**. This module wraps provider calls into **role-specific agents** (analysts, researchers, trader, risk) that all speak the same **state dictionary** contract expected by `DecisionExecutor` and `workflow.build_analyst_chain`. Without this layer, prompt strings would be scattered across routes and scripts—untestable and unsafe to evolve.

## Where it fits in the system

```mermaid
flowchart LR
  Ctx[DecisionContext]
  Ex[DecisionExecutor]
  Ag[agents_callables]
  St[AstroState_reports]
  Ctx --> Ex
  Ex --> Ag
  Ag --> St
```

**Upstream:** `DecisionContext` text fields and optional `ModelPrediction` (from `services.context_builder`).  
**Downstream:** Populated reports and debate histories consumed by **policy**, **signal extraction**, and **risk** in `decision_engine`.

## What happens if it fails

| Failure | System impact |
|---------|----------------|
| Provider auth error | Route or script raises; decision aborts mid-pipeline |
| Over-long context | Latency, truncation, or provider errors—monitor token usage |
| Bad patch shape from custom agent | `KeyError` or silent state corruption—follow existing patch patterns |

## Module overview

| | |
|--|--|
| **Purpose** | LLM-powered analysts, bull/bear researchers, research synthesizer, trader, three-way risk debators, risk judge, and shared memory utilities. |
| **Responsibilities** | Produce text reports and debate state consumed by `DecisionExecutor`; expose factory functions for each agent role. |
| **Dependencies** | `langchain` LLM handles from `utils.llm.factory`; `decision_engine.state_manager` types in payloads. |

## Key entry points (`astro/agents/__init__.py`)

Factory functions (representative list): `create_technical_analyst`, `create_sentiment_analyst`, `create_news_analyst`, `create_fundamentals_analyst`, `create_macro_analyst`, `create_bullish_researcher`, `create_bearish_researcher`, `create_research_synthesizer`, `create_trader_agent`, `create_aggressive_debator`, `create_conservative_debator`, `create_neutral_debator`, `create_risk_judge`.

Each returns a **callable** compatible with `workflow.build_analyst_chain` / executor patches (dict-in, dict-out patches on `AstroState` fields).

## Key classes

| Class / type | Role |
|--------------|------|
| `FinancialSituationMemory` (`agents/shared/memory.py`) | Role-tagged memory buffer for debators/judge. |
| Agent callables | Encapsulate prompt + LLM invoke; mutate state via returned patches. |

## Key functions

| Function | Description |
|----------|-------------|
| `extract_signal_from_text` (`agents/trader/signal_generator.py`) | Parse BUY/SELL/HOLD from narrative text. |
| `build_analyst_chain` (`decision_engine/workflow.py`) | Ordered list of analyst steps from string keys. |

## Subpackages

| Path | Role |
|------|------|
| `agents/analysts/` | Market, sentiment, news, fundamentals, macro |
| `agents/researchers/` | Bull, bear, debate engine, synthesizer |
| `agents/trader/` | Trader agent, signal extraction |
| `agents/risk/` | Debators, judge, exposure, portfolio constraints, position sizer |
| `agents/shared/` | Base agent, memory, messaging, grounding |
