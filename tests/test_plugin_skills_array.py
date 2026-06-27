"""The plugin manifests' `skills` arrays must enumerate every category dir.

Claude Code's plugin loader scans each `skills` path only one level deep. With
category nesting (`skills/<category>/<name>/SKILL.md`), the manifests must list
every directory that directly contains a `<name>/SKILL.md`, or Claude Code loads
zero nested skills. `gen_plugin_skills.py` regenerates the list; this test fails
if any committed manifest is out of date.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GEN = REPO_ROOT / "geno_tools" / "scripts" / "gen_plugin_skills.py"
MANIFESTS = [
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    "plugin.json",
]


def _load_gen():
    spec = importlib.util.spec_from_file_location("gen_plugin_skills", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generator_check_passes():
    """Committed manifests match what the generator would write (CI gate)."""
    gen = _load_gen()
    assert gen.main(["--check"]) == 0, (
        "Plugin manifest skills array is stale — run "
        "`python3 geno_tools/scripts/gen_plugin_skills.py`."
    )


def test_every_category_dir_listed():
    gen = _load_gen()
    desired = gen.skill_parent_dirs()
    # umbrella + every category that holds leaf skills
    assert "./skills" in desired
    for manifest in MANIFESTS:
        path = REPO_ROOT / manifest
        if not path.exists():
            continue
        skills = json.loads(path.read_text()).get("skills")
        assert skills == desired, f"{manifest} skills array out of date"


def test_listed_dirs_have_skill_children():
    """Every path in the array directly contains at least one <name>/SKILL.md."""
    gen = _load_gen()
    for rel in gen.skill_parent_dirs():
        d = REPO_ROOT / rel.lstrip("./")
        children = [c for c in d.iterdir() if (c / "SKILL.md").exists()]
        assert children, f"{rel} lists no <name>/SKILL.md children"
