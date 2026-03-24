# Module: `astro.backtesting`

## Why this module exists

Before trusting agents or models with capital, teams need **cheap** historical evaluation of a signal column. This module stays LLM-free for reproducibility.

## Where it fits

Called from `api/routes/backtest.py` and scripts; consumes fused frames via `FeatureService`.

## If it fails

**400** on schema validation—fix Parquet vs registry before interpreting Sharpe numbers.

## Overview

| | |
|--|--|
| **Purpose** | Run lightweight signal-driven backtests on fused feature DataFrames and compute summary metrics. |
| **Responsibilities** | Signal backtest loop, equity curve, trade list, Sharpe and drawdown helpers. |
| **Dependencies** | `pandas`; `services.feature_service` for validation at API boundary. |

## Key functions

| Function | Inputs | Outputs |
|----------|--------|---------|
| `run_signal_backtest` (`engine.py`) | DataFrame, signal column name | Result object with `equity_curve`, `trades` |
| `sharpe_ratio` (`metrics.py`) | Return series | float |
| `max_drawdown` (`metrics.py`) | Equity curve series | float |

## Key classes

| Class | Role |
|-------|------|
| Types in `engine.py` / `simulator.py` | Encapsulate simulation state (consult source for dataclass names). |
