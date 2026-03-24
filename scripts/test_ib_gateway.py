#!/usr/bin/env python3
"""Test IB Gateway: (1) async path same as FastAPI lifespan, (2) optional sync ib.connect() like a plain script.

Run from project root with venv active:

    python scripts/test_ib_gateway.py
    python scripts/test_ib_gateway.py --sync
    python scripts/test_ib_gateway.py --host 127.0.0.1 --port 4001 --client-id 101

ASTRO_IBKR_DEBUG=1 enables ib_async wire logging.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from astro.ingestion.ibkr.client import IBKRClient, IBKRConnectionConfig
from astro.utils.config_loader import load_all_configs


def _merge_cli(base: dict, args: argparse.Namespace) -> dict:
    d = dict(base)
    if args.host is not None:
        d["host"] = args.host
    if args.port is not None:
        d["port"] = args.port
    if args.client_id is not None:
        d["client_id"] = args.client_id
    if args.timeout is not None:
        d["connect_timeout"] = args.timeout
    if args.read_only:
        d["read_only"] = True
    return d


async def _run_async(ic: IBKRConnectionConfig) -> int:
    client = IBKRClient(ic)
    try:
        ib = await client.connect_async()
        accounts = ib.client.getAccounts() if ib.client.isReady() else []
        print("OK (async / API lifespan path): connected", flush=True)
        print(f"    host={ic.host} port={ic.port} client_id={ic.client_id}", flush=True)
        print(f"    accounts={accounts}", flush=True)
        return 0
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr, flush=True)
        return 1
    finally:
        client.disconnect()


def _run_sync(ic: IBKRConnectionConfig) -> int:
    """Same as a standalone script: IB().connect(...) with no running asyncio loop."""
    try:
        from ib_async import IB  # type: ignore
    except ImportError as e:
        print(f"FAIL: install ib_async — {e}", file=sys.stderr, flush=True)
        return 1

    ib = IB()
    try:
        ib.connect(
            ic.host,
            ic.port,
            clientId=ic.client_id,
            timeout=ic.connect_timeout or 0,
            readonly=ic.read_only,
        )
        accounts = ib.client.getAccounts() if ib.client.isReady() else []
        print("OK (sync script path): connected", flush=True)
        print(f"    host={ic.host} port={ic.port} client_id={ic.client_id}", flush=True)
        print(f"    accounts={accounts}", flush=True)
        return 0
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr, flush=True)
        return 1
    finally:
        if ib.isConnected():
            ib.disconnect()


def main() -> None:
    p = argparse.ArgumentParser(description="Test IBKR Gateway (ib_async).")
    p.add_argument(
        "--sync",
        action="store_true",
        help="Use blocking ib.connect() (no asyncio; matches a minimal test script).",
    )
    p.add_argument("--host", default=None)
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--client-id", type=int, default=None)
    p.add_argument("--timeout", type=float, default=None)
    p.add_argument("--read-only", action="store_true")
    args = p.parse_args()

    cfg = load_all_configs()
    ic = IBKRConnectionConfig.from_dict(_merge_cli(cfg.ibkr, args))

    mode = "sync ib.connect()" if args.sync else "async connect_async() (FastAPI-style)"
    print(
        f"Trying [{mode}] {ic.host}:{ic.port} client_id={ic.client_id} "
        f"timeout={ic.connect_timeout or 'unlimited'}s ...",
        flush=True,
    )

    if args.sync:
        code = _run_sync(ic)
    else:
        code = asyncio.run(_run_async(ic))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
