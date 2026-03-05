"""Configuration loader for the autonomous system."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any


@dataclass(frozen=True)
class SystemConfig:
    """Typed configuration used by all system modules."""

    emotional_dimension: int
    embedding_dimension: int
    lambda_stability: float
    kappa_collective: float
    loss_weights: Dict[str, float]


def _parse_scalar(value: str) -> Any:
    text = value.strip()
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def _simple_yaml_load(raw: str) -> Dict[str, Any]:
    """Parse a constrained YAML subset (mapping + one nested mapping level)."""

    result: Dict[str, Any] = {}
    current_map: Dict[str, float] | None = None
    current_key: str | None = None

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line.startswith("  "):
            if current_map is None:
                raise ValueError("Invalid nested YAML section")
            key, value = stripped.split(":", 1)
            current_map[key.strip()] = float(_parse_scalar(value))
            continue

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            current_key = key
            current_map = {}
            result[current_key] = current_map
        else:
            result[key] = _parse_scalar(value)
            current_key = None
            current_map = None
    return result


def load_system_config(path: str | Path) -> SystemConfig:
    """Load typed configuration from YAML without hard dependency on PyYAML."""

    config_path = Path(path)
    raw = config_path.read_text(encoding="utf-8")

    parsed: Dict[str, Any]
    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(raw)
    except Exception:
        parsed = _simple_yaml_load(raw)

    required = {
        "emotional_dimension",
        "embedding_dimension",
        "lambda_stability",
        "kappa_collective",
        "loss_weights",
    }
    missing = required - set(parsed.keys())
    if missing:
        raise ValueError(f"Missing config keys: {sorted(missing)}")

    return SystemConfig(
        emotional_dimension=int(parsed["emotional_dimension"]),
        embedding_dimension=int(parsed["embedding_dimension"]),
        lambda_stability=float(parsed["lambda_stability"]),
        kappa_collective=float(parsed["kappa_collective"]),
        loss_weights={k: float(v) for k, v in dict(parsed["loss_weights"]).items()},
    )
