from __future__ import annotations

from typing import List, Tuple

import torch
import torch.nn as nn


class TimeSeriesTransformer(nn.Module):
    """Encoder-only transformer over (batch, seq, n_features)."""

    def __init__(
        self,
        n_features: int,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 2,
        dropout: float = 0.1,
        num_classes: int = 2,
    ):
        super().__init__()
        self.input_proj = nn.Linear(n_features, d_model)
        enc_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(enc_layer, num_layers=n_layers)
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, L, F)
        h = self.input_proj(x)
        h = self.encoder(h)
        last = self.norm(h[:, -1, :])
        return self.head(last)


def build_model(
    feature_columns: List[str], model_cfg: dict
) -> Tuple[TimeSeriesTransformer, List[str]]:
    n = len(feature_columns)
    m = TimeSeriesTransformer(
        n_features=n,
        d_model=int(model_cfg.get("d_model", 64)),
        n_heads=int(model_cfg.get("n_heads", 4)),
        n_layers=int(model_cfg.get("n_layers", 2)),
        dropout=float(model_cfg.get("dropout", 0.1)),
        num_classes=2,
    )
    return m, feature_columns
