#!/usr/bin/env python3
"""Start async ingestion + optional decision loop (requires TWS/Gateway + ib_async)."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import asyncio

from astro.ingestion.scheduler import default_scheduler
from astro.utils.config_loader import load_all_configs
from astro.utils.logger import get_logger, setup_logging

LOG = get_logger("astro.run_live")


async def main_async(symbol: str):
    cfg = load_all_configs()
    setup_logging(cfg.system.get("log_level", "INFO"))
    try:
        from ib_async import util  # type: ignore

        util.patchAsyncio()
    except Exception:
        pass

    async def on_bar(bar):
        LOG.info("bar %s %s", bar.symbol, bar.close)

    sched = default_scheduler(cfg.ibkr, symbol, on_bar=on_bar)
    await sched.run_stream_loop(symbol)


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="SPY")
    args = p.parse_args()
    asyncio.run(main_async(args.symbol))


if __name__ == "__main__":
    main()
