# Module: `astro.ingestion`

## Why this module exists

Market and alt data enter the system somewhere noisy—sockets, CSVs, JSONL. Ingestion isolates **I/O quirks** so pipelines see cleaner tables.

## Where it fits

Upstream of **pipelines** and beside **execution** (shared IBKR client patterns). Optional dependency `ib_async` for broker paths.

## If it fails

Stale or partial bars poison features—monitor scheduler and Gateway connectivity before tuning models.

## Overview

| | |
|--|--|
| **Purpose** | Acquire raw or semi-structured market and alt-data inputs for pipelines. |
| **Responsibilities** | IBKR connect, historical fetch, streaming hooks, order execution helpers; news and sentiment streams; scheduler. |
| **Dependencies** | Optional `ib_async` (`[ibkr]` extra); `pandas`. |

## Key classes

| Class | Role |
|-------|------|
| `IBKRClient` (`ingestion/ibkr/client.py`) | Connection lifecycle, sync/async connect. |
| `IBKRConnectionConfig` | Parsed `ibkr.yaml`. |

## Key functions / modules

| Symbol | Role |
|--------|------|
| `historical_fetch.py` | CSV / interim OHLCV helpers. |
| `market_stream.py` | Streaming market data (IBKR). |
| `order_executor.py` | Lower-level order helpers (ingestion namespace). |
| `scheduler.py` | `IngestionScheduler` for live loops. |
| `news_stream.py`, `sentiment/social_stream.py` | Alternative data ingestion. |

## Related documentation

- `astro/ingestion/STREAMING.md` — streaming notes.
