"""Safely reconcile the local installation toward a validated lockfile."""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Callable
from dataclasses import dataclass

from geno_tools.skills_manager import paths
from geno_tools.skills_manager.commands import remove
from geno_tools.skills_manager.commands.install import _get_requires, _install_one
from geno_tools.skills_manager.commands.upgrade import _update_one

from .diff import compare
from .lockfile import apply_portable_config, build_lockfile, parse_lockfile


class ReconcileError(RuntimeError):
    """Reconciliation cannot begin without risking local state."""


@dataclass(frozen=True)
class ReconcileOptions:
    dry_run: bool = False
    yes: bool = False
    rebuild: bool = True


@dataclass(frozen=True)
class ReconcileAction:
    name: str
    kind: str
    detail: str = ""


@dataclass(frozen=True)
class ReconcileResult:
    actions: tuple[ReconcileAction, ...]
    failures: tuple[ReconcileAction, ...]
    changed: bool


def dirty_skillsets() -> list[str]:
    """Return managed stable worktrees that are dirty or cannot be inspected."""
    if not paths.ROOT.exists():
        return []
    dirty: list[str] = []
    for item in sorted(paths.ROOT.iterdir()):
        if (
            not item.is_dir()
            or not item.name.startswith("geno-")
            or item.name == "geno-bootstrap"
        ):
            continue
        worktree = paths.skillset_worktree(item.name)
        try:
            output = subprocess.check_output(
                ["git", "-C", str(worktree), "status", "--porcelain"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            output = "unavailable"
        if output:
            dirty.append(item.name)
    return dirty


def confirm_removals(names: list[str]) -> bool:
    print("The following skillsets will be removed:")
    for name in names:
        print(f"  {name}")
    try:
        answer = input("Continue? [y/N] ")
    except EOFError:
        return False
    return answer.strip().lower() in {"y", "yes"}


def _dependency_closure(desired: set[str]) -> set[str]:
    protected = set(desired)
    pending = list(sorted(desired))
    while pending:
        name = pending.pop()
        for requirement in _get_requires(name):
            dependency = paths.normalize(requirement)
            if dependency in protected:
                continue
            protected.add(dependency)
            pending.append(dependency)
    return protected


def _planned_actions(source: dict) -> tuple[list[ReconcileAction], list[str], bool]:
    delta = compare(build_lockfile(), source)
    protected = _dependency_closure(set(source["skillsets"]))
    actions = [
        ReconcileAction(item.name, "install")
        for item in delta.skillsets
        if item.state == "missing-here"
    ]
    actions.extend(
        ReconcileAction(item.name, "update")
        for item in delta.skillsets
        if item.state == "version-skew"
    )
    removals = [
        item.name
        for item in delta.skillsets
        if item.state == "extra-here" and item.name not in protected
    ]
    actions.extend(ReconcileAction(name, "remove") for name in removals)
    config_changed = bool(delta.config)
    if config_changed:
        actions.append(ReconcileAction("config", "apply"))
    return actions, removals, config_changed


def reconcile(
    source: dict,
    options: ReconcileOptions,
    *,
    confirm: Callable[[list[str]], bool] = confirm_removals,
) -> ReconcileResult:
    """Make local managed state match ``source`` without discarding dev work."""
    desired = parse_lockfile(source)
    dirty = dirty_skillsets()
    if dirty:
        raise ReconcileError(
            "refusing to sync dirty or unreadable skillsets: " + ", ".join(dirty)
        )

    planned, planned_removals, config_changed = _planned_actions(desired)
    if options.dry_run:
        return ReconcileResult(tuple(planned), (), False)
    if planned_removals and not options.yes and not confirm(planned_removals):
        raise ReconcileError("sync cancelled; no changes made")

    actions: list[ReconcileAction] = []
    failures: list[ReconcileAction] = []
    initial = compare(build_lockfile(), desired)

    for item in initial.skillsets:
        if item.state == "missing-here":
            action = ReconcileAction(item.name, "install")
            try:
                rc = _install_one(item.source["url"], installing=set())
            except Exception as error:
                failures.append(ReconcileAction(item.name, "install", str(error)))
                continue
            if rc != 0:
                failures.append(
                    ReconcileAction(item.name, "install", f"installer exited {rc}")
                )
                continue
            actions.append(action)
        elif item.state == "version-skew":
            try:
                result = _update_one(
                    item.name, force_venv_rebuild=options.rebuild
                )
            except Exception as error:
                failures.append(ReconcileAction(item.name, "update", str(error)))
                continue
            if result.status in {"error", "skipped"}:
                failures.append(
                    ReconcileAction(item.name, "update", result.detail or result.status)
                )
            else:
                actions.append(ReconcileAction(item.name, "update"))

    current = build_lockfile()
    protected = _dependency_closure(set(desired["skillsets"]))
    removals = sorted(set(current["skillsets"]) - protected)
    for name in removals:
        try:
            rc = remove.run(argparse.Namespace(name=name, keep_data=False))
        except Exception as error:
            failures.append(ReconcileAction(name, "remove", str(error)))
            continue
        if rc:
            failures.append(
                ReconcileAction(name, "remove", f"uninstaller exited {rc}")
            )
        else:
            actions.append(ReconcileAction(name, "remove"))

    if config_changed:
        try:
            apply_portable_config(desired["config"])
        except Exception as error:
            failures.append(ReconcileAction("config", "apply", str(error)))
        else:
            actions.append(ReconcileAction("config", "apply"))

    return ReconcileResult(tuple(actions), tuple(failures), bool(actions))
