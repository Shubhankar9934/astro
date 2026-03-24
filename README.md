# Astro Trading (`astro-trading`)

Self-contained package: install and run entirely from this directory.

```bash
cd astro
pip install -e .
pip install -e ".[ibkr]"   # optional: IB Gateway / TWS
pip install -e ".[api]"    # optional: FastAPI (included in default deps for server)
pip install -e ".[train]"  # optional: PyTorch
```

- **Documentation (MkDocs):** `pip install -e ".[docs]"` then `mkdocs serve` — site source in [docs/](docs/)
- **Monolithic overview:** [astro_project.md](astro_project.md)
- **API:** `python scripts/run_api.py` (loads `.env` from this folder)
- **Tests:** `python -m pytest tests/ -q`
- **Postman:** [postman/Astro_Trading_API.postman_collection.json](postman/Astro_Trading_API.postman_collection.json)

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` (and optional `ASTRO_API_KEY`, IBKR vars).

Data and checkpoints resolve from `system.yaml` `data_root` and `model.yaml` paths relative to the **current working directory** when you run scripts (usually this folder).
