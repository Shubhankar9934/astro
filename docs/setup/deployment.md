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

#### `https://mlwithshubh.me/astro/` (next to `/Socio_Sim_AI/`)

That URL is served by your **root GitHub Pages repository** (the one `mlwithshubh.me` uses—often **`username.github.io`**), not by this repo’s `gh-pages` branch alone.

If `/astro/` shows a long **“Project Astro – Technical Overview”** (plain text, no Material chrome), the folder still has **old markdown/README** (or a partial deploy). The workflow must push the full **`mkdocs build`** output into **`astro/`** on that root repo, and **replace** everything under `astro/` each time.

In **this** (`astro`) repository:

1. **PAT** with **Contents: Read and write** on the **site** repo (e.g. `Shubhankar9934.github.io`—use your real repo name).
2. **Settings → Secrets → Actions** → **`GH_PAGES_DEPLOY_TOKEN`** = that PAT.
3. Optional **Variables**: **`PAGES_ROOT_REPO`**, **`PAGES_ROOT_BRANCH`** if not `Shubhankar9934/Shubhankar9934.github.io` / `main`.

The workflow uses [peaceiris/actions-gh-pages](https://github.com/peaceiris/actions-gh-pages) with **`destination_dir: astro`**. With **`keep_files` left at default (false)** peaceiris **removes existing files only under `astro/`**, then copies `./site`—sibling folders like **`Socio_Sim_AI/`** stay. Do **not** set `keep_files: true` for this layout or old `README.md` / markdown can remain and override what you expect to see.

After a green **Deploy documentation** run, open **`https://mlwithshubh.me/astro/`** in a private window; **`site_url`** in `mkdocs.yml` should stay **`https://mlwithshubh.me/astro/`**.

See GitHub’s [custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site) docs for apex DNS if needed.

## Security hardening (operational)

- Restrict CORS in `astro/api/app.py` for production.
- Set `ASTRO_API_KEY` for execution routes if the API is exposed.
- Keep `ibkr.paper: true` until live trading is explicitly approved and code gates are revisited.
