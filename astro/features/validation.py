from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

_REGISTRY_PATH = Path(__file__).resolve().parent / "schema_registry.json"


@dataclass
class ValidationReport:
    ok: bool
    schema_id: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def load_schema_registry(path: Optional[Path] = None) -> Dict[str, Any]:
    p = path or _REGISTRY_PATH
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def get_schema(registry: Dict[str, Any], schema_id: Optional[str] = None) -> Dict[str, Any]:
    sid = schema_id or registry.get("default_schema_id", "fused_v1")
    schemas = registry.get("schemas", {})
    if sid not in schemas:
        raise KeyError(f"Unknown schema_id: {sid}")
    return {"id": sid, **schemas[sid]}


def validate_fused_frame(
    df: pd.DataFrame,
    schema_id: Optional[str] = None,
    *,
    registry_path: Optional[Path] = None,
    strict_optional: bool = False,
) -> ValidationReport:
    reg = load_schema_registry(registry_path)
    sid = schema_id or reg.get("default_schema_id", "fused_v1")
    schema = get_schema(reg, sid)
    required: Set[str] = set(schema.get("required_columns", []))
    errors: List[str] = []
    warnings: List[str] = []

    lower_map = {str(c).lower(): c for c in df.columns}

    for r in required:
        if r.lower() not in lower_map:
            errors.append(f"missing required column: {r}")

    if strict_optional:
        optional = set(c.lower() for c in schema.get("optional_columns", []))
        for c in df.columns:
            cl = c.lower() if isinstance(c, str) else str(c)
            if cl not in required and cl not in optional and cl != "date":
                warnings.append(f"unexpected column: {c}")

    return ValidationReport(ok=len(errors) == 0, schema_id=sid, errors=errors, warnings=warnings)


def assert_fused_frame_valid(df: pd.DataFrame, schema_id: Optional[str] = None) -> None:
    rep = validate_fused_frame(df, schema_id)
    if not rep.ok:
        raise ValueError(f"Feature validation failed ({rep.schema_id}): " + "; ".join(rep.errors))


def validate_model_window(
    df: pd.DataFrame,
    feature_columns: List[str],
    schema_id: Optional[str] = None,
) -> ValidationReport:
    """Validate that model feature columns exist (Date not required in window array)."""
    reg = load_schema_registry()
    sid = schema_id or reg.get("default_schema_id", "fused_v1")
    errors = []
    for c in feature_columns:
        if c not in df.columns:
            errors.append(f"missing model feature column: {c}")
    return ValidationReport(ok=len(errors) == 0, schema_id=sid, errors=errors)
