# HTTP endpoints

Source: `astro/api/routes/*.py`, `astro/api/schemas/requests.py`. **Rate limits:** none (see [overview](overview.md)).

## How to read this reference

Each endpoint below follows the same intent:

| Block | What it answers |
|-------|-----------------|
| **When to use** | Operational or integration scenarios—when this call is the right tool. |
| **What happens internally** | The main Python path (files opened, classes invoked)—so logs and stack traces map to code. |
| **Purpose / schema / errors** | Contract details aligned with FastAPI and Pydantic. |

For response fields not fully expanded here, use the running server’s **OpenAPI** at `/docs` or `/redoc`.

---

## System

### `GET /api/v1/system/health`

| | |
|--|--|
| **Purpose** | Liveness and subsystem status |
| **Request** | None |
| **Response** | JSON: `status`, `ibkr_connected`, `ibkr_connect_error`, `model_loaded`, nested `model` object from `model_inference_status` |

**When to use:** Load-balancer probes, dashboards, or **pre-flight checks** before running expensive decisions—confirm model artifacts exist and whether a shared IBKR session is connected.

**What happens internally:** `get_config()` loads cached YAML; IBKR status comes from `request.app.state.ibkr_client` if lifespan connected it, else an optional one-off probe when `ASTRO_HEALTH_CHECK_IBKR=1`. Model fields come from `model_inference_status(ROOT)` (`astro/services/model_readiness.py`).

**`ibkr_connected`:** `True`/`False`/`null` — if `app.state.ibkr_client` exists, uses `ib.isConnected()`; else if `ASTRO_HEALTH_CHECK_IBKR=1`, performs one-off connect probe; otherwise may be `null`.

**Example (shape):**

```json
{
  "status": "ok",
  "ibkr_connected": null,
  "ibkr_connect_error": null,
  "model_loaded": false,
  "model": {
    "checkpoint_exists": false,
    "scaler_exists": false,
    "inference_loadable": false,
    "inference_ready": false,
    "inference_smoke_ok": false,
    "load_error": null,
    "schema_id": "fused_v1"
  }
}
```

| Status | Condition |
|--------|-----------|
| 200 | Always on success |

---

### `GET /api/v1/system/config`

| | |
|--|--|
| **Purpose** | Return merged YAML config (secrets stripped from `ibkr`) |
| **Request** | None |
| **Response** | `{ "system", "agents", "model", "risk", "ibkr" }` — keys containing `password` (case-insensitive) removed from `ibkr` |

**When to use:** Debugging “why did the system behave this way?” without SSH—inspect effective analysts, governance block, model `schema_id`, risk caps, and IBKR host/port (but not secrets).

**What happens internally:** `get_config()` returns the in-memory `AstroConfig`; the route clones dicts and filters `ibkr` keys for substring `password`.

| Status | Condition |
|--------|-----------|
| 200 | Success |

---

## Data

### `GET /api/v1/data/features`

| | |
|--|--|
| **Purpose** | Latest fused feature row as a dict |
| **Query** | `symbol` (required), `timeframe` (default `1d`) |

**When to use:** Quick sanity check that **fused Parquet exists** and the latest row is non-empty—often before calling `/decision/run` or `/model/predict`.

**What happens internally:** `get_feature_service()` → `FeatureService.latest_feature_row(symbol)` resolves `{data_root}/features/{symbol}_fused.parquet` via `AstroConfig.data_root_path(ROOT)`.

**Response:**

```json
{
  "symbol": "SPY",
  "timeframe": "1d",
  "features": { "...": "column_value_map" }
}
```

| Status | Condition |
|--------|-----------|
| 404 | `FileNotFoundError` from `FeatureService.latest_feature_row` |
| 422 | Missing/invalid query params |

---

### `GET /api/v1/data/market`

| | |
|--|--|
| **Purpose** | Last 20 rows of fused frame as JSON records |
| **Query** | `symbol` (required) |

**When to use:** UI sparklines, support tickets, or verifying **recent bar history** after an ingestion job—more context than a single latest row.

**What happens internally:** `FeatureService.load_fused(symbol)`, tail 20, datetime columns coerced to ISO strings for JSON safety.

**Response:**

```json
{
  "symbol": "SPY",
  "bars": [ { "...": "..." } ]
}
```

| Status | Condition |
|--------|-----------|
| 404 | Fused file not found |
| 422 | Missing `symbol` |

---

## Model

### `POST /api/v1/model/predict`

| | |
|--|--|
| **Purpose** | Run transformer inference on latest window from fused Parquet |
| **Body** | `PredictRequest` |

**When to use:** **Isolated model scoring** without paying for LLM rounds—good for dashboards, gating downstream jobs, or comparing model output to a full decision narrative.

**What happens internally:** Resolve fused path → `load_inference_optional(ROOT/best.pt, scaler)` → `TransformerInference.predict_latest_from_parquet` with `seq_len` from `model.yaml`. Marks **degenerate** when `p_up` is near 0.5 and uncertainty is very high.

**Request schema (`PredictRequest`):**

