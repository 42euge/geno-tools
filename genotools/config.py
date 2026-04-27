"""User configuration from ~/.geno/config.yaml."""

from __future__ import annotations

import shutil
import yaml
from pathlib import Path

CONFIG_DIR = Path.home() / ".geno"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

_DEFAULTS_SOURCE = Path(__file__).resolve().parent.parent / "config" / "defaults.yaml"

_DEFAULTS = {
    "aliases": {
        "command_prefix": "gt",
    },
    "discovery": {
        "sources": [
            {"kind": "github", "org": "42euge"},
        ],
    },
}


def ensure_dir() -> Path:
    """Create ~/.geno/ (and seed config.yaml from defaults) if missing.

    Called on install so a fresh machine ends up with the expected user
    config directory without any extra setup step.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        if _DEFAULTS_SOURCE.exists():
            shutil.copyfile(_DEFAULTS_SOURCE, CONFIG_FILE)
        else:
            CONFIG_FILE.write_text(yaml.safe_dump(_DEFAULTS, sort_keys=False))
    return CONFIG_DIR


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
