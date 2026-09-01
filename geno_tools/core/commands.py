"""Commands that manage geno-tools itself."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import yaml

from . import config, uninstall
from .terminal import bold, dim, green, is_tty, red, rule, yellow

REPO_URL = "https://github.com/42euge/geno-tools.git"

SYSTEM_HELP_EPILOG = """\
common tasks:
  geno-tools system update               Update geno-tools itself

safety workflow:
  geno-tools system uninstall --dry-run  Preview everything that would be removed
  geno-tools system uninstall            Review the plan and confirm explicitly

User data under ~/.geno is always preserved.
"""


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    system_parser = subparsers.add_parser(
        "system",
        help="update, inspect, or remove the geno-tools installation",
        description=(
            "Manage the geno-tools installation. Commands here can affect every "
            "installed skillset."
        ),
        epilog=SYSTEM_HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    system_parser.set_defaults(_dispatch=dispatch, _system_parser=system_parser)
    system_commands = system_parser.add_subparsers(
        dest="system_cmd", title="commands", metavar="COMMAND"
    )
    system_commands.add_parser(
        "update", help="update geno-tools itself to the latest version"
    )
    uninstall_parser = system_commands.add_parser(
        "uninstall",
        help="remove all geno-tools-managed skillsets and registrations",
        description=(
            "Remove all geno-tools-managed skillsets, agent registrations, and "
            "legacy installation files. User data under ~/.geno is preserved."
        ),
    )
    uninstall_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show exactly what would be removed and kept, without deleting",
    )
    uninstall_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="skip explicit confirmation (for automation)",
    )

    parser = subparsers.add_parser(
        "config", help="show or set geno ecosystem config values"
    )
    parser.set_defaults(_dispatch=dispatch)
    sub = parser.add_subparsers(dest="config_cmd", required=True)
    sub.add_parser("show", help="print current config")
    set_parser = sub.add_parser("set", help="set a config key")
    set_parser.add_argument("key", help="dot-path key (e.g. aliases.command_prefix)")
    set_parser.add_argument("value", help="value to set")


def dispatch(args: argparse.Namespace) -> int:
    if args.cmd == "system":
        if args.system_cmd is None:
            args._system_parser.print_help()
            return 0
        handlers = {"update": _self_update, "uninstall": uninstall.run}
        return handlers[args.system_cmd](args)
    if args.config_cmd == "show":
        return _config_show()
    return _config_set(args.key, args.value)


def _self_update(_: argparse.Namespace) -> int:
    print(bold("geno-tools system update"))
    print(rule("self-update"))
    ok = True

    brew = _managing_brew()
    if brew:
        print(dim("  upgrading CLI via Homebrew …"))
        rc = subprocess.call([brew, "upgrade", "geno-tools"])
        if rc == 0:
            print(green("  ✓ CLI updated"))
        else:
            ok = False
            print(red("  ✗ Homebrew upgrade failed — run brew upgrade geno-tools"))
    else:
        pipx = shutil.which("pipx") or _find_pipx()
        if pipx:
            print(dim(f"  reinstalling CLI via pipx from {REPO_URL} …"))
            rc = subprocess.call([pipx, "install", "--force", f"git+{REPO_URL}"])
            if rc == 0:
                print(green("  ✓ CLI updated"))
            else:
                ok = False
                print(red("  ✗ pipx install failed — run /geno-tools-setup"))
        else:
            ok = False
            print(yellow("  ! pipx not found — run /geno-tools-setup to install the CLI"))

    print()
    print(dim("  installed skillsets are unaffected; re-register with:"))
    print("    geno-tools update")
    return 0 if ok else 1


def _managing_brew() -> str | None:
    """Return Homebrew when this package lives in its formula Cellar."""
    package_path = Path(__file__).resolve()
    if not any(
        parent.name == "geno-tools" and parent.parent.name == "Cellar"
        for parent in package_path.parents
    ):
        return None
    return shutil.which("brew")


def _find_pipx() -> str | None:
    for path in [
        Path.home() / ".local" / "bin" / "pipx",
        *Path.home().glob("Library/Python/*/bin/pipx"),
    ]:
        if path.exists():
            return str(path)
    return None


def _config_show() -> int:
    print(yaml.safe_dump(config.load(), sort_keys=False).rstrip())
    return 0


def _config_set(key: str, value: str) -> int:
    config.set_config(key, value)
    if is_tty():
        print(f"set {key} in ~/.geno/config.yaml")
    return 0
