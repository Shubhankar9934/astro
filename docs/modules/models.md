# Module: `astro.models`

## Why this module exists

A dedicated **numeric** head prevents forcing the LLM to act as a classifier on raw OHLCV. The transformer produces calibrated-ish probabilities and uncertainty used by governance and routing.

## Where it fits

Trained offline; loaded at API/script time via `load_inference_optional`. Outputs attach to `DecisionContext.model`.

## If it fails

Missing or mismatched checkpoints yield **503** on predict or governance blocks—align `schema_id` and `feature_columns` with fused data.

## Overview

| | |
|--|--|
| **Purpose** | Trainable models and inference wrappers; currently centered on a **transformer** binary classifier. |
| **Responsibilities** | Architecture definition, dataset windows, training loop, inference with uncertainty. |
| **Dependencies** | `torch` for training/inference (`[train]` extra). |

## Subpackages

### `models/transformer/`

| Symbol | Role |
|--------|------|
| `trainer.train` | Fit model; write `best.pt` and metadata. |
| `inference.TransformerInference` | Load checkpoint + scaler; `predict_latest_from_parquet`. |
| `load_inference_optional` | Return `None` if artifacts missing (API uses this). |
| `dataset.py` | Time-ordered windows and labels. |
| `architecture.py` | Network definition. |

### `models/ensemble/`

| `aggregator.py` | Stub / placeholder for future ensemble logic. |
