"""Remove geno-tools' installed footprint while preserving user data."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from geno_tools.core.terminal import bold, dim, green, red, rule

from .. import paths
from .install import SYSTEM_BIN, _remove_bin_symlinks, _uninstall_skills_via_npx
from .status import _installed_skillsets

_CC_MARKETPLACE = Path.home() / ".claude" / "plugins" / "marketplaces" / "geno-tools"
_AGENT_SKILL_DIRS = [
    Path.home() / ".claude" / "skills",
    Path.home() / ".agents" / "skills",
    Path.home() / ".codex" / "skills",
    Path.home() / ".cursor" / "skills",
    Path.home() / ".gemini" / "skills",
    Path.home() / ".gemini" / "antigravity" / "skills",
    Path.home() / ".copilot" / "skills",
]
_CC_PLUGIN_DIRS = [
    Path.home() / ".claude" / "plugins" / "cache" / "geno-tools",
    Path.home() / ".claude" / "plugins" / "data" / "geno-tools-geno-tools",
    Path.home() / ".claude" / "plugins" / "data" / "geno-tools-skills-dir",
    _CC_MARKETPLACE,
]


def run(args: argparse.Namespace) -> int:
    skillsets = _installed_skillsets() if paths.ROOT.exists() else []
    agent_skills = [
        entry
        for directory in _AGENT_SKILL_DIRS
        if directory.exists()
        for entry in sorted(directory.iterdir())
        if entry.name.startswith(("geno-", "geno-tools", "geno-iso"))
    ]

    bin_links: list[Path] = []
    if SYSTEM_BIN.exists():
        managed_prefix = str(paths.ROOT)
        for entry in SYSTEM_BIN.iterdir():
            if not entry.is_symlink():
                continue
            try:
                target = (entry.parent / entry.readlink()).resolve()
            except OSError:
                continue
            if str(target).startswith(managed_prefix):
                bin_links.append(entry)

    plugin_dirs = [directory for directory in _CC_PLUGIN_DIRS if directory.exists()]
    kept_user_data = (
        [
            entry
            for entry in sorted(paths.GENO_DIR.iterdir())
            if not entry.name.startswith(".")
        ]
        if paths.GENO_DIR.exists()
        else []
    )

    print(bold("geno-tools skills uninstall"))
    print(rule("plan"))
    _print_section(
        f"skillsets under {paths.ROOT}",
        skillsets,
        lambda name: f"{paths.ROOT}/{name}",
    )
    _print_section("agent skill registrations", agent_skills)
    _print_section("bin symlinks", bin_links)
    _print_section("Claude Code plugin/marketplace clones", plugin_dirs)
    print()
    print(bold(f"  {green('KEPT')} — your data, never touched:"))
    if kept_user_data:
        for item in kept_user_data:
            print(f"    keep    {item}")
    else:
        print(dim("    (no user data found in ~/.geno)"))

    total = len(skillsets) + len(agent_skills) + len(bin_links) + len(plugin_dirs)
    print()
    if total == 0:
        print(green("nothing to remove — geno-tools is not installed here."))
    if args.dry_run:
        print(dim("dry-run — nothing was deleted."))
        _print_pkg_removal_hint()
        return 0
    if total > 0 and not args.yes:
        try:
            response = input(f"remove {total} item(s)? [y/N] ").strip().lower()
        except EOFError:
            response = ""
        if response not in ("y", "yes"):
            print("aborted.")
            return 1

    for name in skillsets:
        _uninstall_skills_via_npx(name)
        _remove_bin_symlinks(name, system_bin=SYSTEM_BIN)
        shutil.rmtree(paths.skillset_root(name), ignore_errors=True)
        print(f"  removed skillset {name}")
    for skill in agent_skills:
        if skill.is_dir() and not skill.is_symlink():
            shutil.rmtree(skill, ignore_errors=True)
        else:
            skill.unlink(missing_ok=True)
        print(f"  removed {skill}")
    for link in bin_links:
        link.unlink(missing_ok=True)
        print(f"  removed {link}")
    for directory in plugin_dirs:
        shutil.rmtree(directory, ignore_errors=True)
        print(f"  removed {directory}")
    if paths.ROOT.exists() and not any(paths.ROOT.iterdir()):
        shutil.rmtree(paths.ROOT, ignore_errors=True)
        print(f"  removed empty {paths.ROOT}")

    _clean_agent_json_configs()
    print(green("\nuninstalled geno-tools' on-disk footprint."))
    _print_pkg_removal_hint()
    return 0


def _print_section(title, items, render=str) -> None:
    print(bold(f"  {title} ({len(items)})"))
    for item in items:
        print(f"    {red('remove')}  {render(item)}")
    if not items:
        print(dim("    (none)"))


def _print_pkg_removal_hint() -> None:
    print()
    print(bold("last step — remove the CLI package (a process can't delete itself):"))
    print("  pipx uninstall geno-tools        # if installed via pipx")
    print(dim("  # or, if installed via Homebrew:"))
    print("  brew uninstall 42euge/geno/geno  # NOTE: may cascade shared deps; check `brew uses`")


def _clean_agent_json_configs() -> None:
    targets = [Path.home() / ".claude" / "settings.json", Path.home() / ".claude.json"]
    for path in targets:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        changed = False
        for key in ("enabledPlugins", "extraKnownMarketplaces", "installedPlugins"):
            value = data.get(key)
            if not isinstance(value, dict):
                continue
            for name in [name for name in value if "geno-tools" in name or "geno-iso" in name]:
                del value[name]
                changed = True
        if changed:
            path.write_text(json.dumps(data, indent=2) + "\n")
            print(f"  cleaned geno entries from {path}")


_uninstall = run
