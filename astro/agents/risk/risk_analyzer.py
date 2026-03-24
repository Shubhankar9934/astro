"""Risk analysis helpers (policy hooks)."""

from typing import Dict


def summarize_risk_config(risk_yaml: Dict) -> str:
    return f"max_position={risk_yaml.get('max_position_fraction')}, max_daily_loss={risk_yaml.get('max_daily_loss_fraction')}"
