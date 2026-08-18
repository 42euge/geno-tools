"""Tests for skills-manager paths and on-disk layout."""

from pathlib import Path

from geno_tools.skills_manager import paths


class TestNormalize:
    def test_bare_slug_gets_prefix(self):
        assert paths.normalize("dev") == "geno-dev"

    def test_full_name_unchanged(self):
        assert paths.normalize("geno-dev") == "geno-dev"

    def test_non_geno_prefix_gets_prefixed(self):
        assert paths.normalize("acme-foo") == "geno-acme-foo"


class TestSkillsetPaths:
    def test_root(self):
        p = paths.skillset_root("geno-dev")
        assert p == paths.ROOT / "geno-dev"

    def test_git(self):
        p = paths.skillset_git("geno-dev")
        assert p == paths.ROOT / "geno-dev" / ".git"

    def test_worktree_main(self):
        p = paths.skillset_worktree("geno-dev")
        assert p == paths.ROOT / "geno-dev" / "main"

    def test_active(self):
        p = paths.skillset_active("geno-dev")
        assert p == paths.ROOT / "geno-dev" / "active"

    def test_venvs(self):
        p = paths.skillset_venvs("geno-dev")
        assert p == paths.ROOT / "geno-dev" / "venvs"

    def test_normalize_applied_to_root(self):
        assert paths.skillset_root("dev") == paths.skillset_root("geno-dev")
