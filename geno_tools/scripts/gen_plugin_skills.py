#!/usr/bin/env python3
"""Regenerate the `skills` array in every plugin manifest.

Claude Code's plugin loader scans each path in a manifest's `skills` field only
ONE level deep (`<dir>/<name>/SKILL.md`). Our skills use category nesting
(`skills/<category>/<name>/SKILL.md`, arbitrarily deep), so a single
`"skills": "./skills"` would miss everything below the top level.

This walks `skills/`, finds every directory that DIRECTLY contains a
`<name>/SKILL.md`, and writes that list (relative, `./`-prefixed, sorted) into
the `skills` field of each plugin manifest. Run it whenever categories change
(the bootstrap runs it on install). Idempotent.

Usage: python3 geno_tools/scripts/gen_plugin_skills.py [--check]
  --check  exit 1 if any manifest is out of date (for CI), writing nothing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SKILLS = REPO / "skills"

# Manifests whose `skills` field must enumerate the category dirs.
MANIFESTS = [
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    "plugin.json",
]


def skill_parent_dirs() -> list[str]:
    """Dirs that directly contain a `<name>/SKILL.md`, as `./`-relative paths."""
    parents = set()
    for skill_md in SKILLS.rglob("SKILL.md"):
        # skill_md = .../skills/<...>/<name>/SKILL.md; parent.parent is the dir
        # the loader must be pointed at so it finds <name>/ one level down.
        parent = skill_md.parent.parent
        rel = parent.relative_to(REPO)
        parents.add("./" + str(rel))
    return sorted(parents)


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    check = "--check" in argv
    desired = skill_parent_dirs()
    stale = []
    for rel in MANIFESTS:
        path = REPO / rel
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        if data.get("skills") == desired:
            continue
        stale.append(rel)
        if not check:
            data["skills"] = desired
            path.write_text(json.dumps(data, indent=2) + "\n")
    if check:
        if stale:
            print("stale skills array in: " + ", ".join(stale), file=sys.stderr)
            return 1
        print("plugin skills arrays up to date")
        return 0
    if stale:
        print(f"updated skills array ({len(desired)} paths) in: {', '.join(stale)}")
    else:
        print("plugin skills arrays already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
