import argparse
import sys

from genotools import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="geno-tools")
    parser.add_argument("--version", action="version", version=f"geno-tools {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ls = sub.add_parser("ls", help="list installed skillsets and their active variant")
    p_ls.add_argument("--available", action="store_true", help="list registry")

    p_install = sub.add_parser("install", help="install a skillset")
    p_install.add_argument("name", help="full repo name (e.g. geno-media), git URL, or local path")
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
    p_use.add_argument("spec", help="<name>@<variant> (e.g. geno-media@exp-1)")
    p_use.add_argument("--here", action="store_true",
                       help="cwd-only override; otherwise repoint global active symlink")

    p_promote = sub.add_parser("promote", help="merge variant into main (no upstream push)")
    p_promote.add_argument("name")
    p_promote.add_argument("variant")

    p_update = sub.add_parser("update", help="git pull on main worktree")
    p_update.add_argument("name", nargs="?", help="omit to update all")

    p_rm = sub.add_parser("remove", help="uninstall a skillset")
    p_rm.add_argument("name")
    p_rm.add_argument("--keep-data", action="store_true",
                      help="preserve venvs/ and worktrees")

    sub.add_parser("doctor", help="verify symlinks, worktrees, venvs")

    p_disc = sub.add_parser("discover", help="list candidate skillsets from configured sources")
    p_disc.add_argument("--dry-run", action="store_true",
                        help="print candidates without installing (default behavior)")

    args = parser.parse_args(argv)

    from genotools import commands
    return commands.dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
