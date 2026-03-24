# Module: `astro.utils`

## Why this module exists

Configuration, logging, and LLM vendor selection are **cross-cutting**. Centralizing them avoids import cycles and keeps operational toggles discoverable.

## Where it fits

Imported from nearly every package; keep it **thin**—no business rules here.

## If it fails

Bad YAML → empty dicts or wrong types downstream; bad env keys → LLM auth errors surfaced late.

## Overview

| | |
|--|--|
| **Purpose** | Cross-cutting utilities: configuration, logging, time, constants, LLM client factory. |
| **Responsibilities** | Single source for YAML-backed `AstroConfig`; structured logging setup; provider-specific LLM adapters. |
| **Dependencies** | `pyyaml`; `langchain` stacks per provider. |

## Key functions

| Function | Role |
|----------|------|
| `load_all_configs` (`config_loader.py`) | Load five YAML files into `AstroConfig`. |
| `setup_logging` / `get_logger` (`logger.py`) | Configure root logging; module loggers. |
| `log_extra` | JSON-ish structured log line helper. |
| `create_llm_client` (`llm/factory.py`) | Provider dispatch → client with `.get_llm()`. |

## Key classes

| Class | Role |
|-------|------|
| `AstroConfig` | Dataclass with `data_root_path(cwd)`. |

## Subpackage `utils/llm/`

| Module | Role |
|--------|------|
| `openai_client.py`, `anthropic_client.py`, `google_client.py` | Provider implementations. |
| `base_client.py`, `validators.py` | Shared contracts. |
