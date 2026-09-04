"""Inventory active developer checkouts and choose what a sync transfers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from geno_tools.skills_manager.commands import dev
from geno_tools.sync import lockfile, snapshot


INVENTORY_PROTOCOL = 1
POLICIES = {"ask", "stable", "active"}
ANSWERS = {"stable", "active", "stable-all", "active-all", "cancel"}


class SelectionError(RuntimeError):
    """Raised when a sync selection cannot be completed safely."""


Chooser = Callable[[dict[str, Any], list[dict[str, Any]]], str]


def inventory() -> dict[str, Any]:
    """Describe Stable fallbacks and eligible active dev selections."""
    stable_lock = lockfile.build_lockfile()
    skillsets: dict[str, Any] = {}
    for name, stable in sorted(stable_lock["skillsets"].items()):
        details = dev.selection_details(name)
        active = None
        if details["active"]["mode"] == "dev":
            captured = snapshot.capture(
                Path(details["active"]["source"]), machine=stable_lock["machine"]
            )
            active = {
                key: value
                for key, value in captured.items()
                if key != "artifacts"
            }
            active["transfer_size"] = snapshot.encoded_size(captured)
        skillsets[name] = {
            "stable": stable,
            "active": active,
            "rollback": bool(details.get("rollback")),
        }
    return {
        "protocol": INVENTORY_PROTOCOL,
        "machine": stable_lock["machine"],
        "generated": stable_lock["generated"],
        "lockfile": stable_lock,
        "skillsets": skillsets,
    }


def parse(value: str | bytes | dict[str, Any]) -> dict[str, Any]:
    """Decode and validate inventory received from another geno-tools CLI."""
    if isinstance(value, (str, bytes)):
        try:
            data = json.loads(value)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise SelectionError("sync inventory is not valid JSON") from exc
    else:
        data = value
    if not isinstance(data, dict) or data.get("protocol") != INVENTORY_PROTOCOL:
        protocol = data.get("protocol") if isinstance(data, dict) else None
        raise SelectionError(
            f"unsupported sync inventory protocol {protocol!r}; "
            f"this geno-tools supports protocol {INVENTORY_PROTOCOL}"
        )
    if not isinstance(data.get("machine"), str):
        raise SelectionError("sync inventory has no machine name")
    stable = data.get("lockfile")
    try:
        validated_lock = lockfile.parse_lockfile(stable)
    except lockfile.LockfileError as exc:
        raise SelectionError(f"invalid inventory lockfile: {exc}") from exc
    candidates = _candidates(data)
    if {candidate["name"] for candidate in candidates} != set(
        validated_lock["skillsets"]
    ):
        raise SelectionError(
            "sync inventory skillsets must exactly match its Stable lockfile"
        )
    return data


def _candidates(value: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or value.get("protocol") != INVENTORY_PROTOCOL:
        raise SelectionError("unsupported sync inventory protocol")
    skillsets = value.get("skillsets")
    if not isinstance(skillsets, dict):
        raise SelectionError("sync inventory has no skillsets")
    candidates = []
    for name, item in sorted(skillsets.items()):
        if not isinstance(name, str) or not isinstance(item, dict):
            raise SelectionError("sync inventory has an invalid skillset")
        if not isinstance(item.get("stable"), dict):
            raise SelectionError(f"sync inventory has no Stable fallback for {name}")
        candidates.append({"name": name, **item})
    return candidates


def choose(
    value: dict[str, Any],
    policy: str,
    chooser: Chooser,
    *,
    interactive: bool,
) -> dict[str, str]:
    """Resolve one Stable/Dev source choice for every inventoried skillset."""
    if policy not in POLICIES:
        raise SelectionError(f"unsupported dev source policy: {policy}")
    candidates = _candidates(value)
    selected = {candidate["name"]: "stable" for candidate in candidates}

    if policy == "stable":
        return selected
    if policy == "active":
        for candidate in candidates:
            if isinstance(candidate.get("active"), dict):
                selected[candidate["name"]] = "active"
        return selected
    if not interactive:
        raise SelectionError(
            "cannot ask which dev source to sync without a TTY; "
            "use --dev-source stable|active"
        )

    eligible = [
        candidate for candidate in candidates if isinstance(candidate.get("active"), dict)
    ]
    for index, candidate in enumerate(eligible):
        remaining = eligible[index:]
        answer = chooser(candidate, remaining)
        if answer not in ANSWERS:
            raise SelectionError(f"invalid sync selection: {answer}")
        if answer == "cancel":
            raise SelectionError("sync selection cancelled")
        if answer == "stable-all":
            break
        if answer == "active-all":
            for item in remaining:
                selected[item["name"]] = "active"
            break
        selected[candidate["name"]] = answer
    return selected
