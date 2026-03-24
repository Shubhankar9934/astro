# Module: `astro.features`

## Why this module exists

Trading features must be **repeatable** and **verifiable**. This module holds indicator logic, helpers, and the **schema registry** so training, inference, and API validation share one definition of “valid fused data.”

## Where it fits

Between **pipelines** (writers) and **models/services** (readers). A column added here without registry/fusion updates will break downstream consumers.

## If it fails

Validation errors propagate to API responses and training exceptions—fix data or registry, not random try/except in routes.

## Overview

| | |
|--|--|
| **Purpose** | Feature engineering helpers, schema registry, and fused-frame validation. |
| **Responsibilities** | Technical indicators, volatility, sentiment/news helpers, fundamental stubs; enforce column contracts. |
| **Dependencies** | `pandas`, `pyarrow`; `schema_registry.json` on disk. |

## Key functions

| Function | Role |
|----------|------|
| `validate_fused_frame` (`validation.py`) | Check required columns per schema id. |

## Key artifacts

| Path | Role |
|------|------|
| `features/schema_registry.json` | `default_schema_id`, per-schema `required_columns`. |
| `features/diagnostics.py` | Feature quality diagnostics. |

## Subpackages

| Path | Role |
|------|------|
| `features/technical/` | Indicators, volatility |
| `features/sentiment/` | Embeddings, scoring |
| `features/news/` | Macro features, event extraction |
| `features/fundamental/` | Valuation/ratio stubs |
