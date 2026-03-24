# Module: `astro.services`

## Why this module exists

Routes and scripts shared the same problem: **resolve paths** under `data_root`, **load fused Parquet safely**, **attach optional inference**, and **validate schemas**—without copy-pasting. `FeatureService` and `build_decision_context` are the **single implementation** of that glue, which keeps API and CLI behavior aligned.

## Where it fits in the system

- Called from **`api/routes/*`** (`data`, `model`, `agents`, `decision`) and from **`scripts/`** via imports.  
- Sits **between** raw files (`pipelines` output) and **reasoning** (`decision_engine`, `agents`).

## What happens if it fails

| Failure | System impact |
|---------|----------------|
| Wrong `cwd` / `ROOT` | Silent reads from empty or wrong `data/` tree |
| Validation errors | Surfaced in API JSON; may still allow decision depending on route |
| Inference load failure | `model_predict_error` in `extra`; may trigger governance 503 |

## Module overview

| | |
|--|--|
| **Purpose** | Shared application services used by API routes and scripts. |
| **Responsibilities** | Load and validate fused Parquet; build `DecisionContext`; report model file readiness. |
| **Dependencies** | `decision_engine.state_manager`, `features.validation`, `models.transformer.inference`, `utils.config_loader`. |

## Key classes

| Class | Role |
|-------|------|
| `FeatureService` (`feature_service.py`) | Resolve paths under `data_root`; `load_fused`, `latest_feature_row`, `validate_for_schema`, `fused_path`. |

## Key functions

| Function | Role |
|----------|------|
| `build_decision_context` (`context_builder.py`) | Assemble `DecisionContext` + optional inference + validation flags. |
| `model_inference_status` (`model_readiness.py`) | Checkpoint/scaler existence and load smoke for `/health`. |
