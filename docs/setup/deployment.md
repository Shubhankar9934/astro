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

#### Default: only this repo (`github.io/<repo>/`)

If you do **not** set the variable below, the workflow pushes the MkDocs build to this repository’s **`gh-pages`** branch. Then use **Settings → Pages → Source: Deploy from a branch → `gh-pages` → `/`**.

#### `https://mlwithshubh.me/astro/` (folder next to `/Socio_Sim_AI/`)

That URL is served by your **root GitHub Pages repository** (the one `mlwithshubh.me` points at—often **`username.github.io`**), not by this `astro` repo alone. If `/astro/` shows a **README** instead of the **Material** MkDocs UI, the folder only has markdown/README content; you need to deploy the **`mkdocs build`** output (`site/`) **into** that repo under **`astro/`**.

In **this** (`astro`) repository:

1. Create a **PAT** (classic *or* fine-grained) with **Contents: Read and write** on the **root site** repo (e.g. `Shubhankar9934.github.io`—name must match yours).
2. **Settings → Secrets and variables → Actions → New repository secret** → `GH_PAGES_DEPLOY_TOKEN` = the PAT.
3. **Settings → Secrets and variables → Actions → Variables → New repository variable** → `PUBLISH_TO_PAGES_ROOT` = `true`.
4. Optional variables: `PAGES_ROOT_REPO` (default `Shubhankar9934/Shubhankar9934.github.io`), `PAGES_ROOT_BRANCH` (default `main`) if your site repo name or default branch differs.

The workflow uses [peaceiris/actions-gh-pages](https://github.com/peaceiris/actions-gh-pages) with **`destination_dir: astro`** and **`keep_files: true`** so other paths (e.g. **`/Socio_Sim_AI/`**) are not deleted. After a green **Deploy documentation** run, **`https://mlwithshubh.me/astro/`** should show the full MkDocs site; **`site_url`** in `mkdocs.yml` must stay **`https://mlwithshubh.me/astro/`** so CSS and links resolve.

See GitHub’s [custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site) docs if DNS for the apex domain is not already configured.

## Security hardening (operational)

- Restrict CORS in `astro/api/app.py` for production.
- Set `ASTRO_API_KEY` for execution routes if the API is exposed.
- Keep `ibkr.paper: true` until live trading is explicitly approved and code gates are revisited.
