"""Skill-manager command registration and dispatch."""

from __future__ import annotations

import argparse

from . import deps, discover, install, remove, scan, status, uninstall, upgrade


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the skillset lifecycle commands."""
    status_parser = subparsers.add_parser(
        "status", help="installed skillsets: version, commit, drift vs remote"
    )
    status_parser.set_defaults(_dispatch=dispatch)

    parser = subparsers.add_parser(
        "skills", help="install, remove, and inspect skillsets"
    )
    parser.set_defaults(_dispatch=dispatch)
    commands = parser.add_subparsers(dest="skills_cmd", required=True)

    install_parser = commands.add_parser("install", help="install a skillset")
    install_parser.add_argument(
        "name", help="full repo name (e.g. geno-<name>), git URL, or local path"
    )

    uninstall_parser = commands.add_parser(
        "uninstall",
        help="fully remove geno-tools and all it installed (inverse of install)",
    )
    uninstall_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show exactly what would be removed and kept, without deleting",
    )
    uninstall_parser.add_argument(
        "--yes", "-y", action="store_true", help="skip the confirmation prompt"
    )

    upgrade_parser = commands.add_parser(
        "upgrade", help="upgrade installed skillset(s) to latest"
    )
    upgrade_parser.add_argument(
        "name", nargs="?", help="skillset to upgrade; omit for all"
    )

    remove_parser = commands.add_parser("remove", help="uninstall a skillset")
    remove_parser.add_argument("name")
    remove_parser.add_argument(
        "--keep-data", action="store_true", help="preserve the skillset venv"
    )

    deps_parser = commands.add_parser(
        "deps", help="show dependency tree for a skillset"
    )
    deps_parser.add_argument("name", help="skillset name")

    discover_parser = commands.add_parser(
        "discover", help="find & list installable skillsets, by category"
    )
    discover_parser.add_argument(
        "--refresh",
        action="store_true",
        help="force a network refresh (otherwise auto-refreshes if >30min stale)",
    )

    scan_parser = commands.add_parser(
        "scan", help="scan for new uninstalled skillsets and queue candidates"
    )
    scan_parser.add_argument(
        "--namespace", help="filter by namespace prefix (e.g. 'geno', 'acme')"
    )
    scan_parser.add_argument(
        "--dry-run", action="store_true", help="list candidates without writing to queue"
    )


def dispatch(args: argparse.Namespace) -> int:
    if args.cmd == "status":
        return status.run(args)
    handlers = {
        "install": install.run,
        "uninstall": uninstall.run,
        "upgrade": upgrade.run,
        "remove": remove.run,
        "deps": deps.run,
        "discover": discover.run,
        "scan": scan.run,
    }
    return handlers[args.skills_cmd](args)


__all__ = ["add_parser", "dispatch"]
