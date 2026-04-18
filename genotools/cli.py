import argparse
import sys

from genotools import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="geno-tools")
    parser.add_argument("--version", action="version", version=f"geno-tools {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ls = sub.add_parser("ls", help="list installed skillsets")
    p_ls.add_argument("--available", action="store_true", help="list skillsets in the registry")

    p_install = sub.add_parser("install", help="install a skillset")
    p_install.add_argument("name", help="skillset name (e.g. media) or git URL / local path")
    p_install.add_argument("-a", "--agent", action="append", default=None,
                           help="target agent (repeatable; default: claude-code)")
    p_install.add_argument("--copy", action="store_true", help="copy instead of symlink")
    p_install.add_argument("--project", action="store_true",
                           help="install into ./.claude/ etc. instead of global")

    p_dev = sub.add_parser("dev", help="link a local dev checkout of a skillset")
    p_dev.add_argument("name", help="skillset name")
    p_dev.add_argument("path", help="path to local repo")
    p_dev.add_argument("-a", "--agent", action="append", default=None)

    p_rm = sub.add_parser("remove", help="uninstall a skillset")
    p_rm.add_argument("name")
    p_rm.add_argument("--keep-data", action="store_true",
                      help="preserve configs/ and venvs/ in ~/.geno-tools/geno-{name}/")

    p_up = sub.add_parser("update", help="pull latest for a skillset")
    p_up.add_argument("name", nargs="?", help="omit to update all")

    sub.add_parser("doctor", help="verify links, venvs, and targets")

    args = parser.parse_args(argv)

    # Lazy imports so `--version` and `--help` stay fast.
    from genotools import commands
    return commands.dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
