"""User configuration from ~/.geno/config.yaml."""

from __future__ import annotations

import yaml
from pathlib import Path

CONFIG_DIR = Path.home() / ".geno"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

_DEFAULTS = {
    "aliases": {
        "command_prefix": "gt",
    },
}


def load() -> dict:
    if not CONFIG_FILE.exists():
        return dict(_DEFAULTS)
    try:
        data = yaml.safe_load(CONFIG_FILE.read_text()) or {}
    except Exception:
        return dict(_DEFAULTS)
    merged = dict(_DEFAULTS)
    for section, defaults in _DEFAULTS.items():
        if section in data and isinstance(data[section], dict):
            merged[section] = {**defaults, **data[section]}
    return merged


def command_prefix() -> str:
    return load().get("aliases", {}).get("command_prefix", "gt")
