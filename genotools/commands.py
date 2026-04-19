"""Subcommand dispatch. Most handlers are stubs until later phases land."""

import argparse
import sys

from genotools import paths, registry


def dispatch(args: argparse.Namespace) -> int:
    handlers = {
        "ls": _ls,
        "install": _install,
        "dev": _dev,
        "fork": _fork,
        "use": _use,
        "promote": _promote,
        "update": _update,
        "remove": _remove,
        "doctor": _doctor,
    }
    return handlers[args.cmd](args)


def _ls(args: argparse.Namespace) -> int:
    if args.available:
        for name, url in registry.available().items():
            print(f"  {name:<12} {url}")
        return 0

    if not paths.ROOT.exists():
        print("no skillsets installed")
        return 0

    installed = sorted(
        p.name for p in paths.ROOT.iterdir()
        if p.is_dir() and p.name.startswith("geno-")
        and p.name not in ("geno-bootstrap",)
    )
    if not installed:
        print("no skillsets installed")
        return 0

    for full in installed:
        active = paths.skillset_active(full)
        target = active.readlink().name if active.is_symlink() else "?"
        print(f"  {full:<24} active: {target}")
    return 0


def _install(args: argparse.Namespace) -> int:
    if args.here:
        return _todo(f"install --here {args.name}: cwd alias materialization")
    return _todo(f"install {args.name}: clone, worktree, venv, skill install (npx skills)")


def _dev(args: argparse.Namespace) -> int:
    return _todo(f"dev {args.name} {args.path}: symlink local checkout as main worktree")


def _fork(args: argparse.Namespace) -> int:
    return _todo(f"fork {args.name} {args.variant}: git worktree add"
                 + (" + isolated venv" if args.isolated_venv else ""))


def _use(args: argparse.Namespace) -> int:
    scope = "cwd" if args.here else "global"
    return _todo(f"use {args.spec} ({scope}): repoint active or cwd alias")


def _promote(args: argparse.Namespace) -> int:
    return _todo(f"promote {args.name} {args.variant}: merge variant -> main")


def _update(args: argparse.Namespace) -> int:
    target = args.name or "<all>"
    return _todo(f"update {target}: git pull on main worktree")


def _remove(args: argparse.Namespace) -> int:
    flag = " --keep-data" if args.keep_data else ""
    return _todo(f"remove {args.name}{flag}: uninstall skill, drop ~/.geno-tools/geno-{args.name}/")


def _doctor(_: argparse.Namespace) -> int:
    return _todo("doctor: verify symlinks, worktrees, venvs")


def _todo(msg: str) -> int:
    print(f"[not yet implemented] {msg}", file=sys.stderr)
    return 2
