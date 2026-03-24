#!/usr/bin/env python3
"""Train transformer on fused feature Parquet."""

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

from astro.utils.config_loader import load_all_configs
from astro.models.transformer.trainer import train


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--fused", type=Path, required=True, help="Fused features parquet")
    p.add_argument("--out", type=Path, default=ROOT / "models" / "checkpoints")
    args = p.parse_args()
    cfg = load_all_configs()
    model_cfg = dict(cfg.model)
    out = train(args.fused, args.out, model_cfg)
    print(f"Saved checkpoint to {out}")


if __name__ == "__main__":
    main()
