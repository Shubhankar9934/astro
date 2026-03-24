# Module: `astro.pipelines`

## Why this module exists

Deterministic transforms must stay **out** of LLM code. Pipelines turn messy inputs into **typed Parquet** with predictable columns so the rest of the stack can stay declarative (YAML, validation, SQL).

## Where it fits

Downstream of `ingestion`, upstream of `FeatureService` and `models`. Fusion output is the **system contract surface**.

## If it fails

Missing files or bad joins manifest as empty modalities or validation errors—debug ETL here before blaming agents.

## Overview

| | |
|--|--|
| **Purpose** | Deterministic ETL-style pipelines from raw/interim inputs to **Parquet** feature files. |
| **Responsibilities** | Market, news, sentiment pipelines; **fusion** into a single per-symbol fused frame. |
| **Dependencies** | `features`, `pandas`, `pyarrow`. |

## Key classes / functions

| Module | Role |
|--------|------|
| `market_pipeline.py` | `MarketPipeline.run` → per-symbol feature Parquet. |
| `news_pipeline.py` | News-derived features. |
| `sentiment_pipeline.py` | Sentiment-derived features. |
| `fusion_pipeline.py` | `fuse_features` — merged fused Parquet for model and decisions. |
