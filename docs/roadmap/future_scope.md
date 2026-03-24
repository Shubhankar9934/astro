# Future scope

Items below are **not commitments**; they reflect gaps and stubs visible in the current codebase.

## Platform / DevOps

- **Docker / docker-compose** for API + optional Gateway sidecar  
- **CI** — lint, `pytest`, `mkdocs build` on pull requests  
- **Hosted docs** — GitHub Pages or internal portal from `mkdocs build`  
- **Rate limiting and auth** on all mutating routes, not only execution  

## Product / architecture

- **mkdocstrings** — Auto-generated Python API reference embedded in MkDocs  
- **Monitoring module** — Replace placeholders with metrics (Prometheus), tracing (OpenTelemetry), structured dashboards  
- **Ensemble models** — Implement `models/ensemble/aggregator.py` beyond stub  
- **Replay `recompute=true`** — Currently returns **501** (`replay.py`)  
- **WebSocket stream** — Extend beyond heartbeat to curated decision or quote events (requires design)  
- **Horizontal scaling** — Externalize SQLite; clarify IBKR session ownership per worker  

## Documentation polish

- Additional sequence diagrams for partial agent routes and backtest  
- Stripe-style “guides” split per user journey  
- Versioned docs (mike / material versioning) tied to releases  

## Governance and risk

- Richer policy UI and audit export  
- Stronger guarantees around live trading gates (beyond `paper` flag)  

When implementing any item, update this page and the relevant **Modules** / **API** sections so the site stays code-grounded.
