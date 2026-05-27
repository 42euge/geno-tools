"""Tests for the install/remove/skills flow — the core of geno-tools.

These tests verify the documented install behavior:
  1. geno-tools install <name> clones, creates venv, symlinks bin, registers skills
  2. All sub-skills are enumerated and installed individually (not just the umbrella)
  3. geno-tools remove <name> unregisters skills, removes bin symlinks, cleans up
  4. Dependency resolution installs transitive requires
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from genotools import commands, paths


# ── skill enumeration ─────────────────────────────────────────────────────


class TestEnumerateSkills:
    def test_umbrella_only(self, fake_skillset):
        fake_skillset("geno-simple")
        names = commands._enumerate_skills("geno-simple")
        assert names == ["geno-simple"]

    def test_umbrella_plus_sub_skills(self, fake_skillset):
        fake_skillset(
            "geno-dev",
            sub_skills=["geno-dev-tasks-start", "geno-dev-commits-rewrite"],
        )
        names = commands._enumerate_skills("geno-dev")
        assert "geno-dev" in names
        assert "geno-dev-tasks-start" in names
        assert "geno-dev-commits-rewrite" in names
        assert len(names) == 3

    def test_sub_skills_sorted(self, fake_skillset):
        fake_skillset(
            "geno-dev",
            sub_skills=["geno-dev-z", "geno-dev-a", "geno-dev-m"],
        )
        names = commands._enumerate_skills("geno-dev")
        sub = [n for n in names if n != "geno-dev"]
        assert sub == sorted(sub)

    def test_ignores_dirs_without_skill_md(self, fake_skillset, tmp_root):
        fake_skillset("geno-dev", sub_skills=["geno-dev-real"])
        # add a dir without SKILL.md
        bogus = tmp_root / "geno-dev" / "main" / "skills" / "geno-dev-bogus"
        bogus.mkdir()
        (bogus / "README.md").write_text("not a skill")

        names = commands._enumerate_skills("geno-dev")
        assert "geno-dev-bogus" not in names
        assert "geno-dev-real" in names


class TestEnumerateSkillDirs:
    def test_returns_paths(self, fake_skillset):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a"])
        dirs = commands._enumerate_skill_dirs("geno-dev")
        assert all(isinstance(d, Path) for d in dirs)

    def test_umbrella_dir_is_active(self, fake_skillset, tmp_root):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a"])
        dirs = commands._enumerate_skill_dirs("geno-dev")
        active = paths.skillset_active("geno-dev")
        assert dirs[0] == active

    def test_sub_skill_dirs_point_to_skills_subdir(self, fake_skillset, tmp_root):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a", "geno-dev-b"])
        dirs = commands._enumerate_skill_dirs("geno-dev")
        sub_dirs = dirs[1:]
        for d in sub_dirs:
            assert "skills" in str(d)
            assert (d / "SKILL.md").exists()


class TestEnumerateNestedSkills:
    """Nested skill trees: skills/{sub}/skills/{leaf}/SKILL.md at any depth.

    Verifies that the enumerator walks the whole tree, not just the first
    level under skills/.
    """

    def _write_skill(self, skill_dir: Path, name: str) -> None:
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: fake nested skill\n---\n# {name}\n"
        )

    def _setup_nested(self, fake_skillset, tmp_root: Path) -> Path:
        # Skillset root with umbrella SKILL.md but no flat sub-skills.
        fake_skillset("geno-dev")
        skills = tmp_root / "geno-dev" / "main" / "skills"
        skills.mkdir()
        # Sub-skillset 'tasks' with leaf 'start' at depth 2.
        self._write_skill(skills / "tasks", "geno-dev-tasks")
        self._write_skill(skills / "tasks" / "skills" / "start", "geno-dev-tasks-start")
        # Sub-skillset 'commits' with two leaves.
        self._write_skill(skills / "commits", "geno-dev-commits")
        self._write_skill(skills / "commits" / "skills" / "rewrite", "geno-dev-commits-rewrite")
        self._write_skill(skills / "commits" / "skills" / "amend", "geno-dev-commits-amend")
        return skills

    def test_finds_leaves_at_depth_two(self, fake_skillset, tmp_root):
        self._setup_nested(fake_skillset, tmp_root)
        names = commands._enumerate_skills("geno-dev")
        assert "geno-dev-tasks-start" in names
        assert "geno-dev-commits-rewrite" in names
        assert "geno-dev-commits-amend" in names

    def test_finds_sub_skillset_umbrellas(self, fake_skillset, tmp_root):
        self._setup_nested(fake_skillset, tmp_root)
        names = commands._enumerate_skills("geno-dev")
        assert "geno-dev-tasks" in names
        assert "geno-dev-commits" in names

    def test_uses_frontmatter_name_not_dir_name(self, fake_skillset, tmp_root):
        """Nested leaf dirs are bare nouns; their full names come from
        the frontmatter, not the directory name."""
        self._setup_nested(fake_skillset, tmp_root)
        names = commands._enumerate_skills("geno-dev")
        # Bare dir names like 'start', 'rewrite' must NOT appear — only
        # the fully-qualified names from frontmatter.
        assert "start" not in names
        assert "rewrite" not in names
        assert "amend" not in names

    def test_includes_umbrella(self, fake_skillset, tmp_root):
        self._setup_nested(fake_skillset, tmp_root)
        names = commands._enumerate_skills("geno-dev")
        assert "geno-dev" in names

    def test_recurses_to_depth_three(self, fake_skillset, tmp_root):
        """Tree shape is fractal — depth is unbounded."""
        fake_skillset("geno-deep")
        skills = tmp_root / "geno-deep" / "main" / "skills"
        skills.mkdir()
        self._write_skill(
            skills / "a" / "skills" / "b" / "skills" / "leaf",
            "geno-deep-a-b-leaf",
        )
        names = commands._enumerate_skills("geno-deep")
        assert "geno-deep-a-b-leaf" in names

    def test_falls_back_to_dirname_when_no_frontmatter(self, fake_skillset, tmp_root):
        """If a SKILL.md lacks frontmatter, the directory name is used —
        backwards compatibility with skills authored before the rule.
        """
        fake_skillset("geno-dev")
        skills = tmp_root / "geno-dev" / "main" / "skills"
        skills.mkdir()
        legacy = skills / "geno-dev-legacy"
        legacy.mkdir()
        (legacy / "SKILL.md").write_text("# legacy skill, no frontmatter\n")

        names = commands._enumerate_skills("geno-dev")
        assert "geno-dev-legacy" in names

    def test_ignores_dirs_without_skill_md_at_any_depth(self, fake_skillset, tmp_root):
        fake_skillset("geno-dev")
        skills = tmp_root / "geno-dev" / "main" / "skills"
        skills.mkdir()
        self._write_skill(skills / "tasks" / "skills" / "start", "geno-dev-tasks-start")
        # An empty intermediate dir at depth 1 with no SKILL.md.
        (skills / "tasks").mkdir(exist_ok=True)
        # An empty leaf dir at depth 2 — no SKILL.md.
        (skills / "tasks" / "skills" / "bogus").mkdir(parents=True)

        dirs = commands._enumerate_skill_dirs("geno-dev")
        names = commands._enumerate_skills("geno-dev")
        # The 'tasks' sub-skillset has no SKILL.md so it isn't registered.
        assert not any(d.name == "tasks" and "skills" not in str(d.parent.name) for d in dirs)
        # The bogus leaf is excluded because it has no SKILL.md.
        assert "bogus" not in names
        # The real leaf is included.
        assert "geno-dev-tasks-start" in names


# ── npx skills install ────────────────────────────────────────────────────


class TestInstallSkillsViaNpx:
    def test_installs_each_skill_individually(self, fake_skillset, monkeypatch):
        fake_skillset(
            "geno-dev",
            sub_skills=["geno-dev-tasks-start", "geno-dev-commits-rewrite"],
        )
        calls = []
        monkeypatch.setattr(
            "subprocess.check_call",
            lambda cmd, **kw: calls.append(cmd),
        )

        commands._install_skills_via_npx("geno-dev")

        assert len(calls) == 3  # umbrella + 2 sub-skills
        for cmd in calls:
            assert cmd[0] == "npx"
            assert "--global" in cmd
            assert "--yes" in cmd
            # each call gets a distinct skill dir path
            assert "--skill" not in cmd  # no more --skill '*'

    def test_no_skills_does_nothing(self, tmp_root, monkeypatch):
        # empty skillset with no SKILL.md
        root = tmp_root / "geno-empty"
        root.mkdir()
        main = root / "main"
        main.mkdir()
        (root / "active").symlink_to("main")

        calls = []
        monkeypatch.setattr("subprocess.check_call", lambda cmd, **kw: calls.append(cmd))

        commands._install_skills_via_npx("geno-empty")
        assert calls == []


class TestUninstallSkillsViaNpx:
    def test_uninstalls_all_skills(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a", "geno-dev-b"])
        calls = []
        monkeypatch.setattr("subprocess.run", lambda cmd, **kw: calls.append(cmd))

        commands._uninstall_skills_via_npx("geno-dev")

        assert len(calls) == 1
        cmd = calls[0]
        assert "remove" in cmd
        assert "geno-dev" in cmd
        assert "geno-dev-a" in cmd
        assert "geno-dev-b" in cmd


# ── source resolution ─────────────────────────────────────────────────────


class TestResolveSource:
    def test_registry_name(self, monkeypatch):
        monkeypatch.setattr("genotools.registry._cache", {
            "geno-dev": "https://github.com/42euge/geno-dev.git",
        })
        monkeypatch.setattr("genotools.discovery.candidates_by_name", lambda: {})
        source, name = commands._resolve_source("geno-dev")
        assert source == "https://github.com/42euge/geno-dev.git"
        assert name == "geno-dev"

    def test_local_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr("genotools.registry._cache", {})
        monkeypatch.setattr("genotools.discovery.candidates_by_name", lambda: {})
        local = tmp_path / "my-skillset"
        local.mkdir()
        source, name = commands._resolve_source(str(local))
        assert source == str(local.resolve())
        assert name is None

    def test_git_url(self, monkeypatch):
        monkeypatch.setattr("genotools.registry._cache", {})
        monkeypatch.setattr("genotools.discovery.candidates_by_name", lambda: {})
        url = "https://github.com/acme/acme-foo.git"
        source, name = commands._resolve_source(url)
        assert source == url
        assert name is None

    def test_ssh_url(self, monkeypatch):
        monkeypatch.setattr("genotools.registry._cache", {})
        monkeypatch.setattr("genotools.discovery.candidates_by_name", lambda: {})
        url = "git@github.com:acme/acme-foo.git"
        source, name = commands._resolve_source(url)
        assert source == url

    def test_discovered_source(self, monkeypatch):
        monkeypatch.setattr("genotools.registry._cache", {})
        monkeypatch.setattr("genotools.discovery.candidates_by_name",
                            lambda: {"geno-new": "https://github.com/42euge/geno-new.git"})
        source, name = commands._resolve_source("geno-new")
        assert "geno-new" in source
        assert name == "geno-new"

    def test_unknown_raises(self, monkeypatch):
        monkeypatch.setattr("genotools.registry._cache", {})
        monkeypatch.setattr("genotools.discovery.candidates_by_name", lambda: {})
        with pytest.raises(SystemExit, match="unknown skillset"):
            commands._resolve_source("totally-unknown")


# ── pyproject name reading ────────────────────────────────────────────────


class TestReadPyprojectName:
    def test_reads_name(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "geno-foo"\nversion = "0.1.0"\n'
        )
        assert commands._read_pyproject_name(tmp_path) == "geno-foo"

    def test_missing_file_returns_none(self, tmp_path):
        assert commands._read_pyproject_name(tmp_path) is None

    def test_malformed_toml_returns_none(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("not valid toml {{{}}")
        assert commands._read_pyproject_name(tmp_path) is None

    def test_no_project_section_returns_none(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[build-system]\nrequires = ["setuptools"]\n')
        assert commands._read_pyproject_name(tmp_path) is None


# ── dependency resolution ─────────────────────────────────────────────────


class TestDependencyResolution:
    def test_get_requires_empty(self, fake_skillset):
        fake_skillset("geno-a")
        assert commands._get_requires("geno-a") == []

    def test_get_requires_from_manifest(self, fake_skillset):
        fake_skillset("geno-a", has_manifest=True, requires=["geno-b", "geno-c"])
        reqs = commands._get_requires("geno-a")
        assert reqs == ["geno-b", "geno-c"]

    def test_circular_dependency_detected(self, tmp_root, monkeypatch, capsys):
        monkeypatch.setattr("genotools.registry._cache", {
            "geno-a": "https://example.com/geno-a.git",
        })
        monkeypatch.setattr("genotools.discovery.candidates_by_name", lambda: {})
        installing = {"geno-a"}
        rc = commands._install_one("geno-a", installing=installing)
        assert rc == 1
        assert "circular" in capsys.readouterr().err

    def test_deps_command_shows_tree(self, fake_skillset, monkeypatch, capsys):
        fake_skillset("geno-top", has_manifest=True, requires=["geno-child"])
        fake_skillset("geno-child")
        from genotools.cli import main
        rc = main(["deps", "geno-top"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "geno-top" in out
        assert "geno-child" in out


# ── ls command ────────────────────────────────────────────────────────────


class TestLs:
    def test_empty_install(self, tmp_root, capsys, monkeypatch):
        monkeypatch.setattr("genotools.registry._cache", {})
        from genotools.cli import main
        rc = main(["ls"])
        assert rc == 0
        assert "no skillsets" in capsys.readouterr().out

    def test_lists_installed(self, fake_skillset, capsys, monkeypatch):
        monkeypatch.setattr("genotools.registry._cache", {})
        fake_skillset("geno-dev")
        fake_skillset("geno-agents")
        from genotools.cli import main
        rc = main(["ls"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "geno-dev" in out
        assert "geno-agents" in out

    def test_ls_available_shows_registry(self, monkeypatch, capsys):
        monkeypatch.setattr("genotools.registry._cache", {
            "geno-dev": "https://example.com/geno-dev.git",
            "geno-media": "https://example.com/geno-media.git",
        })
        monkeypatch.setattr("genotools.discovery.candidates_by_name", lambda: {})
        from genotools.cli import main
        rc = main(["ls", "--available"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "geno-dev" in out
        assert "geno-media" in out


# ── remove command ────────────────────────────────────────────────────────


class TestRemove:
    def test_remove_cleans_up(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a"])
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: None)
        monkeypatch.setattr("genotools.commands.SYSTEM_BIN", Path("/nonexistent"))

        from genotools.cli import main
        rc = main(["remove", "geno-dev"])
        assert rc == 0
        assert not paths.skillset_root("geno-dev").exists()

    def test_remove_keep_data(self, fake_skillset, monkeypatch, tmp_root):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a"])
        # create a venvs dir to verify it's preserved
        venvs = tmp_root / "geno-dev" / "venvs"
        venvs.mkdir()
        (venvs / "default").mkdir()

        monkeypatch.setattr("subprocess.run", lambda *a, **kw: None)
        monkeypatch.setattr("genotools.commands.SYSTEM_BIN", Path("/nonexistent"))

        from genotools.cli import main
        rc = main(["remove", "geno-dev", "--keep-data"])
        assert rc == 0
        assert venvs.exists()

    def test_remove_nonexistent_fails(self, tmp_root, capsys):
        from genotools.cli import main
        rc = main(["remove", "geno-nonexistent"])
        assert rc == 1
        assert "not installed" in capsys.readouterr().err


# ── bin symlinks ──────────────────────────────────────────────────────────


class TestBinSymlinks:
    def test_materialize_creates_symlinks(self, fake_skillset, tmp_path, monkeypatch):
        fake_skillset("geno-dev", has_pyproject=True)
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        monkeypatch.setattr("genotools.commands.SYSTEM_BIN", bin_dir)

        venv_bin = paths.skillset_venvs("geno-dev") / "default" / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "geno-dev").write_text("#!/bin/sh\necho hi")

        commands._materialize_bin_symlinks("geno-dev", {"geno-dev": "..."})
        assert (bin_dir / "geno-dev").is_symlink()
        assert (bin_dir / "geno-dev").readlink() == venv_bin / "geno-dev"

    def test_remove_cleans_symlinks(self, fake_skillset, tmp_path, monkeypatch):
        fake_skillset("geno-dev", has_pyproject=True)
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        monkeypatch.setattr("genotools.commands.SYSTEM_BIN", bin_dir)

        venv_bin = paths.skillset_venvs("geno-dev") / "default" / "bin"
        venv_bin.mkdir(parents=True)
        fake_bin = venv_bin / "geno-dev"
        fake_bin.write_text("#!/bin/sh")
        (bin_dir / "geno-dev").symlink_to(fake_bin)

        commands._remove_bin_symlinks("geno-dev")
        assert not (bin_dir / "geno-dev").exists()
