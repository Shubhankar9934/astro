# Deployment

## Container images and CI

**Dockerfile, docker-compose, and GitHub Actions (or other CI) workflows are not available in the current repository.** Operators must supply their own images and pipelines if containerized or automated deployment is required.

## Process-based deployment (supported pattern)

1. Install the package and extras on the host or VM: `pip install -e ".[api,ibkr]"` (plus `[train]` only on training nodes).
2. Place configuration under `astro/configs/` or mount overrides and call `load_all_configs(override_path=...)` from custom entrypoints if needed (default code uses packaged YAML).
3. Set environment variables (see [Configuration](configuration.md)).
4. Run the API with a production ASGI server:

```bash
uvicorn astro.api.app:app --host 0.0.0.0 --port 8000 --workers 1
```

Use **`workers 1`** unless you refactor global singletons (`lru_cache` config, `app.state.ibkr_client`) for multi-worker layouts.

5. Put a reverse proxy (nginx, Envoy, AWS ALB, etc.) in front for TLS termination and routing.

## Health checks

- **Liveness:** `GET /api/v1/system/health` — returns `status: ok` and subsystem flags.
- **Readiness:** Combine `model.inference_loadable` and your own checks for fused data presence; not a separate Kubernetes-style probe in code.

## Data and SQLite

- Mount a persistent volume for **`data_root`** (`data/` by default) so `astro_meta.sqlite` and `decision_logs` survive restarts.
- Single-writer assumptions: concurrent API processes writing the same SQLite file without WAL/locking strategy may corrupt data—use one writer or externalize the database.

## IBKR

- Gateway/TWS must be reachable from the API host; firewall rules for `ibkr.port`.
- Optional skip connect: `ASTRO_SKIP_IBKR_CONNECT` for environments without broker access.

## Static documentation site

Build with `mkdocs build` and serve `site/` from any static host, or run `mkdocs serve` for internal previews only.

### GitHub Pages (this repository)

The workflow **Deploy documentation** pushes the built site to the **`gh-pages`** branch. In the repo **Settings → Pages → Build and deployment**, set **Source** to **Deploy from a branch**, branch **`gh-pages`**, folder **`/` (root)**, then save. If **Source** is left on **GitHub Actions** while using this workflow, the default `github.io/<repo>/` URL stays empty (404) because GitHub will not publish the `gh-pages` branch. On GitHub, switch the branch dropdown to **`gh-pages`** and confirm **`index.html`** exists at the root of that branch.

## Security hardening (operational)

- Restrict CORS in `astro/api/app.py` for production.
- Set `ASTRO_API_KEY` for execution routes if the API is exposed.
- Keep `ibkr.paper: true` until live trading is explicitly approved and code gates are revisited.
