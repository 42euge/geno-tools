"""Build, validate, and apply portable installation lockfiles."""

from __future__ import annotations

import json
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

from geno_tools.core import config
from geno_tools.skills_manager import paths
from geno_tools.skills_manager.commands import dev


SCHEMA_VERSION = 1
PORTABLE_CONFIG_KEYS = ("aliases", "discovery", "autonomy", "mode")
_ENTRY_KEYS = ("url", "branch", "sha", "version")


class LockfileError(ValueError):
    """The supplied installation lockfile is malformed or unsupported."""


def _raw_config() -> dict:
    if not config.CONFIG_FILE.exists():
        return {}
    try:
        value = yaml.safe_load(config.CONFIG_FILE.read_text()) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return value if isinstance(value, dict) else {}


def portable_config(value: dict) -> dict:
    """Return only configuration safe to reproduce on another machine."""
    return {key: value[key] for key in PORTABLE_CONFIG_KEYS if key in value}


def _git(full: str, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(paths.skillset_worktree(full)), *arguments],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def _cloneable(value: str) -> bool:
    return value.startswith(("http://", "https://", "ssh://", "git://", "git@", "file://"))


def clone_source(full: str) -> str:
    """Return a source another host can clone without changing local Git config."""
    origin = _git(full, "remote", "get-url", "origin")
    local = Path(origin).expanduser()
    if not local.is_dir():
        return origin
    try:
        nested = subprocess.check_output(
            ["git", "-C", str(local), "remote", "get-url", "origin"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return origin
    return nested if _cloneable(nested) else origin


def _installed_skillsets() -> list[str]:
    if not paths.ROOT.exists():
        return []
    return sorted(
        item.name
        for item in paths.ROOT.iterdir()
        if item.is_dir()
        and item.name.startswith("geno-")
        and item.name != "geno-bootstrap"
    )


def _generated_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_lockfile(
    *, machine: str | None = None, generated: str | None = None
) -> dict:
    """Describe stable managed skillsets and portable configuration."""
    skillsets: dict[str, dict[str, str]] = {}
    for full in _installed_skillsets():
        version, _scripts = dev._project_details(paths.skillset_worktree(full))
        skillsets[full] = {
            "url": clone_source(full),
            "branch": _git(full, "branch", "--show-current"),
            "sha": _git(full, "rev-parse", "HEAD"),
            "version": version,
        }
    return {
        "version": SCHEMA_VERSION,
        "machine": machine or socket.gethostname(),
        "generated": generated or _generated_now(),
        "skillsets": skillsets,
        "config": portable_config(_raw_config()),
    }


def parse_lockfile(value: str | bytes | dict) -> dict:
    """Decode and validate a schema-version-1 lockfile."""
    if isinstance(value, (str, bytes)):
        try:
            data = json.loads(value)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise LockfileError("lockfile is not valid JSON") from error
    else:
        data = value
    if not isinstance(data, dict):
        raise LockfileError("lockfile must be a JSON object")
    version = data.get("version")
    if type(version) is not int or version != SCHEMA_VERSION:
        raise LockfileError(
            f"unsupported lockfile version {version!r}; this geno-tools supports version {SCHEMA_VERSION}"
        )
    for key in ("machine", "generated"):
        if not isinstance(data.get(key), str):
            raise LockfileError(f"lockfile field {key!r} must be a string")
    skillsets = data.get("skillsets")
    if not isinstance(skillsets, dict):
        raise LockfileError("lockfile field 'skillsets' must be a mapping")
    if not isinstance(data.get("config"), dict):
        raise LockfileError("lockfile field 'config' must be a mapping")
    for name, entry in skillsets.items():
        if not isinstance(name, str) or not isinstance(entry, dict):
            raise LockfileError("lockfile contains an invalid skillset entry")
        if any(not isinstance(entry.get(key), str) for key in _ENTRY_KEYS):
            raise LockfileError(f"invalid lockfile entry for {name}")
    return data


def apply_portable_config(value: dict) -> None:
    """Replace supplied portable keys while preserving all local-only keys."""
    incoming = portable_config(value)
    current = _raw_config()
    current.update(incoming)
    config.ensure_dir()
    config.CONFIG_FILE.write_text(yaml.safe_dump(current, sort_keys=False))
