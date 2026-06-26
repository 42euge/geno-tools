"""Tests for arbitrary-depth nested skill discovery.

The nesting standard is `skills/<category>/<name>/SKILL.md`, arbitrarily deep
(e.g. `skills/meta/harness/fork/SKILL.md`). Category dirs hold no SKILL.md;
a SKILL.md at a shallow level shadows anything nested below it (the
category-XOR-leaf invariant). geno-tools must register every leaf by its
fully-qualified frontmatter `name:`, not the (colliding) leaf dir name.

See `_walk_skill_dirs` / `_skill_name` / `_enumerate_skill_dirs` in
geno_tools/commands.py.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from geno_tools import commands, paths


def _skillset(tmp_root: Path, name: str, skills: dict[str, str]) -> Path:
    """Create a skillset whose `skills/` tree is described by {relpath: name}.

    relpath is the dir under `skills/` (may be nested, e.g. "meta/harness/fork");
    name is the frontmatter `name:`. A leaf gets a SKILL.md; intermediate dirs
    are created implicitly as bare category dirs (no SKILL.md).
    """
    root = tmp_root / name
    main = root / "main"
    main.mkdir(parents=True)
    (main / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: umbrella\n---\n# {name}\n"
    )
    skills_dir = main / "skills"
    skills_dir.mkdir()
    for relpath, skill_name in skills.items():
        d = skills_dir / relpath
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(
            f"---\nname: {skill_name}\ndescription: {skill_name}\n---\n# {skill_name}\n"
        )
    (root / "active").symlink_to("main")
    (root / ".git").mkdir()
    return root


class TestNestedDiscovery:
    def test_category_nesting_one_level(self, tmp_root):
        _skillset(tmp_root, "geno-x", {
            "manager/install": "geno-x-manager-install",
            "manager/remove": "geno-x-manager-remove",
            "audit/run": "geno-x-audit-run",
        })
        names = set(commands._enumerate_skills("geno-x"))
        # umbrella + 3 leaves
        assert names == {
            "geno-x",
            "geno-x-manager-install",
            "geno-x-manager-remove",
            "geno-x-audit-run",
        }

    def test_arbitrary_depth(self, tmp_root):
        # 4 levels under skills/: meta/harness/fork
        _skillset(tmp_root, "geno-y", {
            "meta/harness/fork": "geno-y-meta-harness-fork",
            "meta/harness/use": "geno-y-meta-harness-use",
            "meta/ecosystem/onboarding": "geno-y-meta-ecosystem-onboarding",
            "author/skill": "geno-y-author-skill",
        })
        names = set(commands._enumerate_skills("geno-y"))
        assert "geno-y-meta-harness-fork" in names
        assert "geno-y-meta-ecosystem-onboarding" in names
        assert len(names) == 5  # umbrella + 4 leaves

    def test_names_from_frontmatter_not_dir(self, tmp_root):
        # two leaf dirs both named "install" under different categories —
        # dir name collides, frontmatter name does not.
        _skillset(tmp_root, "geno-z", {
            "manager/install": "geno-z-manager-install",
            "author/install": "geno-z-author-install",
        })
        names = set(commands._enumerate_skills("geno-z"))
        assert names == {"geno-z", "geno-z-author-install", "geno-z-manager-install"}

    def test_shadowing_parent_wins(self, tmp_root):
        # a leaf with a nested SKILL.md beneath it: parent shadows child.
        _skillset(tmp_root, "geno-w", {
            "x": "geno-w-x",
            "x/inner": "geno-w-x-inner",  # shadowed by x/
        })
        names = set(commands._enumerate_skills("geno-w"))
        assert names == {"geno-w", "geno-w-x"}
        assert "geno-w-x-inner" not in names

    def test_category_dirs_not_registered(self, tmp_root):
        # bare category dirs (no SKILL.md) must not register.
        ss = _skillset(tmp_root, "geno-c", {"cat/leaf": "geno-c-cat-leaf"})
        # `cat/` itself has no SKILL.md
        assert not (ss / "main" / "skills" / "cat" / "SKILL.md").exists()
        dirs = commands._enumerate_skill_dirs("geno-c")
        rels = [str(d).split("/skills/", 1)[-1] for d in dirs]
        assert rels == ["cat/leaf"]

    def test_install_registers_every_leaf_with_full_depth(self, tmp_root, monkeypatch):
        _skillset(tmp_root, "geno-i", {
            "manager/install": "geno-i-manager-install",
            "meta/harness/fork": "geno-i-meta-harness-fork",
        })
        calls = []
        monkeypatch.setattr("subprocess.check_call", lambda cmd, **kw: calls.append(cmd))
        commands._install_skills_via_npx("geno-i")
        assert len(calls) == 2
        for cmd in calls:
            assert cmd[0] == "npx"
            assert "--full-depth" in cmd
            assert "--global" in cmd
