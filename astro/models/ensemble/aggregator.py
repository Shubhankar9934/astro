from __future__ import annotations

from typing import List

from astro.decision_engine.state_manager import ModelPrediction


def average_predictions(preds: List[ModelPrediction]) -> ModelPrediction:
    if not preds:
        return ModelPrediction()
    p_up = sum(p.p_up for p in preds) / len(preds)
    er = sum(p.expected_return for p in preds) / len(preds)
    unc = sum(p.uncertainty for p in preds) / len(preds)
    return ModelPrediction(p_up=p_up, expected_return=er, uncertainty=unc)
