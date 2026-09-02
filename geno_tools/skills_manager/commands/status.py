"""Report installed skillsets and their repository state."""

from __future__ import annotations

import argparse
import subprocess

from geno_tools.core.terminal import (
    bold,
    cyan,
    dim,
    green,
    is_tty,
    red,
    rule,
    yellow,
)

from .. import paths
from . import dev

_STATE_FORMATS = {
    "in-sync": ("●", "ok", green),
    "ahead": ("▲", "ahead", cyan),
    "dirty": ("✎", "dirty", yellow),
    "diverged": ("✗", "diverged", red),
    "offline": ("·", "offline", dim),
    "dev-drift": ("!", "dev-drift", red),
}


def _installed_skillsets() -> list[str]:
    if not paths.ROOT.exists():
        return []
    return sorted(
        path.name
        for path in paths.ROOT.iterdir()
        if path.is_dir()
        and path.name.startswith("geno-")
        and path.name != "geno-bootstrap"
    )


def _format_state(state: str) -> str:
    if state.startswith("behind"):
        glyph = "▼" if is_tty() else "<"
        return yellow(f"{glyph} {state}")
    glyph, ascii_label, color = _STATE_FORMATS.get(state, ("", state, dim))
    prefix = f"{glyph} " if is_tty() and glyph else ""
    return color(f"{prefix}{state if is_tty() else ascii_label}")


def run(_: argparse.Namespace) -> int:
    installed = _installed_skillsets()
    print(bold("geno-tools"))
    if not installed:
        print(rule("installed"))
        print(dim("  no skillsets installed."))
        print(dim("  geno-tools discover   # see what you can install"))
        return 0

    print(rule(f"installed · {len(installed)}"))
    rows = [_skillset_status(name, check_remote=True) for name in installed]
    name_width = max(len(row["name"]) for row in rows)
    version_width = max(len(row["version"]) for row in rows)
    for row in rows:
        ref = dim(f"{row['variant']}@{row['commit']}")
        line = (
            f"  {bold(row['name'].ljust(name_width))}  "
            f"{row['version'].ljust(version_width)}  {ref}"
        )
        if row["state"]:
            line += f"  {_format_state(row['state'])}"
        print(line)

    behind = [row for row in rows if row["state"].startswith("behind")]
    if behind:
        print()
        print(dim(f"  {len(behind)} behind remote — geno-tools update"))
    return 0


def _skillset_status(full: str, *, check_remote: bool) -> dict:
    worktree = paths.skillset_worktree(full)
    active = dev.active_details(full)
    version = active["version"]

    def git(*arguments: str) -> str:
        try:
            return subprocess.check_output(
                ["git", "-C", str(worktree), *arguments],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""

    state = "" if active["consistent"] else "dev-drift"
    if check_remote and not state:
        if git("status", "--porcelain"):
            state = "dirty"
        else:
            branch = git("branch", "--show-current") or "main"
            try:
                output = subprocess.check_output(
                    ["git", "-C", str(worktree), "ls-remote", "origin", f"refs/heads/{branch}"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                ).strip()
                remote = output.split()[0] if output else ""
            except (
                subprocess.CalledProcessError,
                subprocess.TimeoutExpired,
                FileNotFoundError,
            ):
                remote = ""
                state = "offline"

            if remote:
                local = git("rev-parse", "HEAD")

                def is_ancestor(first: str, second: str) -> bool:
                    return (
                        subprocess.call(
                            ["git", "-C", str(worktree), "merge-base", "--is-ancestor", first, second],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        == 0
                    )

                if remote == local:
                    state = "in-sync"
                elif is_ancestor(local, remote):
                    state = f"behind {remote[:7]}"
                elif is_ancestor(remote, local):
                    state = "ahead"
                else:
                    state = "diverged"

    return {
        "name": full,
        "version": version,
        "variant": active["mode"],
        "commit": active["commit"],
        "state": state,
    }
