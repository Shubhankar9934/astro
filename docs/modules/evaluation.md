# Module: `astro.evaluation`

## Why this module exists

Provides a dedicated entry for **offline evaluation jobs** separate from training and API serving—useful as the project grows beyond a single `trainer.py` loop.

## Where it fits

Invoked via `python -m astro.evaluation`; interacts with core packages depending on `runner.py` implementation.

## If it fails

Consult source—API surface is still evolving; extend docs when stabilized.

## Overview

| | |
|--|--|
| **Purpose** | Offline evaluation utilities and CLI entry (`python -m astro.evaluation`). |
| **Responsibilities** | Run evaluation jobs against saved artifacts or metrics (see source for current scope). |
| **Dependencies** | Project core packages as invoked by `runner.py`. |

## Key symbols

| Symbol | Role |
|--------|------|
| `evaluation/runner.py` | Orchestrates evaluation steps. |
| `evaluation/__main__.py` | Module execution entry point. |

Consult `astro/evaluation/` for the exact public API surface; extend this page when evaluation stabilizes.
