from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch

from astro.decision_engine.state_manager import ModelPrediction
from astro.features.validation import validate_model_window
from astro.models.transformer.architecture import build_model
from astro.models.transformer.dataset import load_fused_parquet, load_scaler


def _entropy_uncertainty(probs: np.ndarray) -> float:
    p = np.clip(probs, 1e-12, 1.0)
    ent = float(-(p * np.log(p)).sum())
    max_ent = float(np.log(len(p)))
    u = ent / max_ent if max_ent > 0 else 0.0
    return u if math.isfinite(u) else 1.0


class TransformerInference:
    def __init__(self, checkpoint: Path, scaler_path: Path):
        try:
            ckpt = torch.load(checkpoint, map_location="cpu", weights_only=False)
        except TypeError:
            ckpt = torch.load(checkpoint, map_location="cpu")
        self.feature_columns: List[str] = list(ckpt["feature_columns"])
        model_cfg = dict(ckpt["model_cfg"])
        self.schema_id: str = str(ckpt.get("schema_id", model_cfg.get("schema_id", "fused_v1")))
        self.feature_schema_version: str = str(
            ckpt.get("feature_schema_version", "1")
        )
        self.checkpoint_path = checkpoint
        self.model, _ = build_model(self.feature_columns, model_cfg)
        self.model.load_state_dict(ckpt["model_state"])
        self.model.eval()
        self.mean, self.std, cols = load_scaler(scaler_path)
        if cols != self.feature_columns:
            pass  # trust checkpoint columns order

    def predict_window(self, window: np.ndarray) -> ModelPrediction:
        """window shape (L, F) raw features matching feature_columns."""
        w = np.nan_to_num(np.asarray(window, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)
        x = (w - self.mean) / np.where(self.std < 1e-8, 1.0, self.std)
        x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
        t = torch.from_numpy(x).float().unsqueeze(0)
        with torch.no_grad():
            logits = self.model(t)
            prob = torch.softmax(logits, dim=-1)[0]
            pv = np.nan_to_num(prob.cpu().numpy(), nan=0.5, posinf=1.0, neginf=0.0)
            s = float(pv.sum())
            if s <= 0 or not math.isfinite(s):
                pv = np.ones_like(pv) / max(len(pv), 1)
            else:
                pv = pv / s
        p_up = float(pv[1]) if len(pv) > 1 else float(pv[0])
        p_up = float(min(1.0, max(0.0, p_up)))
        unc = _entropy_uncertainty(pv)
        return ModelPrediction(
            p_up=p_up,
            uncertainty=unc,
            raw={"logits": logits.numpy().tolist(), "probs": pv.tolist()},
        )

    def predict_latest_from_parquet(self, fused_parquet: Path, seq_len: int) -> ModelPrediction:
        df = load_fused_parquet(fused_parquet)
        rep = validate_model_window(df, self.feature_columns, self.schema_id)
        if not rep.ok:
            raise ValueError("Model window validation: " + "; ".join(rep.errors))
        for c in self.feature_columns:
            if c not in df.columns:
                df[c] = 0.0
        tail = df.iloc[-seq_len:][self.feature_columns].to_numpy(dtype=np.float64)
        return self.predict_window(tail)


def load_inference_optional(
    checkpoint: Path, scaler_path: Path
) -> TransformerInference | None:
    if not checkpoint.exists() or not scaler_path.exists():
        return None
    return TransformerInference(checkpoint, scaler_path)
