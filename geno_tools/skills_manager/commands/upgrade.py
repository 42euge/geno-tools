"""Upgrade installed skillsets to their latest remote revision."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .. import paths, registry
from .install import (
    _create_venv_if_needed,
    _detect_default_branch,
    _enumerate_registered_skills,
    _install_skills_via_npx,
    _uninstall_skill_names_via_npx,
)


def run(args: argparse.Namespace) -> int:
    if args.name:
        full = paths.normalize(args.name)
        if not paths.skillset_root(full).exists():
            print(f"not installed: {full}", file=sys.stderr)
            return 1
        results = [_update_one(full)]
    else:
        if not paths.ROOT.exists():
            print("no skillsets installed")
            return 0
        installed = sorted(
            path.name
            for path in paths.ROOT.iterdir()
            if path.is_dir()
            and path.name.startswith("geno-")
            and path.name != "geno-bootstrap"
        )
        if not installed:
            print("no skillsets installed")
            return 0
        results = [_update_one(full) for full in installed]

    _print_update_summary(results)
    return 1 if any(result.status == "error" for result in results) else 0


@dataclass
class _UpdateResult:
    name: str
    status: str
    detail: str = ""
    old_rev: str = ""
    new_rev: str = ""
    canonical_source: str = ""


def _update_one(
    full: str,
    *,
    force_venv_rebuild: bool = False,
    branch: str | None = None,
    revision: str | None = None,
) -> _UpdateResult:
    bare = paths.skillset_git(full)
    worktree = paths.skillset_worktree(full)
    if not worktree.exists():
        return _UpdateResult(full, "error", "main worktree missing")

    try:
        status = subprocess.check_output(
            ["git", "-C", str(worktree), "status", "--porcelain"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return _UpdateResult(full, "error", "git status failed")
    if status:
        return _UpdateResult(full, "skipped", "dirty worktree")

    default_branch = branch or _detect_default_branch(bare)
    try:
        current_branch = subprocess.check_output(
            ["git", "-C", str(worktree), "branch", "--show-current"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return _UpdateResult(full, "error", "cannot detect branch")
    if current_branch != default_branch:
        return _UpdateResult(
            full,
            "skipped",
            f"on branch '{current_branch}', not '{default_branch}'",
        )

    origin = _origin_url(bare)
    local_origin = bool(origin and Path(origin).expanduser().is_absolute())

    old_skills = set(_enumerate_registered_skills(full))

    try:
        old_rev = subprocess.check_output(
            ["git", "-C", str(worktree), "rev-parse", "HEAD"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        old_rev = ""

    print(f"  fetching {full}...")
    try:
        subprocess.check_call(["git", "-C", str(bare), "fetch", "--quiet", "origin"])
    except subprocess.CalledProcessError:
        return _UpdateResult(full, "error", "git fetch failed")
    if revision:
        try:
            subprocess.check_call(
                ["git", "-C", str(bare), "cat-file", "-e", f"{revision}^{{commit}}"]
            )
            subprocess.check_call(
                ["git", "-C", str(worktree), "reset", "--hard", "--quiet", revision]
            )
        except subprocess.CalledProcessError:
            return _UpdateResult(full, "error", f"recorded commit is unavailable: {revision}")
    else:
        try:
            subprocess.check_call(
                [
                    "git",
                    "-C",
                    str(worktree),
                    "pull",
                    "--ff-only",
                    "--quiet",
                    "origin",
                    default_branch,
                ]
            )
        except subprocess.CalledProcessError:
            return _UpdateResult(full, "error", "git pull --ff-only failed (diverged?)")

    try:
        new_rev = subprocess.check_output(
            ["git", "-C", str(worktree), "rev-parse", "HEAD"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        new_rev = ""
    if old_rev == new_rev:
        if force_venv_rebuild:
            _force_reinstall_venv(full)
        if local_origin:
            return _UpdateResult(
                full,
                "local-source",
                detail=origin,
                old_rev=old_rev[:8],
                canonical_source=registry.resolve(full) or "",
            )
        return _UpdateResult(full, "up-to-date", old_rev=old_rev[:8])

    if force_venv_rebuild:
        _force_reinstall_venv(full)
    else:
        _maybe_reinstall_venv(full, old_rev, new_rev)
    retired_skills = sorted(
        old_skills - set(_enumerate_registered_skills(full))
    )
    _uninstall_skill_names_via_npx(retired_skills)
    _install_skills_via_npx(full)
    return _UpdateResult(
        full, "updated", old_rev=old_rev[:8], new_rev=new_rev[:8]
    )


def _origin_url(bare: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(bare), "remote", "get-url", "origin"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        return ""


def _maybe_reinstall_venv(full: str, old_rev: str, new_rev: str) -> None:
    worktree = paths.skillset_worktree(full)
    if not (worktree / "pyproject.toml").exists():
        return
    try:
        changed = subprocess.check_output(
            ["git", "-C", str(worktree), "diff", "--name-only", old_rev, new_rev],
            text=True,
        )
    except subprocess.CalledProcessError:
        changed = "pyproject.toml"
    if "pyproject.toml" not in changed:
        return

    venv_dir = paths.skillset_venvs(full) / "default"
    if not venv_dir.exists():
        _create_venv_if_needed(full)
        return

    print("  pyproject.toml changed; reinstalling venv...")
    try:
        subprocess.check_call(
            [str(venv_dir / "bin" / "pip"), "install", "--quiet", "-e", str(worktree)]
        )
    except subprocess.CalledProcessError as error:
        print(f"  warn: venv reinstall failed for {full}: {error}", file=sys.stderr)


def _force_reinstall_venv(full: str) -> None:
    worktree = paths.skillset_worktree(full)
    if not (worktree / "pyproject.toml").exists():
        return
    venv_dir = paths.skillset_venvs(full) / "default"
    print(f"  rebuilding venv for {full}...")
    try:
        if not venv_dir.exists():
            _create_venv_if_needed(full)
        else:
            subprocess.check_call(
                [
                    str(venv_dir / "bin" / "pip"),
                    "install",
                    "--quiet",
                    "-e",
                    str(worktree),
                ]
            )
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"  warn: venv reinstall failed for {full}: {error}", file=sys.stderr)


def _print_update_summary(results: list[_UpdateResult]) -> None:
    groups = {
        "updated": [result for result in results if result.status == "updated"],
        "local source": [
            result for result in results if result.status == "local-source"
        ],
        "already up-to-date": [
            result for result in results if result.status == "up-to-date"
        ],
        "skipped": [result for result in results if result.status == "skipped"],
        "errors": [result for result in results if result.status == "error"],
    }
    print()
    for label, group in groups.items():
        if not group:
            continue
        print(f"{label} ({len(group)}):")
        for result in group:
            if result.status == "updated":
                print(f"  {result.name:<24} {result.old_rev} -> {result.new_rev}")
            elif result.status == "local-source":
                print(f"  {result.name:<24} {result.detail}")
                if result.canonical_source:
                    print("    replace with discovered source:")
                    print(f"      geno-tools uninstall {result.name}")
                    print(f"      geno-tools install {result.canonical_source}")
            elif result.status in {"skipped", "error"}:
                print(f"  {result.name:<24} {result.detail}")
            else:
                print(f"  {result.name}")
