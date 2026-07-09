"""User configuration from ~/.geno/config.yaml."""

from __future__ import annotations

import os
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
    "llm": {
        "endpoint": "",
        "model": "",
        "timeout": 10,
        "settings_file": "~/.geno/settings.json",
        "model_rankings": [],
    },
    "mode": "user",
    "autonomy": 1,
}

_SETTINGS_FILE = Path.home() / ".geno" / "settings.json"


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


def get_mode(cwd: Path | None = None) -> str:
    """Return 'dev' or 'user'. Checks $GENO_MODE, then CWD heuristic, then config."""
    env = os.environ.get("GENO_MODE", "").strip().lower()
    if env in ("dev", "user"):
        return env
    if cwd is None:
        cwd = Path.cwd()
    for part in cwd.parts:
        if part.startswith("geno-") and part.endswith("-ws"):
            return "dev"
    return load().get("mode", "user")


def get_autonomy() -> int:
    """Return autonomy level 0, 1, or 2. Checks $GENO_AUTONOMY, then config."""
    env = os.environ.get("GENO_AUTONOMY", "").strip()
    if env in ("0", "1", "2"):
        return int(env)
    return int(load().get("autonomy", 1))


def get_llm() -> dict:
    """Return merged llm config + token from settings.json.

    The token lives in ~/.geno/settings.json so config.yaml can be
    committed to version control without leaking credentials.
    """
    import json as _json
    cfg = {**_DEFAULTS["llm"], **load().get("llm", {})}
    settings_path = Path(cfg.get("settings_file", "~/.geno/settings.json")).expanduser()
    token = ""
    if settings_path.exists():
        try:
            token = _json.loads(settings_path.read_text()).get("llm", {}).get("token", "")
        except Exception:  # noqa: BLE001
            pass
    return {**cfg, "token": token}


def set_config(key: str, value: str) -> None:
    """Set a dot-path key in config.yaml. Token keys are routed to settings.json."""
    import json as _json
    # Token is secret — route to settings.json
    if key in ("llm.token",):
        _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data: dict = {}
        if _SETTINGS_FILE.exists():
            try:
                data = _json.loads(_SETTINGS_FILE.read_text())
            except Exception:  # noqa: BLE001
                pass
        # Upsert nested key
        parts = key.split(".")
        cur = data
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = value
        _SETTINGS_FILE.write_text(_json.dumps(data, indent=2) + "\n")
        return

    # Everything else goes in config.yaml
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
    # Coerce to int/float/bool where sensible
    try:
        v: object = int(value)
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
