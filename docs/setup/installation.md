# Installation

## Prerequisites

- **Python 3.10+** (`requires-python` in `pyproject.toml`)
- **Project root** — the directory containing `pyproject.toml` (paths for `data/` and `models/checkpoints/` assume a consistent working directory when running scripts and the API)

## Editable install (recommended)

```bash
cd /path/to/astro
pip install -e .
```

## Optional extras

| Extra | Command | Provides |
|-------|---------|----------|
| IBKR | `pip install -e ".[ibkr]"` | `ib_async` |
| API server | `pip install -e ".[api]"` | `fastapi`, `uvicorn` |
| Training | `pip install -e ".[train]"` | `torch` |
| Dev / tests | `pip install -e ".[dev]"` | `pytest`, `httpx`, FastAPI stack |
| Vector DB | `pip install -e ".[vectordb]"` | `chromadb` |
| Documentation site | `pip install -e ".[docs]"` | MkDocs Material (see below) |

## Documentation tooling

Either:

```bash
pip install -e ".[docs]"
```

or:

```bash
pip install -r requirements-docs.txt
```

Then:

```bash
mkdocs serve
```

Build static HTML:

```bash
mkdocs build
```

Output directory: `site/` (gitignored by convention).

## Environment file

Copy or create `.env` in the project root for API keys and toggles. The FastAPI app attempts `python-dotenv` load from project root when installed (`astro/api/app.py`). Typical variables are listed in [Configuration](configuration.md).

## Verify

```bash
python -m pytest tests/ -q
```

API smoke tests require the `[dev]` / FastAPI stack.

## Reference

- **`README.md`** at the repository root — short quick start  
- **`astro_project.md`** at the repository root — monolithic technical overview