| Field | Type | Required |
|-------|------|----------|
| `symbol` | string | yes |

**Response (200):**

```json
{
  "prediction": {
    "p_up": 0.52,
    "uncertainty": 0.41,
    "direction": "UP",
    "degenerate": false
  },
  "model_version": "best.pt",
  "schema_id": "fused_v1"
}
```

| Status | Condition |
|--------|-----------|
| 404 | Fused features not found for symbol |
| 503 | Checkpoint or scaler missing (`load_inference_optional` returns `None`) |
| 422 | Invalid body |

---

## Agents

### `POST /api/v1/agents/analysts`

| | |
|--|--|
| **Purpose** | Run analyst chain only |
| **Body** | `SymbolDateRequest` |

**When to use:** **Prompt engineering** and **data QA**—you get all analyst reports without research, trader, or risk spend.

**What happens internally:** `build_decision_context` (same as full decision) → `DecisionExecutor.run_analysts_only` → `_run_analysts` with `selected_analysts` from YAML.

| Field | Type | Required |
|-------|------|----------|
| `symbol` | string | yes |
| `trade_date` | string | yes |

**Response (200):**

```json
{
  "symbol": "SPY",
  "reports": {
    "technical": "...",
    "sentiment": "...",
    "news": "...",
    "fundamentals": "...",
    "macro": "..."
  }
}
```

---

### `POST /api/v1/agents/research`

| | |
|--|--|
| **Purpose** | Analysts + bull/bear research debate + synthesizer |
| **Body** | `SymbolDateRequest` |

**When to use:** Evaluating **investment thesis quality** before enabling automated trading—surfaces bull/bear tension and synthesized plan.

**What happens internally:** Full analysts → `_research_debate(skip=False)` with bull/bear loop bounded by `max_debate_rounds` → synthesizer patch updates `investment_plan`.

**Response (200):** `symbol`, `bull_history`, `bear_history`, `final_summary`

---

### `POST /api/v1/agents/risk`

| | |
|--|--|
| **Purpose** | Risk cycle only from supplied reports |
| **Body** | `RiskRequest` |

**When to use:** You already have analyst output from **another system** or an edited pipeline and only need Astro’s **risk debate + judge** narrative.

**What happens internally:** Builds `AstroState` from JSON (including optional `astro_context` dict) → `_risk_cycle(fast=False)` → returns `risk_summary` and debate `raw` history. Exceptions become **400** with string detail.

| Field | Type | Required |
|-------|------|----------|
| `company_of_interest` | string | yes |
| `trade_date` | string | yes |
| `market_report` | string | no (default `""`) |
| `sentiment_report` | string | no |
| `news_report` | string | no |
| `fundamentals_report` | string | no |
| `investment_plan` | string | no |
| `trader_investment_plan` | string | no |
| `astro_context` | object or null | no |

**Response (200):** `risk_summary`, `raw`

| Status | Condition |
|--------|-----------|
| 400 | Exception inside `run_risk_only` (message as string detail) |
| 422 | Validation error |

---

## Decision

### `POST /api/v1/decision/run`

| | |
|--|--|
| **Purpose** | Full decision pipeline; persist decision row for replay |
| **Body** | `DecisionRequest` |

**When to use:** **Production-style** “what should we do on this symbol/date?”—this is the heaviest, most complete path and the one that writes **SQLite** + returns **`decision_id`** for replay.

**What happens internally:** Build context (with optional inference + portfolio staleness hints) → **governance pre-check** (strict + missing model → **503**) → `DecisionExecutor.run` → `MetadataDB.insert_decision` → large JSON response with snippets, governance metadata, sizing, and validation flags.

| Field | Type | Required |
|-------|------|----------|
| `symbol` | string | yes |
| `trade_date` | string | yes |
| `mode` | `"fast"` \| `"full"` | no — defaults to `decision_mode_default` in `agents.yaml` |

**Governance (strict):** If `model_missing_would_violate_governance` and `resolve_governance_mode` is **`strict`**, returns **503** before calling the executor:

```json
{
  "detail": {
    "error": "model_required",
    "message": "Model inference is required by model_governance but no prediction was produced.",
    "model_predict_error": null,
    "governance_mode": "strict",
    "hint": "Ensure models/checkpoints/best.pt and scaler.npz exist and fused features match the trained schema. Or set governance_mode: degraded|dev or ASTRO_GOVERNANCE_MODE."
  }
}
```

**Response (200)** — abbreviated; see OpenAPI for full shape:

- `decision_id`, `symbol`, `decision` (signal string)
- `governance_mode`, `degraded`, `degraded_reason`, `dev_model_bypass`
- `governance`, `suggested_size_usd`, `sizing`, `model_output`, `model_predict_error`
- `analyst_summary`, `structured_market_facts`, `research_summary`, `risk_summary`
- `schema_validation`, `positions_max_updated_at`, `portfolio_state_stale`

| Status | Condition |
|--------|-----------|
| 503 | Strict governance + missing model prediction |
| 422 | Invalid body |

---

## Backtest

### `POST /api/v1/backtest/run`

