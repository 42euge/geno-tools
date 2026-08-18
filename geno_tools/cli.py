import argparse
import sys

from geno_tools import __version__
from geno_tools.core import add_parser as add_core_parser
from geno_tools.skills_manager import add_parser as add_skills_parser


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="geno-tools")
    parser.add_argument("--version", action="version", version=f"geno-tools {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    add_skills_parser(sub)
    add_core_parser(sub)

    args = parser.parse_args(argv)

    return args._dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
