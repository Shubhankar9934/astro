---
name: MkDocs Enterprise Documentation
overview: |
  Execution-grade documentation pass for astro-trading: build `/docs` + root `mkdocs.yml` (Material, Mermaid) that is code-grounded—sourced from astro_project.md, README, astro/api/routes/*, decision_engine, configs, config_loader, and schemas. No hallucinated APIs, Docker, or CI. Module docs cover public/important interfaces only (~115 files not line-by-line). Optional later pass for mkdocstrings, doc CI, and Stripe-like polish.
todos:
  - id: step-understand
    content: STEP 1 — Re-read routes, schemas, decision_engine, governance_mode, lifecycle; confirm endpoint list vs code
    status: completed
  - id: step-split-overview-arch
    content: STEP 2–3 — Scaffold docs tree; split astro_project.md into overview/* + architecture/* (HLD, tech stack, scaling, fault tolerance, data lifecycle, Mermaid)
    status: completed
  - id: step-lld-design
    content: STEP 4 — design/* LLD (DecisionExecutor, context build, agents, governance, storage); class + sequence Mermaid
    status: completed
  - id: step-api-strict
    content: STEP 5 — api/* from routes + requests.py; per-endpoint path/method/schemas/examples/errors (401/422/503); X-API-Key; group by system/data/model/agents/decision/backtest/execution/replay/experiments/ws
    status: completed
  - id: step-modules-public
    content: STEP 6 — docs/modules/<pkg>.md per top-level astro/ package; overview + key classes/methods + key functions only
    status: completed
  - id: step-flows
    content: STEP 7 — architecture/data_flow.md + sequence_diagrams.md (offline train, pipelines, decision, API lifecycle)
    status: completed
  - id: step-setup-guides
    content: STEP 8–9 — setup/* (install, config, deployment — state Docker/CI not in repo); guides/* (dev, contribution, debugging/logger)
    status: completed
  - id: step-mkdocs-nav
    content: STEP 10 — mkdocs.yml Material (tabs, search, code copy, Mermaid); nav mirrors docs; docs deps extra or requirements-docs.txt
    status: completed
  - id: readme-roadmap
    content: index.md + roadmap/future_scope.md; README one-liner for mkdocs serve; cross-links OpenAPI + Postman
    status: completed
  - id: optional-refinement
    content: (Optional follow-up) More sequence diagrams, LLD depth, API edge cases, Stripe-like readability; mkdocstrings; doc CI
    status: cancelled
isProject: false
---

# Enterprise MkDocs documentation for astro-trading (execution-grade)

## Cursor SUPER PROMPT (authoritative execution brief)

You are a senior software architect and documentation engineer working on **astro-trading**.

**Primary goal:** Create a complete `docs/` structure plus root-level `mkdocs.yml` with **production-quality**, **code-accurate** content—derived only from the real codebase and existing artifacts. **Do not invent** endpoints, Dockerfiles, CI workflows, or features not present in the repository.

**Primary sources (mandatory grounding):**

- [astro_project.md](astro_project.md) — primary narrative to split into overview + architecture + design
- [README.md](README.md) — install and quick run
- `astro/api/routes/*.py` — HTTP surface
- `astro/api/schemas/requests.py` — request bodies
- `astro/decision_engine/`* — orchestration, policy, governance
- `astro/configs/*.yaml` — configuration contracts
- [astro/utils/config_loader.py](astro/utils/config_loader.py) — how config is loaded and paths resolve

**Required output layout:**

```text
docs/
├── index.md
├── overview/
├── architecture/
├── design/
├── api/
├── modules/
├── setup/
├── guides/
└── roadmap/
mkdocs.yml   # repository root
```

---

## Execution sequence (STEP 1–10)


| Step   | Action                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1**  | **Understand system:** pipeline + agents + decision engine; data lifecycle raw → features → fused → decision; FastAPI layer; governance **503** (`model_required`) when strict mode and model missing—verify in code ([decision.py](astro/api/routes/decision.py), [governance_mode.py](astro/decision_engine/governance_mode.py)).                                                                                                               |
| **2**  | **Split astro_project.md** into `overview/`*, `architecture/`*, `design/*`; upgrade tone to enterprise (AWS-level clarity), no fluff.                                                                                                                                                                                                                                                                                                             |
| **3**  | **HLD** in `architecture/hld.md`: ingestion, pipelines, features, models, agents, decision engine, API; tech stack table; scaling; fault tolerance; data lifecycle; Mermaid component diagram.                                                                                                                                                                                                                                                    |
| **4**  | **LLD** in `design/lld.md` + diagrams: DecisionExecutor deep dive, context building, agent orchestration, governance, storage; `design/class_diagrams.md` + `sequence_diagrams.md` (or keep sequence in `architecture/sequence_diagrams.md` per tree—**use existing plan paths**).                                                                                                                                                                |
| **5**  | **API docs (strict):** From `astro/api/routes/*.py` + schemas. For **each** endpoint: path, method, request schema, response shape, example JSON, errors (**401** auth, **422** validation, **503** model_required where applicable), notes (**X-API-Key** when `ASTRO_API_KEY` set). **Group:** system, data, model, agents, decision, backtest, execution, replay, experiments, websocket. **Rate limits:** state N/A unless middleware exists. |
| **6**  | **Modules:** `docs/modules/<module>.md` for each **top-level** package under `astro/`. Sections: **Module overview** (purpose, responsibilities, dependencies); **Key classes** (name, role, important methods); **Key functions** (signature, description, I/O). **Do not** document every trivial helper—**public / important interfaces only**.                                                                                                |
| **7**  | **Flows:** `architecture/data_flow.md` (offline training, feature pipeline, decision execution); `architecture/sequence_diagrams.md` (decision run, API request lifecycle)—Mermaid.                                                                                                                                                                                                                                                               |
| **8**  | **Setup:** `setup/installation.md`, `configuration.md`, `deployment.md` from README + configs. **If Docker/CI absent:** explicit sentence — *"Not available in the current repository."* — plus process deployment (uvicorn, env, reverse proxy sketch).                                                                                                                                                                                          |
| **9**  | **Guides:** `developer_guide.md`, `contribution.md`, `debugging.md` — logging via [utils/logger.py](astro/utils/logger.py); common failures (missing fused Parquet, checkpoints, LLM keys, IBKR, governance 503); how to extend.                                                                                                                                                                                                                  |
| **10** | **mkdocs.yml:** theme `material`; navigation **tabs**; **search**; **content.code.copy**; **Mermaid**; full **nav** matching `docs/` tree; add docs dependencies (`pyproject` `[docs]` extra or `requirements-docs.txt`).                                                                                                                                                                                                                         |


---

## Quality rules (anti-hallucination)

- **No** fabricated APIs, env vars, or behaviors—verify against files.
- **Prefer tables** over long prose where listing options, endpoints, or config keys.
- **Use Mermaid** for architecture, data flow, and sequences; follow Mermaid-safe IDs (no spaces in node IDs; quote labels with special characters; no custom `style` fills).
- **Cross-link** runtime OpenAPI (`/docs`, `/redoc`) from `docs/api/overview.md`.
- **Reference** [postman/Astro_Trading_API.postman_collection.json](postman/Astro_Trading_API.postman_collection.json) when present.
- **Call out limitations** honestly (IBKR singleton, CWD-relative paths, stubs in monitoring/ensemble).

---

## Optional follow-up (not in initial deliverable)

- Refinement pass: more sequence diagrams, stronger decision-engine LLD, API edge cases, readability (e.g. Stripe-like structure).
- **mkdocstrings** for auto-generated Python reference.
- Doc **CI** (e.g. build + deploy to GitHub Pages) when desired.

---

## Codebase snapshot (documentation inputs)

- **Product:** `[astro-trading](pyproject.toml)` (`astro` import root)—ingestion → pipelines → fused Parquet → optional transformer → LLM agents → `DecisionExecutor` → SQLite / logs; optional FastAPI in [astro/api/app.py](astro/api/app.py).
- **Canonical narrative:** [astro_project.md](astro_project.md) — split, refine, deduplicate into the tree above.
- **API surface (verify in code before documenting):**
  - `GET /api/v1/system/health`, `GET /api/v1/system/config` — [system.py](astro/api/routes/system.py)
  - `GET /api/v1/data/features`, `GET /api/v1/data/market` — [data.py](astro/api/routes/data.py)
  - `POST /api/v1/model/predict` — [model.py](astro/api/routes/model.py)
  - `POST /api/v1/agents/analysts`, `/research`, `/risk` — [agents.py](astro/api/routes/agents.py)
  - `POST /api/v1/decision/run` — [decision.py](astro/api/routes/decision.py) (**503** `model_required` strict governance)
  - `POST /api/v1/backtest/run` — [backtest.py](astro/api/routes/backtest.py)
  - `POST /api/v1/execution/order` — [execution.py](astro/api/routes/execution.py); optional `X-API-Key` — [dependencies.py](astro/api/dependencies.py)
  - `GET /api/v1/replay` — [replay.py](astro/api/routes/replay.py)
  - `POST /api/v1/experiments/log` — [experiments.py](astro/api/routes/experiments.py)
  - `WebSocket /ws/stream` — [stream.py](astro/api/routes/stream.py)
- **Request schemas:** [astro/api/schemas/requests.py](astro/api/schemas/requests.py)
- **Deployment reality:** No Dockerfile / docker-compose / `.github/workflows` in repo — state explicitly in deployment doc.

---

## Deliverables (file-level)

- [docs/index.md](docs/index.md) — landing, doc map, OpenAPI + Postman links, governance highlights.
- [docs/overview/](docs/overview/) — `vision.md`, `goals.md`, `problem_statement.md`
- [docs/architecture/](docs/architecture/) — `hld.md`, `system_design.md`, `data_flow.md`, `sequence_diagrams.md`
- [docs/design/](docs/design/) — `lld.md`, `module_breakdown.md`, `class_diagrams.md`, `design_patterns.md`
- [docs/api/](docs/api/) — `overview.md`, `endpoints.md`
- [docs/modules/](docs/modules/) — one `.md` per top-level `astro/` package: `agents`, `api`, `backtesting`, `configs`, `decision_engine`, `evaluation`, `execution`, `features`, `ingestion`, `models`, `monitoring`, `pipelines`, `services`, `storage`, `utils`
- [docs/setup/](docs/setup/) — `installation.md`, `configuration.md`, `deployment.md`
- [docs/guides/](docs/guides/) — `developer_guide.md`, `contribution.md`, `debugging.md`
- [docs/roadmap/future_scope.md](docs/roadmap/future_scope.md)
- **Root** [mkdocs.yml](mkdocs.yml) + docs dependency story

## Relationship to existing docs

- Keep [README.md](README.md) as quick start; add minimal pointer to `mkdocs serve` / `mkdocs build`.
- [astro_project.md](astro_project.md): optional later one-line redirect to `docs/` (separate micro-change if wanted).

## Diagrams (Mermaid)

No spaces in node IDs; use `camelCase` or underscores; quote edge labels with parentheses; avoid reserved IDs like `end`; no theme-breaking `style` blocks.