| | |
|--|--|
| **Purpose** | Simple signal backtest on a fused Parquet file |
| **Body** | `BacktestRequest` |

**When to use:** **Offline evaluation** of a numeric column (e.g. sentiment or a model score) as a trading signal—does not call LLMs.

**What happens internally:** `FeatureService.load_fused` with path resolved relative to `ROOT` if not absolute → schema validation → `run_signal_backtest` → Sharpe / max drawdown / trade count.

| Field | Type | Default |
|-------|------|---------|
| `fused_path` | string | required |
| `signal_col` | string | `sentiment_score` |
| `symbol` | string | `TEST` |

**Response (200):**

```json
{
  "sharpe": 0.0,
  "max_drawdown": 0.0,
  "n_trades": 0
}
```

| Status | Condition |
|--------|-----------|
| 404 | File not found |
| 400 | Schema validation failed (errors joined) or missing `signal_col` handling |
| 422 | Invalid body |

---

## Execution

### `POST /api/v1/execution/order`

| | |
|--|--|
| **Purpose** | Submit idempotent market order via IBKR (paper required) |
| **Headers** | `X-API-Key: <value>` **if** `ASTRO_API_KEY` env is set |
| **Body** | `ExecutionOrderRequest` |

**When to use:** **Acting** on a decision (or manual ops) through IBKR—this is intentionally separated from `/decision/run` so policy can review before capital moves.

**What happens internally:** Optional API key dependency → enforce `ibkr.paper` → reuse `app.state.ibkr_client` or create ephemeral `IBKRClient` → `OrderManager.submit_market` with SQLite idempotency; broker errors surface as **503**.

| Field | Type | Constraints |
|-------|------|-------------|
| `symbol` | string | required |
| `action` | `"BUY"` \| `"SELL"` | required |
| `quantity` | number | required |
| `idempotency_key` | string | min length **4** |

**Response (200):**

```json
{ "status": "submitted", "trade": "..." }
```

or duplicate:

```json
{ "status": "duplicate", "idempotency_key": "order-20240601-001" }
```

| Status | Condition |
|--------|-----------|
| 401 | `ASTRO_API_KEY` set and header missing/wrong |
| 403 | `ibkr.paper` not `true` |
| 503 | Execution exception (detail: `Execution failed: ...`) |
| 422 | Validation error |

---

## Replay

### `GET /api/v1/replay`

| | |
|--|--|
| **Purpose** | Fetch prior decision from SQLite or JSON log file |
| **Query** | One of: `decision_id` (int), `log_file` (string); optional `recompute` (bool) |

**When to use:** **Audit**, support, or building training datasets from historical runs—retrieve exactly what was stored without re-invoking LLMs.

**What happens internally:** SQLite lookup by id **or** read JSON from `decision_logs` under `data_root`; `recompute=true` short-circuits to **501**. Non-finite floats sanitized for JSON (`replay.py`).

| Status | Condition |
|--------|-----------|
| 200 | `source`: `database` or `file`, `record`: payload |
| 400 | Neither `decision_id` nor `log_file` |
| 404 | Decision or file not found |
| 501 | `recompute=true` (not implemented) |

---

## Experiments

### `POST /api/v1/experiments/log`

| | |
|--|--|
| **Purpose** | Log experiment metadata to SQLite |
| **Body** | `ExperimentLogRequest` |

**When to use:** Track **hyperparameter trials**, prompt versions, or offline benchmarks alongside `model_version` / `schema_id` for later SQL queries.

**What happens internally:** `MetadataDB.log_experiment` → returns new `experiment_id`.

| Field | Type | Default |
|-------|------|---------|
| `model_version` | string | required |
| `schema_id` | string | `fused_v1` |
| `payload` | object | `{}` |

**Response (200):**

```json
{ "experiment_id": 1, "status": "logged" }
```

---

## WebSocket

### `WS /ws/stream`

| | |
|--|--|
| **Purpose** | Periodic JSON heartbeat (no market stream) |
| **Handshake** | Standard WebSocket upgrade |
| **Server messages** | Every ~5s: `{"type":"heartbeat","payload":{}}` |

**When to use:** Verify **connectivity** through proxies/firewalls or keep a lightweight channel open for future extensions—**not** a substitute for market data feeds today.

**What happens internally:** Accept socket → infinite loop with `asyncio.sleep(5)` → send JSON text; exits cleanly on `WebSocketDisconnect`.

Disconnect is handled silently on client close.

---

## Quick reference table

| Method | Path |
|--------|------|
| GET | `/api/v1/system/health` |
| GET | `/api/v1/system/config` |
| GET | `/api/v1/data/features` |
| GET | `/api/v1/data/market` |
| POST | `/api/v1/model/predict` |
| POST | `/api/v1/agents/analysts` |
| POST | `/api/v1/agents/research` |
| POST | `/api/v1/agents/risk` |
| POST | `/api/v1/decision/run` |
| POST | `/api/v1/backtest/run` |
| POST | `/api/v1/execution/order` |
| GET | `/api/v1/replay` |
| POST | `/api/v1/experiments/log` |
| WS | `/ws/stream` |
