#!/usr/bin/env python3
"""Run FastAPI with: python scripts/run_api.py"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    import uvicorn

    uvicorn.run("astro.api.app:app", host="0.0.0.0", port=8000, reload=False)
