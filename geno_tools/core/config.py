"""geno-tools configuration from ~/.geno/config.yaml."""

from __future__ import annotations

import shutil
import yaml
from pathlib import Path
CONFIG_DIR = Path.home() / ".geno" / "geno-tools"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

_DEFAULTS_SOURCE = Path(__file__).resolve().parent / "config" / "defaults.yaml"

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
    for key, default in _DEFAULTS.items():
        if key in data:
            if isinstance(default, dict) and isinstance(data[key], dict):
                merged[key] = {**default, **data[key]}
            else:
                merged[key] = data[key]
    return merged


def command_prefix() -> str:
    return load().get("aliases", {}).get("command_prefix", "gt")


def set_config(key: str, value: str) -> None:
    """Set a dot-path key in config.yaml."""
    ensure_dir()
    try:
        data = yaml.safe_load(CONFIG_FILE.read_text()) or {}
    except Exception:
        data = {}
    parts = key.split(".")
    cur = data
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    # Coerce to int/float/bool where sensible — skip if already a non-string type
    if not isinstance(value, str):
        v: object = value
    else:
        try:
            v = int(value)
        except ValueError:
            try:
                v = float(value)
            except ValueError:
                if value.lower() in ("true", "yes"):
                    v = True
                elif value.lower() in ("false", "no"):
                    v = False
                else:
                    v = value
    cur[parts[-1]] = v
    CONFIG_FILE.write_text(yaml.safe_dump(data, sort_keys=False))
