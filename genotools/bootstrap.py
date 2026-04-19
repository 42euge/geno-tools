"""SessionStart hook bootstrap + cwd alias materialization.

The gt-bootstrap.sh script is written to ~/.geno-tools/ on first install
and called via Claude Code's SessionStart hook.  It materializes short
`gt-{rest}` aliases in `<cwd>/.claude/skills/` that symlink to the
globally-installed `geno-{tool}-{rest}` skills.

The hook entry is managed in ~/.claude/settings.json by geno-tools.
"""

from __future__ import annotations

import json
from pathlib import Path

from genotools import paths

SETTINGS_FILE = Path.home() / ".claude" / "settings.json"
BOOTSTRAP_SCRIPT = paths.ROOT / "gt-bootstrap.sh"
HOOK_MARKER = "gt-bootstrap"  # substring to find our hook entry

BOOTSTRAP_SH = r'''#!/bin/bash
# geno-tools SessionStart hook: materialize /gt-* aliases in cwd.
# Only runs if <cwd>/.claude/ exists (project is Claude-aware).

GENO_ROOT="$HOME/.geno-tools"
CWD_SKILLS=".claude/skills"

[ -d ".claude" ] || exit 0
mkdir -p "$CWD_SKILLS" 2>/dev/null || exit 0

for skillset_dir in "$GENO_ROOT"/geno-*/; do
    [ -d "$skillset_dir" ] || continue
    active="$skillset_dir/active"
    [ -L "$active" ] || continue
    skills_dir="$(cd "$active" 2>/dev/null && pwd)/skills"
    [ -d "$skills_dir" ] || continue

    skillset_name=$(basename "$skillset_dir")
    tool="${skillset_name#geno-}"

    for skill_dir in "$skills_dir"/*/; do
        [ -d "$skill_dir" ] || continue
        [ -f "$skill_dir/SKILL.md" ] || continue

        skill_name=$(basename "$skill_dir")

        if [ "$skill_name" = "$skillset_name" ]; then
            alias_name="gt-${tool}"
        else
            rest="${skill_name#${skillset_name}-}"
            if [ "$rest" != "$skill_name" ]; then
                alias_name="gt-${rest}"
            else
                alias_name="gt-${skill_name}"
            fi
        fi

        alias_target="$CWD_SKILLS/$alias_name"
        [ -e "$alias_target" ] || [ -L "$alias_target" ] && continue
        ln -s "$skill_dir" "$alias_target"
    done
done
'''


def write_bootstrap_script() -> None:
    BOOTSTRAP_SCRIPT.parent.mkdir(parents=True, exist_ok=True)
    BOOTSTRAP_SCRIPT.write_text(BOOTSTRAP_SH)
    BOOTSTRAP_SCRIPT.chmod(0o755)


def ensure_hook_registered() -> None:
    """Add the SessionStart hook to ~/.claude/settings.json if missing."""
    write_bootstrap_script()

    if not SETTINGS_FILE.exists():
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        settings: dict = {}
    else:
        settings = json.loads(SETTINGS_FILE.read_text())

    hooks = settings.setdefault("hooks", {})
    session_start = hooks.setdefault("SessionStart", [])

    for group in session_start:
        for h in group.get("hooks", []):
            if HOOK_MARKER in h.get("command", ""):
                return  # already registered

    session_start.append({
        "hooks": [{
            "type": "command",
            "command": str(BOOTSTRAP_SCRIPT),
            "timeout": 5,
        }],
    })

    SETTINGS_FILE.write_text(json.dumps(settings, indent=2) + "\n")


def remove_hook() -> None:
    """Remove the SessionStart hook from ~/.claude/settings.json."""
    if not SETTINGS_FILE.exists():
        return
    settings = json.loads(SETTINGS_FILE.read_text())
    session_start = settings.get("hooks", {}).get("SessionStart", [])
    filtered = [
        group for group in session_start
        if not any(HOOK_MARKER in h.get("command", "") for h in group.get("hooks", []))
    ]
    if len(filtered) != len(session_start):
        settings["hooks"]["SessionStart"] = filtered
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2) + "\n")

    if BOOTSTRAP_SCRIPT.exists():
        BOOTSTRAP_SCRIPT.unlink()


def materialize_cwd_aliases(skillsets: list[str] | None = None) -> int:
    """Materialize gt-* aliases in <cwd>/.claude/skills/ for the given skillsets.

    If skillsets is None, do all installed. This is the Python equivalent of
    gt-bootstrap.sh, used by `install --here` and `use --here`.
    """
    cwd_skills = Path.cwd() / ".claude" / "skills"
    cwd_skills.mkdir(parents=True, exist_ok=True)

    if skillsets is None:
        if not paths.ROOT.exists():
            return 0
        skillsets = [
            p.name for p in paths.ROOT.iterdir()
            if p.is_dir() and p.name.startswith("geno-")
        ]

    count = 0
    for full in skillsets:
        active = paths.skillset_active(full)
        if not active.is_symlink():
            continue
        # Resolve for iteration (to see what skill dirs exist).
        resolved_skills = (active.resolve()) / "skills"
        if not resolved_skills.exists():
            continue

        tool = paths.short(full)

        for skill_dir in sorted(resolved_skills.iterdir()):
            if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
                continue

            skill_name = skill_dir.name
            if skill_name == full:
                alias = f"gt-{tool}"
            else:
                rest = skill_name.removeprefix(f"{full}-")
                alias = f"gt-{rest}" if rest != skill_name else f"gt-{skill_name}"

            alias_path = cwd_skills / alias
            if alias_path.exists() or alias_path.is_symlink():
                continue

            # Point through `active` (not resolved) so global `use` propagates.
            alias_path.symlink_to(active / "skills" / skill_name)
            print(f"  ↳ {alias} -> {skill_name}")
            count += 1

    return count


def remove_cwd_aliases(full: str) -> None:
    """Remove gt-* aliases in <cwd>/.claude/skills/ that point into this skillset."""
    cwd_skills = Path.cwd() / ".claude" / "skills"
    if not cwd_skills.exists():
        return
    active = paths.skillset_active(full)
    if not active.is_symlink():
        return
    skillset_path = str(active.resolve())
    for entry in cwd_skills.iterdir():
        if not entry.is_symlink():
            continue
        try:
            target = str(entry.resolve())
        except OSError:
            continue
        if target.startswith(skillset_path):
            entry.unlink()
            print(f"  ↳ removed cwd alias {entry.name}")
