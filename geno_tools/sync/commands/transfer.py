"""Shared orchestration for symmetric push and pull commands."""

from __future__ import annotations

import base64
import binascii
import json
import sys
from typing import Any

from geno_tools.sync import selection, terminal
from geno_tools.sync.diff import compare
from geno_tools.sync.reconcile import ReconcileAction, ReconcileResult


MAX_UNCONFIRMED_BYTES = 100 * 1024 * 1024


class TransferError(RuntimeError):
    """A transfer could not be selected or approved."""


def encode_selections(value: dict[str, str]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_selections(value: str) -> dict[str, str]:
    try:
        decoded = base64.b64decode(value, altchars=b"-_", validate=True)
        data = json.loads(decoded)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise TransferError("selection JSON is not valid URL-safe base64 JSON") from exc
    if not isinstance(data, dict) or any(
        not isinstance(name, str) or kind not in {"stable", "active"}
        for name, kind in data.items()
    ):
        raise TransferError("selection JSON must map skillsets to stable or active")
    return data


def choose_sources(inventory: dict[str, Any], policy: str) -> dict[str, str]:
    return selection.choose(
        inventory,
        policy,
        terminal.choose_one,
        interactive=sys.stdin.isatty(),
    )


def estimated_size(
    inventory: dict[str, Any], choices: dict[str, str]
) -> int:
    total = 0
    for name, kind in choices.items():
        candidate = inventory["skillsets"][name]
        total += int(candidate.get("stable_transfer_size", 0))
        active = candidate.get("active")
        if kind == "active" and isinstance(active, dict):
            total += int(active.get("transfer_size", 0))
    return total


def approve_large(size: int, *, yes: bool) -> tuple[bool, bool]:
    """Return (approved, explicitly_approved_large_transfer)."""
    if size <= MAX_UNCONFIRMED_BYTES:
        return True, False
    if yes:
        return True, True
    amount = size / (1024 * 1024)
    try:
        answer = input(f"Transfer {amount:.1f} MiB of Dev snapshots? [y/N] ")
    except EOFError:
        return False, False
    approved = answer.strip().lower() in {"y", "yes"}
    return approved, approved


def preview(
    source: dict[str, Any],
    destination: dict[str, Any],
    choices: dict[str, str],
) -> ReconcileResult:
    """Build a no-payload reconciliation preview from two inventories."""
    delta = compare(destination["lockfile"], source["lockfile"])
    actions: list[ReconcileAction] = []
    for item in delta.skillsets:
        kind = {
            "missing-here": "install",
            "version-skew": "update",
            "extra-here": "remove",
        }.get(item.state)
        if kind:
            actions.append(ReconcileAction(item.name, kind))
    if delta.config:
        actions.append(ReconcileAction("config", "apply"))

    destination_skillsets = destination["skillsets"]
    for name, kind in sorted(choices.items()):
        here = destination_skillsets.get(name) or {}
        here_active = here.get("active")
        if kind == "stable":
            if isinstance(here_active, dict):
                actions.append(ReconcileAction(name, "select-stable"))
            continue
        source_active = source["skillsets"][name].get("active") or {}
        if not isinstance(here_active, dict) or here_active.get("fingerprint") != (
            source_active.get("fingerprint")
        ):
            actions.append(ReconcileAction(name, "activate-dev"))
    return ReconcileResult(tuple(actions), (), False)
