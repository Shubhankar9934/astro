# Contribution

## Expectations

- **Code-grounded changes** — Tests or API behavior should match documented endpoints; update `docs/` when public contracts change.
- **Minimal scope** — Prefer focused PRs over wide refactors unless agreed.
- **Style** — Follow existing patterns: type hints, `from __future__ import annotations` where used in module, Pydantic v2 models for API bodies.

## Local workflow

```bash
pip install -e ".[dev]"
python -m pytest tests/ -q
```

## Documentation

- Run `mkdocs build` before publishing doc changes.
- Keep [api/endpoints.md](../api/endpoints.md) aligned with `astro/api/routes/*.py`.

## Licensing / legal

No license file is referenced in this guide; add project policy at repository root as appropriate.
