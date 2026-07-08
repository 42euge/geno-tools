import argparse
import sys

from geno_tools import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="geno-tools")
    parser.add_argument("--version", action="version", version=f"geno-tools {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # status — installed skillsets, versions, and drift vs remote main
    sub.add_parser("status", help="installed skillsets: version, commit, drift vs remote")
    # ls — back-compat alias for status (supports the old --available/--check flags)
    p_ls = sub.add_parser("ls", help="alias for status (deprecated)")
    p_ls.add_argument("--available", action="store_true", help="alias for `discover`")
    p_ls.add_argument("--check", action="store_true",
                      help="deprecated no-op (status always checks remote)")

    p_install = sub.add_parser("install", help="install a skillset")
    p_install.add_argument("name", help="full repo name (e.g. geno-<name>), git URL, or local path")
    p_install.add_argument("--here", action="store_true",
                           help="materialize cwd alias symlinks for this skillset")

    p_dev = sub.add_parser("dev", help="symlink a local checkout as the main worktree")
    p_dev.add_argument("name")
    p_dev.add_argument("path")

    p_fork = sub.add_parser("fork", help="create a variant worktree off main")
    p_fork.add_argument("name")
    p_fork.add_argument("variant", help="variant id (becomes the worktree dir + git branch name)")
    p_fork.add_argument("--isolated-venv", action="store_true",
                        help="create a fresh venv for this variant instead of sharing")

    p_use = sub.add_parser("use", help="select a variant")
    p_use.add_argument("spec", help="<name>@<variant> (e.g. geno-<name>@exp-1)")
    p_use.add_argument("--here", action="store_true",
                       help="cwd-only override; otherwise repoint global active symlink")

    p_promote = sub.add_parser("promote", help="merge variant into main (no upstream push)")
    p_promote.add_argument("name")
    p_promote.add_argument("variant")

    # update — update geno-tools ITSELF to the latest version
    sub.add_parser("update", help="update geno-tools itself to the latest version")
    # upgrade — upgrade installed skillset(s) to latest (git pull + re-register)
    p_upgrade = sub.add_parser("upgrade", help="upgrade installed skillset(s) to latest")
    p_upgrade.add_argument("name", nargs="?", help="skillset to upgrade; omit for all")

    p_rm = sub.add_parser("remove", help="uninstall a skillset")
    p_rm.add_argument("name")
    p_rm.add_argument("--keep-data", action="store_true",
                      help="preserve venvs/ and worktrees")

    p_deps = sub.add_parser("deps", help="show dependency tree for a skillset")
    p_deps.add_argument("name", help="skillset name")

    sub.add_parser("doctor", help="verify symlinks, worktrees, venvs")

    # durability layer for the audit/run skill — deterministic checks the skill delegates to
    p_audit = sub.add_parser("audit", help="check a repo for ecosystem compliance (backs the audit skill)")
    p_audit.add_argument("path", nargs="?", default=".", help="repo path (default: cwd)")

    p_disc = sub.add_parser("discover", help="find & list installable skillsets, by category")
    p_disc.add_argument("--refresh", action="store_true",
                        help="force a network refresh (otherwise auto-refreshes if >30min stale)")

    p_scan = sub.add_parser("scan", help="scan for new uninstalled skillsets and queue candidates")
    p_scan.add_argument("--namespace", help="filter by namespace prefix (e.g. 'geno', 'acme')")
    p_scan.add_argument("--dry-run", action="store_true", help="list candidates without writing to queue")

    p_docs = sub.add_parser("docs", help="compile skill documentation from SKILL.md files")
    p_docs.add_argument("--docs-dir", type=str, default=None,
                        help="MkDocs docs/ directory (default: auto-detect)")
    p_docs.add_argument("--extra-dir", type=str, action="append", default=[],
                        help="additional directory to scan for skills")
    p_docs.add_argument("--dry-run", action="store_true",
                        help="print without writing files")

    args = parser.parse_args(argv)

    from geno_tools import commands
    return commands.dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
