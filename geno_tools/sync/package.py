"""Versioned envelope for Stable fallbacks and selected Dev snapshots."""

from __future__ import annotations

import base64
import binascii
import json
from pathlib import Path
from typing import Any

from geno_tools.skills_manager import paths
from geno_tools.skills_manager.commands import dev
from geno_tools.sync import lockfile, snapshot


PACKAGE_PROTOCOL = 1


class PackageError(ValueError):
    """The supplied sync package is malformed or unsupported."""


def build(selections: dict[str, str]) -> dict[str, Any]:
    """Build a package from one Stable/active choice per installed skillset."""
    stable = lockfile.build_lockfile()
    expected = set(stable["skillsets"])
    if set(selections) != expected:
        raise PackageError("sync selections must exactly match installed skillsets")
    packaged: dict[str, dict[str, Any]] = {}
    for name in sorted(expected):
        kind = selections[name]
        stable_snapshot = snapshot.capture(
            paths.skillset_worktree(name), machine=stable["machine"]
        )
        if kind == "stable":
            packaged[name] = {
                "kind": "stable",
                "stable_snapshot": stable_snapshot,
            }
            continue
        if kind != "active":
            raise PackageError(f"invalid sync selection for {name}: {kind}")
        details = dev.selection_details(name)["active"]
        if details["mode"] != "dev":
            raise PackageError(f"{name} has no active Dev selection")
        packaged[name] = {
            "kind": "dev",
            "stable_snapshot": stable_snapshot,
            "snapshot": snapshot.capture(
                Path(details["source"]), machine=stable["machine"]
            ),
        }
    return {
        "protocol": PACKAGE_PROTOCOL,
        "lockfile": stable,
        "selections": packaged,
    }


def _decode(value: str, *, name: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise PackageError(f"invalid base64 in {name}") from exc


def artifact_size(value: dict[str, Any]) -> int:
    """Return decoded artifact bytes carried by all Dev selections."""
    total = 0
    selections = value.get("selections")
    if not isinstance(selections, dict):
        raise PackageError("sync package field 'selections' must be a mapping")
    for name, selected in selections.items():
        if not isinstance(selected, dict):
            continue
        payloads = []
        if selected.get("stable_snapshot") is not None:
            payloads.append(("stable", selected["stable_snapshot"]))
        if selected.get("kind") == "dev":
            payloads.append(("dev", selected.get("snapshot")))
        for label, payload in payloads:
            artifacts = payload.get("artifacts") if isinstance(payload, dict) else None
            if not isinstance(artifacts, dict):
                raise PackageError(f"invalid {label} snapshot for {name}")
            for artifact_name in snapshot.ARTIFACT_NAMES:
                encoded = artifacts.get(artifact_name)
                if not isinstance(encoded, str):
                    raise PackageError(
                        f"invalid {label} snapshot artifact for {name}: {artifact_name}"
                    )
                total += len(
                    _decode(encoded, name=f"{name}.{label}.{artifact_name}")
                )
    return total


def parse(value: str | bytes | dict[str, Any]) -> dict[str, Any]:
    """Decode and validate a protocol-version-1 sync package."""
    if isinstance(value, (str, bytes)):
        try:
            data = json.loads(value)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise PackageError("sync package is not valid JSON") from exc
    else:
        data = value
    if not isinstance(data, dict):
        raise PackageError("sync package must be a JSON object")
    protocol = data.get("protocol")
    if type(protocol) is not int or protocol != PACKAGE_PROTOCOL:
        raise PackageError(
            f"unsupported sync package protocol {protocol!r}; "
            f"this geno-tools supports protocol {PACKAGE_PROTOCOL}"
        )
    try:
        stable = lockfile.parse_lockfile(data.get("lockfile"))
    except lockfile.LockfileError as exc:
        raise PackageError(str(exc)) from exc
    selections = data.get("selections")
    if not isinstance(selections, dict):
        raise PackageError("sync package field 'selections' must be a mapping")
    if set(selections) != set(stable["skillsets"]):
        raise PackageError(
            "sync package selections must exactly match lockfile skillsets"
        )
    for name, selected in selections.items():
        if not isinstance(selected, dict) or selected.get("kind") not in {
            "stable",
            "dev",
        }:
            raise PackageError(f"invalid sync selection for {name}")
        stable_snapshot = selected.get("stable_snapshot")
        if stable_snapshot is not None:
            if not isinstance(stable_snapshot, dict):
                raise PackageError(f"invalid Stable snapshot for {name}")
            try:
                snapshot.validate(stable_snapshot)
            except snapshot.SnapshotError as exc:
                raise PackageError(
                    f"invalid Stable snapshot for {name}: {exc}"
                ) from exc
        if selected["kind"] == "dev":
            payload = selected.get("snapshot")
            if not isinstance(payload, dict):
                raise PackageError(f"invalid Dev snapshot for {name}")
            try:
                snapshot.validate(payload)
            except snapshot.SnapshotError as exc:
                raise PackageError(f"invalid Dev snapshot for {name}: {exc}") from exc
    artifact_size(data)
    return data
