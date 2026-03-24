"""CLI: python -m astro.evaluation --fused PATH --epsilon 0.0

Exit 1 if model_governance Sharpe < buy_hold Sharpe - epsilon (optional gate).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Evaluation gate: model vs buy-and-hold Sharpe")
    p.add_argument("--fused", type=Path, required=True)
    p.add_argument("--checkpoint", type=Path, default=Path("models/checkpoints/best.pt"))
    p.add_argument("--scaler", type=Path, default=Path("models/checkpoints/scaler.npz"))
    p.add_argument("--seq-len", type=int, default=32)
    p.add_argument("--out-dir", type=Path, default=None, help="Write JSON report under this dir")
    p.add_argument("--epsilon", type=float, default=0.0, help="Required Sharpe edge vs buy_hold")
    p.add_argument("--root", type=Path, default=Path.cwd(), help="Project root for relative paths")
    args = p.parse_args()
    root = args.root.resolve()
    fused = args.fused if args.fused.is_absolute() else (root / args.fused)
    ckpt = args.checkpoint if args.checkpoint.is_absolute() else (root / args.checkpoint)
    scaler = args.scaler if args.scaler.is_absolute() else (root / args.scaler)
    out_dir = args.out_dir
    if out_dir and not out_dir.is_absolute():
        out_dir = root / out_dir

    from astro.evaluation.runner import run_evaluation_report

    rep = run_evaluation_report(
        fused,
        ckpt,
        scaler,
        seq_len=args.seq_len,
        out_dir=out_dir,
        cwd=root,
    )
    print(json.dumps(rep, indent=2, default=str))
    m_sh = rep["baselines"]["model_governance"]["sharpe"]
    bh_sh = rep["baselines"]["buy_hold"]["sharpe"]
    if m_sh < bh_sh - args.epsilon:
        print(
            f"GATE_FAIL: model_sharpe={m_sh:.4f} < buy_hold_sharpe={bh_sh:.4f} - epsilon={args.epsilon}",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
