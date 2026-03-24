# Module: `astro.configs`

## Why this module exists

Runtime behavior (analysts, governance, risk, broker endpoints) must be **diffable** and **environment-promotable** without code changes. YAML in-package is the default source of truth loaded by `config_loader`.

## Where it fits

Read at process start (with `lru_cache` in API). No Python imports—pure data.

## If it fails

Silent defaults if a file is missing (empty dict sections)—validate critical keys in ops checklists.

## Overview

| | |
|--|--|
| **Purpose** | Version-controlled YAML configuration shipped inside the package. |
| **Responsibilities** | Define defaults for system, agents, model, risk, and IBKR connectivity. |
| **Dependencies** | None (static files); loaded by `utils.config_loader`. |

## Files

| File | Content |
|------|---------|
| `system.yaml` | `data_root`, `log_level`, timezone, debounce hints |
| `agents.yaml` | Analyst lists, LLM providers/models, `model_governance`, debate thresholds |
| `model.yaml` | Transformer hyperparameters, paths, `schema_id`, `feature_columns` |
| `risk.yaml` | Position limits, NAV, slippage, stale position warnings |
| `ibkr.yaml` | Host, port, `client_id`, `paper`, timeouts |

**Security:** Do not commit live secrets; use environment variables as documented in [Configuration](../setup/configuration.md).
