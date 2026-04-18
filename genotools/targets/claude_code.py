"""Claude Code target adapter.

Install locations:
  global : ~/.claude/skills/geno-{name}/     and  ~/.claude/commands/gt-{name}-*.md
  project: ./.claude/skills/geno-{name}/     and  ./.claude/commands/gt-{name}-*.md
"""

from __future__ import annotations

import shutil
from pathlib import Path

from genotools.manifest import Manifest


def install(
    repo_dir: Path,
    manifest: Manifest,
    *,
    copy: bool = False,
    project: bool = False,
) -> list[Path]:
    """Link or copy skill + command files. Returns paths written (for linkdb)."""
    base = Path.cwd() / ".claude" if project else Path.home() / ".claude"
    skills_dir = base / "skills" / manifest.full_name
    commands_dir = base / "commands"

    skills_dir.mkdir(parents=True, exist_ok=True)
    commands_dir.mkdir(parents=True, exist_ok=True)

    # Record the skill dir first so removal (reverse order) rmdirs it LAST,
    # after its contents are already gone.
    written: list[Path] = [skills_dir]

    # Umbrella SKILL.md
    src_skill = repo_dir / "SKILL.md"
    if src_skill.exists():
        dst_skill = skills_dir / "SKILL.md"
        _place(src_skill, dst_skill, copy=copy)
        written.append(dst_skill)

    # Per-command .md files
    cmd_src_dir = repo_dir / manifest.commands_src
    if cmd_src_dir.is_dir():
        for md in sorted(cmd_src_dir.glob("*.md")):
            dst = commands_dir / md.name
            _place(md, dst, copy=copy)
            written.append(dst)

    return written


def _place(src: Path, dst: Path, *, copy: bool) -> None:
    if dst.is_symlink() or dst.exists():
        dst.unlink()
    if copy:
        shutil.copy2(src, dst)
    else:
        dst.symlink_to(src.resolve())
