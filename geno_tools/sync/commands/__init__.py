"""Registration and shared presentation for ``geno-tools sync`` commands."""

from __future__ import annotations

import argparse
import sys

from geno_tools.sync.reconcile import ReconcileOptions, ReconcileResult


def _add_reconcile_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--dry-run", action="store_true", help="show the reconciliation plan only"
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="skip removal confirmation"
    )
    parser.add_argument(
        "--no-rebuild",
        action="store_true",
        help="skip deterministic venv rebuilds after repository updates",
    )
    parser.add_argument(
        "--dev-source",
        choices=("ask", "stable", "active"),
        default="ask",
        help="choose Stable or active Dev sources (default: ask interactively)",
    )


def options_from_args(args: argparse.Namespace) -> ReconcileOptions:
    return ReconcileOptions(
        dry_run=args.dry_run,
        yes=args.yes,
        rebuild=not args.no_rebuild,
    )


def render_result(result: ReconcileResult, *, dry_run: bool = False) -> int:
    prefix = "would " if dry_run else ""
    if not result.actions and not result.failures:
        print("already in sync")
    for action in result.actions:
        print(f"  {prefix}{action.kind} {action.name}")
    for failure in result.failures:
        detail = f": {failure.detail}" if failure.detail else ""
        print(f"  failed {failure.kind} {failure.name}{detail}", file=sys.stderr)
    return 1 if result.failures else 0


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "sync", help="compare or reconcile installations across hosts"
    )
    parser.set_defaults(_dispatch=dispatch, _sync_parser=parser)
    commands = parser.add_subparsers(
        dest="sync_action", title="commands", metavar="COMMAND"
    )

    commands.add_parser("export", help="print the local installation lockfile")

    status_parser = commands.add_parser(
        "status", help="compare this installation with configured hosts"
    )
    status_parser.add_argument("hosts", nargs="*", metavar="HOST")

    pull_parser = commands.add_parser(
        "pull", help="make this machine match a source host"
    )
    pull_parser.add_argument("host", nargs="?", metavar="HOST")
    _add_reconcile_flags(pull_parser)

    push_parser = commands.add_parser(
        "push", help="make a destination host match this machine"
    )
    push_parser.add_argument("host", metavar="HOST")
    _add_reconcile_flags(push_parser)

    apply_parser = commands.add_parser(
        "apply", help="reconcile from a lockfile on standard input"
    )
    apply_parser.add_argument("input", choices=["-"], metavar="-")
    _add_reconcile_flags(apply_parser)


def dispatch(args: argparse.Namespace) -> int:
    if args.sync_action is None:
        args._sync_parser.print_help()
        return 0
    from . import apply, export, pull, push, status

    handlers = {
        "apply": apply.run,
        "export": export.run,
        "pull": pull.run,
        "push": push.run,
        "status": status.run,
    }
    return handlers[args.sync_action](args)


__all__ = ["add_parser", "dispatch"]
