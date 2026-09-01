"""Print the dependency tree for an installed skillset."""

from __future__ import annotations

import argparse
import sys

from .. import paths
from .install import _get_requires


def run(args: argparse.Namespace) -> int:
    full = paths.normalize(args.name)
    if not paths.skillset_root(full).exists():
        print(f"not installed: {full}", file=sys.stderr)
        return 1
    _print_dep_tree(full, indent=0, seen=set())
    return 0


def _print_dep_tree(full: str, indent: int, seen: set[str]) -> None:
    prefix = "  " * indent
    installed = paths.skillset_root(full).exists()
    print(f"{prefix}{full}{'' if installed else ' (missing)'}")
    if full in seen:
        if _get_requires(full):
            print(f"{prefix}  (circular, skipped)")
        return
    seen.add(full)
    if not installed:
        return
    for dependency in _get_requires(full):
        _print_dep_tree(paths.normalize(dependency), indent + 1, seen)
