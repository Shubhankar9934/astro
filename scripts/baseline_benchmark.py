#!/usr/bin/env python3
"""Train a simple sklearn logistic baseline on fused Parquet (next-day up label).

Requires: scikit-learn, pandas, pyarrow.
Writes JSON with train AUC / accuracy (sanity check vs transformer labels).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fused", type=Path, required=True)
    p.add_argument("--horizon", type=int, default=1, help="Forward return horizon bars for label")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, roc_auc_score
        from sklearn.model_selection import train_test_split
    except ImportError:
        print("Install scikit-learn: pip install scikit-learn", file=sys.stderr)
        raise SystemExit(1)

    df = pd.read_parquet(args.fused)
    if "close" not in df.columns and "Close" in df.columns:
        df = df.rename(columns={"Close": "close"})
    if "close" not in df.columns:
        raise SystemExit("Need close column for labels")
    close = pd.to_numeric(df["close"], errors="coerce")
    fwd = close.shift(-args.horizon) / close - 1.0
    y = (fwd > 0).astype(int).fillna(0).to_numpy()
    exclude = {"Date", "date", "open", "high", "low", "close", "volume"}
    num_cols = [
        c
        for c in df.columns
        if str(c) not in exclude and pd.api.types.is_numeric_dtype(df[c])
    ]
    if not num_cols:
        raise SystemExit("No numeric feature columns")
    X = df[num_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()
    n = min(len(X), len(y))
    X, y = X[:n], y[:n]
    if len(np.unique(y)) < 2:
        print(json.dumps({"error": "single_class", "n": n}))
        raise SystemExit(0)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, shuffle=False
    )
    clf = LogisticRegression(max_iter=500, class_weight="balanced")
    clf.fit(X_train, y_train)
    prob = clf.predict_proba(X_test)[:, 1]
    pred = (prob >= 0.5).astype(int)
    auc = float(roc_auc_score(y_test, prob))
    acc = float(accuracy_score(y_test, pred))
    rep = {
        "model": "sklearn_logistic",
        "n_total": n,
        "n_features": len(num_cols),
        "auc_holdout": auc,
        "accuracy_holdout": acc,
        "feature_sample": num_cols[:20],
    }
    print(json.dumps(rep, indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=2)


if __name__ == "__main__":
    main()
