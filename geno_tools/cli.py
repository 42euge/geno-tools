import argparse
import sys

from geno_tools import __version__
from geno_tools.skills import add_parser as add_skills_parser


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="geno-tools")
    parser.add_argument("--version", action="version", version=f"geno-tools {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # status — installed skillsets, versions, and drift vs remote main
    sub.add_parser("status", help="installed skillsets: version, commit, drift vs remote")

    add_skills_parser(sub)

    # update — update geno-tools ITSELF to the latest version
    sub.add_parser("update", help="update geno-tools itself to the latest version")

    # config — read/write ~/.geno/config.yaml (and settings.json for secrets)
    p_cfg = sub.add_parser("config", help="show or set geno ecosystem config values")
    cfg_sub = p_cfg.add_subparsers(dest="config_cmd", required=True)
    cfg_sub.add_parser("show", help="print current config (token redacted)")
    p_cfg_set = cfg_sub.add_parser("set", help="set a config key (dot-path, e.g. llm.endpoint)")
    p_cfg_set.add_argument("key", help="dot-path key (e.g. llm.endpoint, llm.token, llm.model)")
    p_cfg_set.add_argument("value", help="value to set")

    args = parser.parse_args(argv)

    from geno_tools import commands
    return commands.dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
