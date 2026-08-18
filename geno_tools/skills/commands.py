"""Parser and dispatcher for ``geno-tools skills`` commands."""

from __future__ import annotations

import argparse


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the skillset lifecycle command group."""
    parser = subparsers.add_parser(
        "skills", help="install, remove, and inspect skillsets"
    )
    sub = parser.add_subparsers(dest="skills_cmd", required=True)

    install = sub.add_parser("install", help="install a skillset")
    install.add_argument(
        "name",
        help="full repo name (e.g. geno-<name>), git URL, or local path",
    )

    uninstall = sub.add_parser(
        "uninstall",
        help="fully remove geno-tools and all it installed (inverse of install)",
    )
    uninstall.add_argument(
        "--dry-run",
        action="store_true",
        help="show exactly what would be removed and kept, without deleting",
    )
    uninstall.add_argument(
        "--yes", "-y", action="store_true", help="skip the confirmation prompt"
    )
    upgrade = sub.add_parser(
        "upgrade", help="upgrade installed skillset(s) to latest"
    )
    upgrade.add_argument("name", nargs="?", help="skillset to upgrade; omit for all")

    remove = sub.add_parser("remove", help="uninstall a skillset")
    remove.add_argument("name")
    remove.add_argument(
        "--keep-data", action="store_true", help="preserve venvs/ and worktrees"
    )

    deps = sub.add_parser("deps", help="show dependency tree for a skillset")
    deps.add_argument("name", help="skillset name")

    discover = sub.add_parser(
        "discover", help="find & list installable skillsets, by category"
    )
    discover.add_argument(
        "--refresh",
        action="store_true",
        help="force a network refresh (otherwise auto-refreshes if >30min stale)",
    )

    scan = sub.add_parser(
        "scan", help="scan for new uninstalled skillsets and queue candidates"
    )
    scan.add_argument(
        "--namespace", help="filter by namespace prefix (e.g. 'geno', 'acme')"
    )
    scan.add_argument(
        "--dry-run", action="store_true", help="list candidates without writing to queue"
    )


def dispatch(args: argparse.Namespace) -> int:
    """Dispatch a parsed ``skills`` subcommand."""
    from geno_tools import commands

    handlers = {
        "install": commands._install,
        "uninstall": commands._uninstall,
        "upgrade": commands._upgrade,
        "remove": commands._remove,
        "deps": commands._deps,
        "discover": commands._discover,
        "scan": commands._scan,
    }
    return handlers[args.skills_cmd](args)
