"""FastAPI lifespan: IBKR connect on startup (shared client); disconnect on shutdown."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from astro.ingestion.ibkr.client import describe_ibkr_connect_failure

log = logging.getLogger(__name__)


async def _try_connect_ibkr(app: FastAPI) -> None:
    app.state.ibkr_client = None
    app.state.ibkr_connect_error = None

    if os.environ.get("ASTRO_SKIP_IBKR_CONNECT", "").lower() in ("1", "true", "yes"):
        log.info("IBKR startup connect skipped (ASTRO_SKIP_IBKR_CONNECT)")
        return

    ic = None
    try:
        from astro.api.dependencies import get_config_cached
        from astro.ingestion.ibkr.client import (
            IBKRClient,
            IBKRConnectionConfig,
            IBKRNotInstalledError,
        )

        cfg = get_config_cached()
        ic = IBKRConnectionConfig.from_dict(cfg.ibkr)
        client = IBKRClient(ic)
        # Sync IB.connect() uses util.run() and breaks inside uvicorn's running loop (esp. Windows).
        await client.connect_async()
        app.state.ibkr_client = client
        log.info("IBKR connected at startup (%s:%s client_id=%s)", ic.host, ic.port, ic.client_id)
    except IBKRNotInstalledError as e:
        log.warning("IBKR unavailable (install ib_async): %s", e)
        app.state.ibkr_connect_error = str(e)
    except Exception as e:
        msg = (
            describe_ibkr_connect_failure(
                e,
                host=ic.host,
                port=ic.port,
                timeout_s=ic.connect_timeout,
            )
            if ic is not None
            else (str(e) or repr(e))
        )
        app.state.ibkr_connect_error = msg
        log.warning("IBKR connect at startup failed (API still up): %s", msg)


def _disconnect_ibkr(app: FastAPI) -> None:
    client = getattr(app.state, "ibkr_client", None)
    if client is None:
        return
    try:
        client.disconnect()
        log.info("IBKR disconnected on shutdown")
    except Exception as e:
        log.warning("IBKR disconnect error: %s", e)
    finally:
        app.state.ibkr_client = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await _try_connect_ibkr(app)
    yield
    _disconnect_ibkr(app)
