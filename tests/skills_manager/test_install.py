"""Tests for the skills-manager install/remove flow.

These tests verify the documented install behavior:
  1. geno-tools install <name> clones, creates venv, symlinks bin, registers skills
  2. All sub-skills are enumerated and installed individually (not just the umbrella)
  3. geno-tools uninstall <name> unregisters skills, removes bin symlinks, cleans up
  4. Dependency resolution installs transitive requires
"""

from __future__ import annotations

from pathlib import Path

import pytest

from geno_tools.skills_manager import paths
from geno_tools.skills_manager.commands import install as commands


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

    def test_umbrella_dir_skipped_when_subs_exist(self, fake_skillset, tmp_root):
        # When sub-skills exist, only the leaf dirs are returned — the umbrella
        # root is skipped so npx registers leaves, not the whole tree.
        fake_skillset("geno-dev", sub_skills=["geno-dev-a"])
        dirs = commands._enumerate_skill_dirs("geno-dev")
        active = paths.skillset_active("geno-dev")
        assert active not in dirs
        assert all("skills" in str(d) for d in dirs)

    def test_sub_skill_dirs_point_to_skills_subdir(self, fake_skillset, tmp_root):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a", "geno-dev-b"])
        dirs = commands._enumerate_skill_dirs("geno-dev")
        for d in dirs:
            assert "skills" in str(d)
            assert (d / "SKILL.md").exists()


# ── npx skills install ────────────────────────────────────────────────────


