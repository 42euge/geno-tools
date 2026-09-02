"""Skill-manager command registration and dispatch."""

from __future__ import annotations

import argparse

from . import audit, dev, discover, install, remove, scan, status, upgrade


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the skillset lifecycle commands."""
    install_parser = subparsers.add_parser("install", help="install a skillset")
    install_parser.set_defaults(_dispatch=dispatch)
    install_parser.add_argument(
        "name", help="full repo name (e.g. geno-<name>), git URL, or local path"
    )

    uninstall_parser = subparsers.add_parser(
        "uninstall", help="uninstall a skillset"
    )
    uninstall_parser.set_defaults(_dispatch=dispatch)
    uninstall_parser.add_argument("name")
    uninstall_parser.add_argument(
        "--keep-data", action="store_true", help="preserve the skillset venv"
    )

    status_parser = subparsers.add_parser(
        "status", help="installed skillsets: version, commit, drift vs remote"
    )
    status_parser.set_defaults(_dispatch=dispatch)

    update_parser = subparsers.add_parser(
        "update", help="update installed skillset(s) to latest"
    )
    update_parser.set_defaults(_dispatch=dispatch)
    update_parser.add_argument(
        "name", nargs="?", help="skillset to update; omit for all"
    )

    dev_parser = subparsers.add_parser(
        "dev", help="activate or restore a local skillset development checkout"
    )
    dev_parser.set_defaults(_dispatch=dispatch, _dev_parser=dev_parser)
    dev_commands = dev_parser.add_subparsers(
        dest="dev_action", title="commands", metavar="COMMAND"
    )
    dev_activate = dev_commands.add_parser(
        "activate", help="select a local checkout and its isolated runtime"
    )
    dev_activate.add_argument("checkout")
    dev_status = dev_commands.add_parser(
        "status", help="show stable/dev selection and consistency"
    )
    dev_status.add_argument("name", nargs="?")
    dev_deactivate = dev_commands.add_parser(
        "deactivate", help="restore an installed skillset's stable main checkout"
    )
    dev_deactivate.add_argument("name")

    discover_parser = subparsers.add_parser(
        "discover", help="find & list installable skillsets, by category"
    )
    discover_parser.set_defaults(_dispatch=dispatch)
    discover_parser.add_argument(
        "--refresh",
        action="store_true",
        help="force a network refresh (otherwise auto-refreshes if >30min stale)",
    )

    scan_parser = subparsers.add_parser(
        "scan", help="scan for new uninstalled skillsets and queue candidates"
    )
    scan_parser.set_defaults(_dispatch=dispatch)
    scan_parser.add_argument(
        "--namespace", help="filter by namespace prefix (e.g. 'geno', 'acme')"
    )
    scan_parser.add_argument(
        "--dry-run", action="store_true", help="list candidates without writing to queue"
    )

    audit_parser = subparsers.add_parser(
        "audit",
        help="check a skillset repository for geno compliance",
        description="Audit skillset compliance without modifying the target.",
    )
    audit_parser.set_defaults(_dispatch=dispatch, _audit_parser=audit_parser)
    audit_commands = audit_parser.add_subparsers(
        dest="audit_cmd", title="commands", metavar="COMMAND"
    )
    audit_check = audit_commands.add_parser(
        "check", help="run the deterministic compliance checklist"
    )
    audit_check.add_argument(
        "target",
        nargs="?",
        default=".",
        help="path, installed name, registry name, or git URL (default: current directory)",
    )
    audit_check.add_argument(
        "--json", action="store_true", help="emit the complete machine-readable report"
    )
    audit_check.add_argument(
        "--strict", action="store_true", help="return nonzero for warnings as well as failures"
    )


def dispatch(args: argparse.Namespace) -> int:
    if args.cmd == "audit":
        if args.audit_cmd is None:
            args._audit_parser.print_help()
            return 0
        return audit.run(args)
    if args.cmd == "dev":
        if args.dev_action is None:
            args._dev_parser.print_help()
            return 0
        return dev.run(args)
    handlers = {
        "install": install.run,
        "uninstall": remove.run,
        "status": status.run,
        "update": upgrade.run,
        "discover": discover.run,
        "scan": scan.run,
    }
    return handlers[args.cmd](args)


__all__ = ["add_parser", "dispatch"]
