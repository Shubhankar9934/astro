# Configuration

## YAML (`astro/configs/`)

Loaded by `astro.utils.config_loader.load_all_configs()` from the **package** directory `astro/configs/` unless `override_path` is passed.

### `system.yaml`

| Key | Meaning |
|-----|---------|
| `timezone` | Display / scheduling default |
| `default_timeframe` | e.g. `1d` |
| `decision_debounce_seconds` | Hint for live loops |
| `max_llm_rounds_fast` | Fast-mode LLM cap hint |
| `log_level` | e.g. `INFO` |
| `data_root` | Root for `data/` tree (relative → resolved against **cwd** passed to `data_root_path`) |
| `feature_schema_version` | Logical version string |

### `agents.yaml` (selected keys)

| Key | Meaning |
|-----|---------|
| `selected_analysts` / `fast_mode_analysts` | Analyst keys for full vs fast paths |
| `max_debate_rounds` / `max_risk_discuss_rounds` | Loop limits |
| `decision_mode_default` | `fast` or `full` when API omits `mode` |
| `quick_think` / `deep_think` | `provider`, `model`, `temperature` |
| `model_governance` | `enabled`, `governance_mode`, `min_edge_for_directional`, `allow_llm_only_without_model`, `agents_can_override_direction`, … |
| `uncertainty_debate_threshold` | Upgrade fast→full when uncertainty high |
| `skip_debate_if_certain` / `uncertainty_certainty_max` | Skip bull/bear when model very certain |

### `model.yaml`

| Key | Meaning |
|-----|---------|
| `schema_id` | Must align with `features/schema_registry.json` |
| `seq_len`, `timeframe`, `feature_columns` | Model I/O |
| `d_model`, `n_heads`, `n_layers`, `dropout` | Architecture |
| `forward_horizon_bars`, `label` | Supervision |
| `batch_size`, `learning_rate`, `epochs` | Training |
| `checkpoint_dir`, `scaler_path` | Artifact locations (often relative to project root) |

### `risk.yaml`

| Key | Meaning |
|-----|---------|
| `max_position_fraction`, `max_concentration`, `max_gross_exposure_fraction` | Book limits |
| `max_daily_loss_fraction` | Policy placeholder |
| `default_slippage_bps` | Backtest |
| `portfolio_nav` | Sizing denominator |
| `positions_stale_warn_minutes` | API sets `portfolio_state_stale` when positions row age exceeds threshold |

### `ibkr.yaml`

| Key | Meaning |
|-----|---------|
| `host`, `port`, `client_id` | TWS / Gateway |
| `paper` | **Must be true** for `POST /execution/order` via API |
| `read_only`, `connect_timeout` | Connection behavior |

## Environment variables

| Variable | Role |
|----------|------|
| `OPENAI_API_KEY` | Default OpenAI stack |
| `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, … | Other providers in `utils/llm` |
| `ASTRO_API_KEY` | If set, `X-API-Key` required on `POST /api/v1/execution/order` |
| `ASTRO_SKIP_IBKR_CONNECT` | `1`/`true`/`yes` — skip IBKR connect on API startup |
| `ASTRO_HEALTH_CHECK_IBKR` | `1` — probe IBKR on `/health` when no shared client |
| `ASTRO_GOVERNANCE_MODE` | Overrides YAML `governance_mode`: `strict` \| `degraded` \| `dev` |
| `IBKR_USERNAME` / `IBKR_PASSWORD` | If using full auth (see comments in `ibkr.yaml`) |

## Path resolution

- **`data_root`:** Relative values join with **`cwd`** argument to `AstroConfig.data_root_path(cwd)`. API uses `ROOT` from `dependencies.py`.
- **Checkpoints:** API resolves `models/checkpoints/best.pt` and `scaler.npz` relative to **`ROOT`** (package parent’s parent from `api` module), not `data_root`.

See [System design](../architecture/system_design.md).
