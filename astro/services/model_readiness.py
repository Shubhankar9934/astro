from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from astro.models.transformer.inference import load_inference_optional


def default_checkpoint_paths(root: Path) -> tuple[Path, Path]:
    ckpt = root / "models" / "checkpoints" / "best.pt"
    scaler = root / "models" / "checkpoints" / "scaler.npz"
    return ckpt, scaler


def model_inference_status(
    root: Path,
    *,
    fused_parquet: Optional[Path] = None,
    seq_len: int = 32,
) -> Dict[str, Any]:
    """Single source of truth for API health and decision gating.

    - ``inference_loadable``: checkpoint + scaler exist and ``TransformerInference`` initializes.
    - ``inference_smoke_ok``: optional forward pass on ``fused_parquet`` (if path provided and exists).
    - ``inference_ready``: loadable and (if fused path given) smoke ok; if no fused path, same as loadable.
    """
    ckpt, scaler = default_checkpoint_paths(root)
    out: Dict[str, Any] = {
        "checkpoint_path": str(ckpt),
        "scaler_path": str(scaler),
        "checkpoint_exists": ckpt.exists(),
        "scaler_exists": scaler.exists(),
        "inference_loadable": False,
        "inference_smoke_ok": None,
        "inference_ready": False,
        "load_error": None,
        "schema_id": None,
    }
    if not ckpt.exists() or not scaler.exists():
        out["load_error"] = "missing_checkpoint_or_scaler"
        return out
    inf = load_inference_optional(ckpt, scaler)
    if inf is None:
        out["load_error"] = "load_inference_optional_returned_none"
        return out
    out["inference_loadable"] = True
    out["schema_id"] = inf.schema_id
    if fused_parquet is None or not fused_parquet.exists():
        out["inference_smoke_ok"] = None
        out["inference_ready"] = True
        return out
    try:
        inf.predict_latest_from_parquet(fused_parquet, seq_len)
        out["inference_smoke_ok"] = True
        out["inference_ready"] = True
    except Exception as e:
        out["inference_smoke_ok"] = False
        out["inference_ready"] = False
        out["load_error"] = f"predict_smoke_failed:{type(e).__name__}:{e}"
    return out


def load_inference_strict(checkpoint: Path, scaler_path: Path):
    """Raise if artifacts missing or load fails (caller handles messaging)."""
    inf = load_inference_optional(checkpoint, scaler_path)
    if inf is None:
        raise FileNotFoundError("Model checkpoint or scaler missing or unloadable")
    return inf
