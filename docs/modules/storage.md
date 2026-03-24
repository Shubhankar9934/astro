# Module: `astro.storage`

## Why this module exists

Decisions, orders, positions, and experiments need **durable** storage without mandating Postgres for small deployments. SQLite provides a pragmatic default with clear upgrade pressure at scale.

## Where it fits

Written by **API decision + execution** paths; read by **replay**, **exposure**, and **constraints**.

## If it fails

Locked DB or corruption blocks inserts—run single writer or externalize DB. Missing tables indicate migration/setup gap (see `database.py` initialization paths).

## Overview

| | |
|--|--|
| **Purpose** | Persistent metadata and optional vector storage. |
| **Responsibilities** | SQLite schema for decisions, orders, positions, experiments; helpers for API and execution. |
| **Dependencies** | Standard library `sqlite3` (via Python). |

## Key classes

| Class | Role |
|-------|------|
| `MetadataDB` (`database.py`) | CRUD for operational records; context manager friendly `close()`. |

## Key functions

| Function | Role |
|----------|------|
| Vector store wrappers (`vector_store.py`) | Optional Chroma / embedding workflows when `[vectordb]` installed. |
