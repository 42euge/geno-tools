"""Remove one installed skillset."""

from __future__ import annotations

import argparse
import shutil
import sys

from .. import paths
from .install import _remove_bin_symlinks, _uninstall_skills_via_npx


def run(args: argparse.Namespace) -> int:
    full = paths.normalize(args.name)
    root = paths.skillset_root(full)
    if not root.exists():
        print(f"not installed: {full}", file=sys.stderr)
        return 1

    _uninstall_skills_via_npx(full)
    _remove_bin_symlinks(full)
    if args.keep_data:
        for child in root.iterdir():
            if child.name == "venvs":
                continue
            if child.is_symlink() or child.is_file():
                child.unlink()
            else:
                shutil.rmtree(child, ignore_errors=True)
    else:
        shutil.rmtree(root, ignore_errors=True)

    print(f"removed {full}")
    return 0
