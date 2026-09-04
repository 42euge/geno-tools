"""Pure comparison of two validated installation lockfiles."""

from __future__ import annotations

from dataclasses import dataclass

from .lockfile import parse_lockfile


@dataclass(frozen=True)
class SkillsetDelta:
    name: str
    state: str
    here: dict | None
    source: dict | None


@dataclass(frozen=True)
class ConfigDelta:
    key: str
    here: object
    source: object


@dataclass(frozen=True)
class SyncDiff:
    skillsets: tuple[SkillsetDelta, ...]
    config: tuple[ConfigDelta, ...]


def _flatten(value: dict, prefix: str = "") -> dict[str, object]:
    flattened: dict[str, object] = {}
    for key in sorted(value):
        path = f"{prefix}.{key}" if prefix else key
        nested = value[key]
        if isinstance(nested, dict):
            flattened.update(_flatten(nested, path))
        else:
            flattened[path] = nested
    return flattened


def compare(here: dict, source: dict) -> SyncDiff:
    """Describe changes required to make ``here`` match ``source``."""
    local = parse_lockfile(here)
    desired = parse_lockfile(source)
    local_skillsets = local["skillsets"]
    desired_skillsets = desired["skillsets"]

    skillsets: list[SkillsetDelta] = []
    for name in sorted(local_skillsets.keys() | desired_skillsets.keys()):
        local_entry = local_skillsets.get(name)
        desired_entry = desired_skillsets.get(name)
        if local_entry is None:
            state = "missing-here"
        elif desired_entry is None:
            state = "extra-here"
        elif local_entry == desired_entry:
            state = "in-sync"
        else:
            state = "version-skew"
        skillsets.append(SkillsetDelta(name, state, local_entry, desired_entry))

    local_config = _flatten(local["config"])
    desired_config = _flatten(desired["config"])
    config_deltas = tuple(
        ConfigDelta(key, local_config.get(key), desired_config.get(key))
        for key in sorted(local_config.keys() | desired_config.keys())
        if local_config.get(key) != desired_config.get(key)
    )
    return SyncDiff(tuple(skillsets), config_deltas)
