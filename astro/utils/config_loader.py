from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

ASTRO_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ASTRO_PACKAGE_ROOT / "configs"


def _read_yaml(name: str) -> Dict[str, Any]:
    path = CONFIG_DIR / name
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


@dataclass
class AstroConfig:
    system: Dict[str, Any] = field(default_factory=dict)
    agents: Dict[str, Any] = field(default_factory=dict)
    model: Dict[str, Any] = field(default_factory=dict)
    risk: Dict[str, Any] = field(default_factory=dict)
    ibkr: Dict[str, Any] = field(default_factory=dict)

    def data_root_path(self, cwd: Optional[Path] = None) -> Path:
        root = Path(self.system.get("data_root", "data"))
        if not root.is_absolute():
            root = (cwd or Path.cwd()) / root
        return root.resolve()


def load_all_configs(
    override_path: Optional[Path] = None,
) -> AstroConfig:
    """Load YAML from astro/configs. Optional override_path can point to a custom config dir."""
    base = override_path or CONFIG_DIR
    if override_path:

        def read(n: str) -> Dict[str, Any]:
            p = base / n
            if not p.exists():
                return {}
            with open(p, encoding="utf-8") as f:
                d = yaml.safe_load(f)
            return d if isinstance(d, dict) else {}

        return AstroConfig(
            system=read("system.yaml"),
            agents=read("agents.yaml"),
            model=read("model.yaml"),
            risk=read("risk.yaml"),
            ibkr=read("ibkr.yaml"),
        )
    return AstroConfig(
        system=_read_yaml("system.yaml"),
        agents=_read_yaml("agents.yaml"),
        model=_read_yaml("model.yaml"),
        risk=_read_yaml("risk.yaml"),
        ibkr=_read_yaml("ibkr.yaml"),
    )
