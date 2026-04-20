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
# Copies SKILL.md with the frontmatter `name:` line stripped so Claude
# uses the folder name (gt-*) instead of the original skill name.
# Alias rule: strip "geno-" prefix, add "gt-" prefix.

GENO_ROOT="$HOME/.geno-tools"
CWD_SKILLS=".claude/skills"

[ -d ".claude" ] || exit 0
mkdir -p "$CWD_SKILLS" 2>/dev/null || exit 0

copy_skill() {
    local src="$1" alias_name="$2"
    local alias_dir="$CWD_SKILLS/$alias_name"
    [ -f "$alias_dir/SKILL.md" ] && return
    mkdir -p "$alias_dir"
    sed '/^name:/d' "$src" > "$alias_dir/SKILL.md"
}

for skillset_dir in "$GENO_ROOT"/geno-*/; do
    [ -d "$skillset_dir" ] || continue
    active="$skillset_dir/active"
    [ -L "$active" ] || continue
    resolved="$(cd "$active" 2>/dev/null && pwd)"

    skillset_name=$(basename "$skillset_dir")

    # Root SKILL.md (umbrella skill)
    if [ -f "$resolved/SKILL.md" ]; then
        copy_skill "$resolved/SKILL.md" "gt-${skillset_name#geno-}"
    fi

    # Individual skills in skills/
    if [ -d "$resolved/skills" ]; then
        for skill_dir in "$resolved/skills"/*/; do
            [ -d "$skill_dir" ] || continue
            [ -f "$skill_dir/SKILL.md" ] || continue
            skill_name=$(basename "$skill_dir")
            copy_skill "$skill_dir/SKILL.md" "gt-${skill_name#geno-}"
        done
    fi
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


def materialize_cwd_aliases(skillsets: list[str] | None = None,
                            variant_override: str | None = None) -> int:
    """Materialize gt-* aliases in <cwd>/.claude/skills/ for the given skillsets.

    Copies SKILL.md with the frontmatter `name` line stripped so Claude Code
    uses the folder name (gt-*) rather than the original skill name.

    If variant_override is set, read from that variant's worktree instead of
    active (used by `use --here`).
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
        if variant_override:
            source_root = paths.skillset_worktree(full, variant_override)
        else:
            active = paths.skillset_active(full)
            if not active.is_symlink():
                continue
            source_root = active.resolve()

        # Collect SKILL.md sources: root-level (umbrella) + skills/*/
        skill_sources: list[tuple[str, Path]] = []

        root_skill = source_root / "SKILL.md"
        if root_skill.exists():
            skill_sources.append((full, root_skill))

        skills_dir = source_root / "skills"
        if skills_dir.exists():
            for skill_dir in sorted(skills_dir.iterdir()):
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    skill_sources.append((skill_dir.name, skill_dir / "SKILL.md"))

        if not skill_sources:
            continue

        for skill_name, skill_md in skill_sources:
            alias = "gt-" + skill_name.removeprefix("geno-")

            alias_dir = cwd_skills / alias
            alias_dir.mkdir(parents=True, exist_ok=True)
            _copy_skill_without_name(skill_md, alias_dir / "SKILL.md")
            print(f"  ↳ {alias} -> {skill_name}")
            count += 1

    return count


def _copy_skill_without_name(src: Path, dst: Path) -> None:
    """Copy a SKILL.md, stripping the frontmatter `name:` line."""
    import re
    content = src.read_text()
    content = re.sub(r'^name:\s+.*\n', '', content, count=1, flags=re.MULTILINE)
    dst.write_text(content)


def remove_cwd_aliases(full: str) -> None:
    """Remove gt-* aliases in <cwd>/.claude/skills/ for this skillset."""
    cwd_skills = Path.cwd() / ".claude" / "skills"
    if not cwd_skills.exists():
        return
    tool = paths.short(full)
    prefix = f"gt-{tool}"
    prefix_long = f"gt-"
    for entry in cwd_skills.iterdir():
        if not entry.name.startswith("gt-"):
            continue
        if not entry.is_dir():
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.exists():
            continue
        # Check if this alias was derived from this skillset by checking
        # if the content matches any skill in the skillset.
        active = paths.skillset_active(full)
        if not active.is_symlink():
            continue
        skills_dir = active.resolve() / "skills"
        if not skills_dir.exists():
            continue
        derived = _alias_matches_skillset(entry.name, full, skills_dir)
        if derived:
            import shutil
            shutil.rmtree(entry)
            print(f"  ↳ removed cwd alias {entry.name}")


def _alias_matches_skillset(alias: str, full: str, skills_dir: Path) -> bool:
    """Check if a gt-* alias name could have been derived from this skillset."""
    # Umbrella: gt-{tool} matches the root SKILL.md
    expected_umbrella = "gt-" + full.removeprefix("geno-")
    if alias == expected_umbrella:
        return True
    # Individual skills: gt-{skill_name_without_geno_prefix}
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        expected = "gt-" + skill_dir.name.removeprefix("geno-")
        if alias == expected:
            return True
    return False
