# Module: `astro.execution`

## Why this module exists

Capital movement must be **idempotent** and **explicit**. This module isolates broker calls and records outcomes so retries do not double-risk the book.

## Where it fits

After a **human or system** chooses to act; invoked from `api/routes/execution.py` and potentially scripts. Depends on `ingestion.ibkr` and `storage`.

## If it fails

Exceptions become HTTP **503** on the order route; idempotent duplicates return `status: duplicate`—design clients to retry safely with the same key.

## Overview

| | |
|--|--|
| **Purpose** | Broker-facing order submission and supporting utilities (slippage model, idempotent order manager). |
| **Responsibilities** | Execute market orders via `IBKRClient`; deduplicate by idempotency key; integrate with `MetadataDB`. |
| **Dependencies** | `ingestion.ibkr.client`, `storage.database`. |

## Key classes

| Class | Role |
|-------|------|
| `TradeExecutor` (`trade_executor.py`) | Wraps IBKR client for place-order operations. |
| `OrderManager` (`order_manager.py`) | Idempotent `submit_market` using SQLite backing. |

## Key functions

| Function | Role |
|----------|------|
| Slippage helpers (`slippage_model.py`) | Backtest / simulation adjustments. |
