"""Commands that manage geno-tools itself."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import yaml

from . import config
from .terminal import bold, dim, green, is_tty, red, rule, yellow

REPO_URL = "https://github.com/42euge/geno-tools.git"
_CC_MARKETPLACE = Path.home() / ".claude" / "plugins" / "marketplaces" / "geno-tools"


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    update = subparsers.add_parser(
        "update", help="update geno-tools itself to the latest version"
    )
    update.set_defaults(_dispatch=dispatch)

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
    if args.cmd == "update":
        return _self_update()
    if args.config_cmd == "show":
        return _config_show()
    return _config_set(args.key, args.value)


def _self_update() -> int:
    print(bold("geno-tools update"))
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

    if (_CC_MARKETPLACE / ".git").exists():
        print(dim("  refreshing Claude Code marketplace clone …"))
        rc = subprocess.call(
            ["git", "-C", str(_CC_MARKETPLACE), "pull", "--quiet", "--ff-only"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(
            green("  ✓ marketplace refreshed")
            if rc == 0
            else yellow("  ! marketplace refresh skipped (diverged?)")
        )

    print()
    print(dim("  to load the new plugin in Claude Code, run:"))
    print("    /plugin install geno-tools@geno-tools")
    print("    /reload-plugins")
    print(dim("  (Codex/Antigravity: re-run the plugin install for your agent)"))
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
