from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from astro.features.diagnostics import correlation_report
from astro.features.validation import assert_fused_frame_valid, load_schema_registry
from astro.models.transformer.architecture import build_model
from astro.models.transformer.dataset import (
    WindowDataset,
    fit_scaler,
    load_fused_parquet,
    save_scaler,
    train_val_split_indices,
)


def train(
    fused_parquet: Path,
    out_dir: Path,
    model_cfg: Dict,
) -> Path:
    df = load_fused_parquet(fused_parquet)
    schema_id = str(model_cfg.get("schema_id", "fused_v1"))
    assert_fused_frame_valid(df, schema_id)
    reg = load_schema_registry()
    feature_schema_version = str(reg.get("feature_schema_version", "1"))
    feature_columns: List[str] = list(model_cfg["feature_columns"])
    for c in feature_columns:
        if c not in df.columns:
            df[c] = 0.0
    corr_rep = correlation_report(
        df,
        feature_columns,
        max_corr=float(model_cfg.get("max_feature_corr", 0.95)),
    )
    if not corr_rep["ok"] and bool(model_cfg.get("fail_on_high_feature_corr", False)):
        raise ValueError("High feature correlations: " + str(corr_rep["pairs"][:10]))
    seq_len = int(model_cfg["seq_len"])
    horizon = int(model_cfg.get("forward_horizon_bars", 1))
    close_col = "close" if "close" in df.columns else "Close"
    train_idx, val_idx = train_val_split_indices(df, close_col, seq_len, horizon)
    if len(train_idx) == 0:
        raise ValueError("No training windows; increase history or lower seq_len / horizon.")
    mean, std = fit_scaler(df, feature_columns, train_idx, seq_len)
    scaler_path = out_dir / "scaler.npz"
    save_scaler(scaler_path, mean, std, feature_columns)

    train_ds = WindowDataset(df, feature_columns, seq_len, horizon, mean, std, train_idx)
    val_ds = WindowDataset(df, feature_columns, seq_len, horizon, mean, std, val_idx)

    train_loader = DataLoader(
        train_ds, batch_size=int(model_cfg.get("batch_size", 32)), shuffle=True
    )
    val_loader = DataLoader(val_ds, batch_size=int(model_cfg.get("batch_size", 32)))

    model, _ = build_model(feature_columns, model_cfg)
    opt = torch.optim.Adam(model.parameters(), lr=float(model_cfg.get("learning_rate", 1e-3)))
    loss_fn = nn.CrossEntropyLoss()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    best_val = float("inf")
    best_path = out_dir / "best.pt"
    out_dir.mkdir(parents=True, exist_ok=True)

    epochs = int(model_cfg.get("epochs", 5))
    for ep in range(epochs):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            opt.step()
        model.eval()
        val_loss = 0.0
        n = 0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                logits = model(xb)
                val_loss += float(loss_fn(logits, yb).item()) * len(xb)
                n += len(xb)
        val_loss /= max(n, 1)
        # NaN < inf is False in Python; without a first-epoch save, no checkpoint is written.
        should_save = ep == 0 or (math.isfinite(val_loss) and val_loss < best_val)
        if should_save:
            if math.isfinite(val_loss):
                best_val = val_loss
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "feature_columns": feature_columns,
                    "model_cfg": model_cfg,
                    "schema_id": schema_id,
                    "feature_schema_version": feature_schema_version,
                },
                best_path,
            )
    return best_path