class TestInstallSkillsViaNpx:
    def test_registers_whole_tree_in_one_call(self, fake_skillset, monkeypatch):
        # Even with multiple sub-skills, npx skills is invoked ONCE over the
        # skills/ root — --full-depth discovers the leaves. This is the fix for
        # the per-leaf loop that printed a banner + repeated failures N times.
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

        assert len(calls) == 1  # ONE call, not one-per-leaf
        cmd = calls[0]
        assert cmd[0] == "npx"
        assert "add" in cmd
        assert "--global" in cmd
        assert "--full-depth" in cmd
        assert "--yes" in cmd
        # points at the skills/ tree root, not an individual leaf dir
        target = cmd[cmd.index("add") + 1]
        assert target.endswith("/skills")

    def test_agent_scoping_passed_through(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a"])
        calls = []
        monkeypatch.setattr("subprocess.check_call", lambda cmd, **kw: calls.append(cmd))
        commands._install_skills_via_npx("geno-dev", agent="claude-code")
        assert calls[0][calls[0].index("--agent") + 1] == "claude-code"

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
        monkeypatch.setattr("geno_tools.skills_manager.registry._cache", {
            "geno-dev": "https://github.com/42euge/geno-dev.git",
        })
        monkeypatch.setattr("geno_tools.skills_manager.discovery.candidates_by_name", lambda: {})
        source, name = commands._resolve_source("geno-dev")
        assert source == "https://github.com/42euge/geno-dev.git"
        assert name == "geno-dev"

    def test_local_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr("geno_tools.skills_manager.registry._cache", {})
        monkeypatch.setattr("geno_tools.skills_manager.discovery.candidates_by_name", lambda: {})
        local = tmp_path / "my-skillset"
        local.mkdir()
        source, name = commands._resolve_source(str(local))
        assert source == str(local.resolve())
        assert name is None

    def test_git_url(self, monkeypatch):
        monkeypatch.setattr("geno_tools.skills_manager.registry._cache", {})
        monkeypatch.setattr("geno_tools.skills_manager.discovery.candidates_by_name", lambda: {})
        url = "https://github.com/acme/acme-foo.git"
        source, name = commands._resolve_source(url)
        assert source == url
        assert name is None

    def test_ssh_url(self, monkeypatch):
        monkeypatch.setattr("geno_tools.skills_manager.registry._cache", {})
        monkeypatch.setattr("geno_tools.skills_manager.discovery.candidates_by_name", lambda: {})
        url = "git@github.com:acme/acme-foo.git"
        source, name = commands._resolve_source(url)
        assert source == url

    def test_unknown_name_points_at_discover_skill(self, monkeypatch):
        # Not in the cache, not a path, not a URL → error names the discover skill.
        monkeypatch.setattr("geno_tools.skills_manager.registry._cache", {})
        with pytest.raises(SystemExit, match="discover"):
            commands._resolve_source("geno-nonexistent")

    def test_resolve_from_discovery_cache(self, monkeypatch):
        # A name written to the registry cache resolves to its URL.
        monkeypatch.setattr("geno_tools.skills_manager.registry._cache", {
            "geno-loops": "https://github.com/42euge/geno-loops.git",
        })
        source, name = commands._resolve_source("geno-loops")
        assert source == "https://github.com/42euge/geno-loops.git"
        assert name == "geno-loops"

    def test_unknown_raises(self, monkeypatch):
        monkeypatch.setattr("geno_tools.skills_manager.registry._cache", {})
        monkeypatch.setattr("geno_tools.skills_manager.discovery.candidates_by_name", lambda: {})
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
        monkeypatch.setattr("geno_tools.skills_manager.registry._cache", {
            "geno-a": "https://example.com/geno-a.git",
        })
        monkeypatch.setattr("geno_tools.skills_manager.discovery.candidates_by_name", lambda: {})
        installing = {"geno-a"}
        rc = commands._install_one("geno-a", installing=installing)
        assert rc == 1
        assert "circular" in capsys.readouterr().err

    def test_dependency_tree_implementation_is_retained(self, fake_skillset, capsys):
        fake_skillset("geno-top", has_manifest=True, requires=["geno-child"])
        fake_skillset("geno-child")
        from geno_tools.skills_manager.commands import deps

        deps._print_dep_tree("geno-top", indent=0, seen=set())
        out = capsys.readouterr().out
        assert "geno-top" in out
        assert "geno-child" in out


class TestStatusAndDiscover:
    def test_status_shows_version(self, fake_skillset, capsys, monkeypatch):
        root = fake_skillset("geno-dev")
        (root / "main" / "genotools.yaml").write_text('version: "0.4.2"\n')
        from geno_tools.cli import main
        assert main(["status"]) == 0
        out = capsys.readouterr().out
        assert "geno-dev" in out
        assert "0.4.2" in out

    def test_status_empty(self, tmp_root, capsys):
        from geno_tools.cli import main
        assert main(["status"]) == 0
        assert "no skillsets installed" in capsys.readouterr().out

    def test_discover_groups_by_category(self, fake_skillset, capsys, monkeypatch):
        # fresh cache → no network; read_full provides categorized entries.
        monkeypatch.setattr("geno_tools.skills_manager.registry.is_stale", lambda *a, **k: False)
        monkeypatch.setattr("geno_tools.skills_manager.registry.read_full", lambda: {
            "geno-dev": {"url": "https://example.com/geno-dev.git",
                         "category": "Developer Tools"},
            "geno-media": {"url": "https://example.com/geno-media.git",
                           "category": "Modalities & Capabilities"},
        })
        fake_skillset("geno-dev")  # installed
        from geno_tools.cli import main
        assert main(["discover"]) == 0
        out = capsys.readouterr().out
        assert "Developer Tools" in out and "Modalities & Capabilities" in out
        assert "geno-dev" in out and "geno-media" in out
        assert "installed" in out  # geno-dev marked

    def test_discover_refreshes_when_stale(self, capsys, monkeypatch):
        # stale cache → discover triggers a (mocked) network refresh.
        called = {"n": 0}
        monkeypatch.setattr("geno_tools.skills_manager.registry.is_stale", lambda *a, **k: True)
        monkeypatch.setattr("geno_tools.skills_manager.registry.cache_age_seconds", lambda: None)
        monkeypatch.setattr("geno_tools.skills_manager.registry.discover_now",
                            lambda *a, **k: called.__setitem__("n", called["n"] + 1) or {})
        monkeypatch.setattr("geno_tools.skills_manager.registry.read_full", lambda: {})
        from geno_tools.cli import main
        assert main(["discover"]) == 0
        assert called["n"] == 1
        assert "discover" in capsys.readouterr().out

    def test_output_is_plain_when_not_tty(self, fake_skillset, capsys):
        # capsys captured stdout is not a TTY → no ANSI escapes, ASCII rule.
        fake_skillset("geno-dev")
        from geno_tools.cli import main
        main(["status"])
        out = capsys.readouterr().out
        assert "\x1b[" not in out      # no ANSI color codes
        assert "─" not in out          # ASCII dashes, not box-drawing


# ── remove command ────────────────────────────────────────────────────────


class TestRemove:
    def test_remove_cleans_up(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a"])
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: None)
        monkeypatch.setattr("geno_tools.skills_manager.commands.install.SYSTEM_BIN", Path("/nonexistent"))

        from geno_tools.cli import main
        rc = main(["uninstall", "geno-dev"])
        assert rc == 0
        assert not paths.skillset_root("geno-dev").exists()

    def test_remove_keep_data(self, fake_skillset, monkeypatch, tmp_root):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a"])
        # create a venvs dir to verify it's preserved
        venvs = tmp_root / "geno-dev" / "venvs"
        venvs.mkdir()
        (venvs / "default").mkdir()

        monkeypatch.setattr("subprocess.run", lambda *a, **kw: None)
        monkeypatch.setattr("geno_tools.skills_manager.commands.install.SYSTEM_BIN", Path("/nonexistent"))

        from geno_tools.cli import main
        rc = main(["uninstall", "geno-dev", "--keep-data"])
        assert rc == 0
        assert venvs.exists()

    def test_remove_nonexistent_fails(self, tmp_root, capsys):
        from geno_tools.cli import main
        rc = main(["uninstall", "geno-nonexistent"])
        assert rc == 1
        assert "not installed" in capsys.readouterr().err


# ── bin symlinks ──────────────────────────────────────────────────────────


class TestBinSymlinks:
    def test_materialize_creates_symlinks(self, fake_skillset, tmp_path, monkeypatch):
        fake_skillset("geno-dev", has_pyproject=True)
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        monkeypatch.setattr("geno_tools.skills_manager.commands.install.SYSTEM_BIN", bin_dir)

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
        monkeypatch.setattr("geno_tools.skills_manager.commands.install.SYSTEM_BIN", bin_dir)

        venv_bin = paths.skillset_venvs("geno-dev") / "default" / "bin"
        venv_bin.mkdir(parents=True)
        fake_bin = venv_bin / "geno-dev"
        fake_bin.write_text("#!/bin/sh")
        (bin_dir / "geno-dev").symlink_to(fake_bin)

        commands._remove_bin_symlinks("geno-dev")
        assert not (bin_dir / "geno-dev").exists()


class TestAgentScoping:
    """npx --agent is scoped to detected agents, not '*' (avoids ~76-agent spam)."""

    def test_scopes_to_detected_agents(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a"])
        monkeypatch.setattr(
            "geno_tools.skills_manager.agents.detect_installed",
            lambda: ["claude-code", "codex"],
        )
        calls = []
        monkeypatch.setattr("subprocess.check_call", lambda cmd, **kw: calls.append(cmd))
        commands._install_skills_via_npx("geno-dev")
        cmd = calls[0]
        i = cmd.index("--agent")
        assert cmd[i + 1:i + 3] == ["claude-code", "codex"]
        assert "*" not in cmd

    def test_falls_back_to_star_when_nothing_detected(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a"])
        monkeypatch.setattr("geno_tools.skills_manager.agents.detect_installed", lambda: [])
        calls = []
        monkeypatch.setattr("subprocess.check_call", lambda cmd, **kw: calls.append(cmd))
        commands._install_skills_via_npx("geno-dev")
        cmd = calls[0]
        assert cmd[cmd.index("--agent") + 1] == "*"

    def test_explicit_agent_bypasses_detection(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a"])
        def _boom():
            raise AssertionError("detection must not run for an explicit agent")
        monkeypatch.setattr("geno_tools.skills_manager.agents.detect_installed", _boom)
        calls = []
        monkeypatch.setattr("subprocess.check_call", lambda cmd, **kw: calls.append(cmd))
        commands._install_skills_via_npx("geno-dev", agent="cursor")
        cmd = calls[0]
        assert cmd[cmd.index("--agent") + 1] == "cursor"


class TestDetectInstalledAgents:
    def test_detects_by_agent_home(self, tmp_path, monkeypatch):
        from geno_tools.skills_manager import agents
        monkeypatch.setattr(agents, "_AGENT_HOMES", {
            "claude-code": str(tmp_path / ".claude"),
            "cursor": str(tmp_path / ".cursor"),
        })
        (tmp_path / ".claude").mkdir()
        assert agents.detect_installed() == ["claude-code"]

    def test_none_installed(self, tmp_path, monkeypatch):
        from geno_tools.skills_manager import agents
        monkeypatch.setattr(agents, "_AGENT_HOMES", {"x": str(tmp_path / "nope")})
        assert agents.detect_installed() == []
