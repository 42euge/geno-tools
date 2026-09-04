"""Tests for upgrading managed skillsets."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from geno_tools.skills_manager import paths
from geno_tools.skills_manager.commands import upgrade as commands


# ── _update_one ──────────────────────────────────────────────────────────


class TestUpgradeOne:
    def test_up_to_date(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev")
        rev = "abc12345"

        def fake_check_output(cmd, **kw):
            if "status" in cmd and "--porcelain" in cmd:
                return ""
            if "branch" in cmd and "--show-current" in cmd:
                return "main"
            if "rev-parse" in cmd:
                return rev
            if "diff" in cmd and "--name-only" in cmd:
                return ""
            return ""

        monkeypatch.setattr("subprocess.check_output", fake_check_output)
        monkeypatch.setattr("subprocess.check_call", lambda cmd, **kw: None)

        result = commands._update_one("geno-dev")
        assert result.status == "up-to-date"
        assert result.old_rev == rev[:8]

    def test_updated_with_skill_re_registration(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev", sub_skills=["geno-dev-a"])
        call_count = {"rev": 0}
        npx_calls = []

        def fake_check_output(cmd, **kw):
            if "status" in cmd and "--porcelain" in cmd:
                return ""
            if "branch" in cmd and "--show-current" in cmd:
                return "main"
            if "rev-parse" in cmd:
                call_count["rev"] += 1
                return "old12345678" if call_count["rev"] == 1 else "new56789abc"
            if "symbolic-ref" in cmd:
                return "main"
            if "diff" in cmd and "--name-only" in cmd:
                return "README.md"
            return ""

        def fake_check_call(cmd, **kw):
            if cmd[0] == "npx":
                npx_calls.append(cmd)

        monkeypatch.setattr("subprocess.check_output", fake_check_output)
        monkeypatch.setattr("subprocess.check_call", fake_check_call)

        result = commands._update_one("geno-dev")
        assert result.status == "updated"
        assert result.old_rev == "old12345"
        assert result.new_rev == "new56789"
        assert len(npx_calls) == 1  # 1 sub-skill (umbrella root skipped)

    def test_updated_prunes_skills_removed_by_pull(self, fake_skillset, monkeypatch):
        root = fake_skillset(
            "geno-dev", sub_skills=["geno-dev-keep", "geno-dev-retired"]
        )
        call_count = {"rev": 0}
        remove_calls = []

        def fake_check_output(cmd, **kw):
            if "status" in cmd and "--porcelain" in cmd:
                return ""
            if "branch" in cmd and "--show-current" in cmd:
                return "main"
            if "rev-parse" in cmd:
                call_count["rev"] += 1
                return "old12345678" if call_count["rev"] == 1 else "new56789abc"
            if "symbolic-ref" in cmd:
                return "main"
            if "diff" in cmd and "--name-only" in cmd:
                return "skills/geno-dev-retired/SKILL.md"
            return ""

        def fake_check_call(cmd, **kw):
            if "pull" in cmd:
                shutil.rmtree(root / "main" / "skills" / "geno-dev-retired")

        monkeypatch.setattr("subprocess.check_output", fake_check_output)
        monkeypatch.setattr("subprocess.check_call", fake_check_call)
        monkeypatch.setattr(
            "subprocess.run", lambda cmd, **kw: remove_calls.append(cmd)
        )

        result = commands._update_one("geno-dev")

        assert result.status == "updated"
        assert len(remove_calls) == 1
        assert "geno-dev-retired" in remove_calls[0]
        assert "geno-dev-keep" not in remove_calls[0]

    def test_dirty_worktree_skipped(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev")

        def fake_check_output(cmd, **kw):
            if "status" in cmd and "--porcelain" in cmd:
                return "M README.md\n"
            return ""

        monkeypatch.setattr("subprocess.check_output", fake_check_output)

        result = commands._update_one("geno-dev")
        assert result.status == "skipped"
        assert "dirty" in result.detail

    def test_wrong_branch_skipped(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev")

        def fake_check_output(cmd, **kw):
            if "status" in cmd and "--porcelain" in cmd:
                return ""
            if "branch" in cmd and "--show-current" in cmd:
                return "feature-branch"
            if "symbolic-ref" in cmd:
                return "main"
            return ""

        monkeypatch.setattr("subprocess.check_output", fake_check_output)

        result = commands._update_one("geno-dev")
        assert result.status == "skipped"
        assert "feature-branch" in result.detail

    def test_missing_worktree_error(self, tmp_root):
        root = tmp_root / "geno-dev"
        root.mkdir()
        (root / ".git").mkdir()
        (root / "active").symlink_to("main")

        result = commands._update_one("geno-dev")
        assert result.status == "error"
        assert "missing" in result.detail

    def test_fetch_failure(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev")

        def fake_check_output(cmd, **kw):
            if "status" in cmd and "--porcelain" in cmd:
                return ""
            if "branch" in cmd and "--show-current" in cmd:
                return "main"
            if "rev-parse" in cmd:
                return "abc12345"
            if "symbolic-ref" in cmd:
                return "main"
            return ""

        def fake_check_call(cmd, **kw):
            if "fetch" in cmd:
                raise subprocess.CalledProcessError(1, cmd)

        monkeypatch.setattr("subprocess.check_output", fake_check_output)
        monkeypatch.setattr("subprocess.check_call", fake_check_call)

        result = commands._update_one("geno-dev")
        assert result.status == "error"
        assert "fetch" in result.detail

    def test_pull_ff_only_failure(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev")

        def fake_check_output(cmd, **kw):
            if "status" in cmd and "--porcelain" in cmd:
                return ""
            if "branch" in cmd and "--show-current" in cmd:
                return "main"
            if "rev-parse" in cmd:
                return "abc12345"
            if "symbolic-ref" in cmd:
                return "main"
            return ""

        def fake_check_call(cmd, **kw):
            if "pull" in cmd:
                raise subprocess.CalledProcessError(1, cmd)

        monkeypatch.setattr("subprocess.check_output", fake_check_output)
        monkeypatch.setattr("subprocess.check_call", fake_check_call)

        result = commands._update_one("geno-dev")
        assert result.status == "error"
        assert "diverged" in result.detail


# ── _maybe_reinstall_venv ────────────────────────────────────────────────


class TestMaybeReinstallVenv:
    def test_reinstalls_when_pyproject_changed(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev", has_pyproject=True)
        venv_dir = paths.skillset_venvs("geno-dev") / "default"
        venv_dir.mkdir(parents=True)
        pip = venv_dir / "bin" / "pip"
        pip.parent.mkdir(parents=True)
        pip.write_text("#!/bin/sh\n")

        pip_calls = []

        def fake_check_output(cmd, **kw):
            if "diff" in cmd and "--name-only" in cmd:
                return "pyproject.toml\nREADME.md\n"
            return ""

        def fake_check_call(cmd, **kw):
            if "pip" in str(cmd[0]):
                pip_calls.append(cmd)

        monkeypatch.setattr("subprocess.check_output", fake_check_output)
        monkeypatch.setattr("subprocess.check_call", fake_check_call)

        commands._maybe_reinstall_venv("geno-dev", "old123", "new456")
        assert len(pip_calls) == 1
        assert "-e" in pip_calls[0]

    def test_skips_when_pyproject_unchanged(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev", has_pyproject=True)
        pip_calls = []

        def fake_check_output(cmd, **kw):
            if "diff" in cmd and "--name-only" in cmd:
                return "README.md\nsrc/main.py\n"
            return ""

        monkeypatch.setattr("subprocess.check_output", fake_check_output)
        monkeypatch.setattr("subprocess.check_call",
                            lambda cmd, **kw: pip_calls.append(cmd))

        commands._maybe_reinstall_venv("geno-dev", "old123", "new456")
        assert len(pip_calls) == 0

    def test_skips_when_no_pyproject(self, fake_skillset, monkeypatch):
        fake_skillset("geno-dev")  # no has_pyproject
        pip_calls = []
        monkeypatch.setattr("subprocess.check_call",
                            lambda cmd, **kw: pip_calls.append(cmd))

        commands._maybe_reinstall_venv("geno-dev", "old123", "new456")
        assert len(pip_calls) == 0


# ── upgrade command ─────────────────────────────────────────────────────


class TestUpgradeAll:
    def test_updates_all_installed(self, fake_skillset, monkeypatch, capsys):
        fake_skillset("geno-agents")
        fake_skillset("geno-dev")
        fake_skillset("geno-media")

        def fake_check_output(cmd, **kw):
            if "status" in cmd and "--porcelain" in cmd:
                return ""
            if "branch" in cmd and "--show-current" in cmd:
                return "main"
            if "rev-parse" in cmd:
                return "same1234"
            if "symbolic-ref" in cmd:
                return "main"
            return ""

        monkeypatch.setattr("subprocess.check_output", fake_check_output)
        monkeypatch.setattr("subprocess.check_call", lambda cmd, **kw: None)

        from geno_tools.cli import main
        rc = main(["update"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "geno-agents" in out
        assert "geno-dev" in out
        assert "geno-media" in out

    def test_excludes_bootstrap(self, tmp_root, monkeypatch, capsys):
        (tmp_root / "geno-bootstrap").mkdir()
        from geno_tools.cli import main
        rc = main(["update"])
        assert rc == 0
        assert "no skillsets" in capsys.readouterr().out

    def test_empty_install(self, tmp_root, capsys):
        from geno_tools.cli import main
        rc = main(["update"])
        assert rc == 0
        assert "no skillsets" in capsys.readouterr().out


class TestUpgradeCli:
    def test_single_by_name(self, fake_skillset, monkeypatch, capsys):
        fake_skillset("geno-dev")

        def fake_check_output(cmd, **kw):
            if "status" in cmd and "--porcelain" in cmd:
                return ""
            if "branch" in cmd and "--show-current" in cmd:
                return "main"
            if "rev-parse" in cmd:
                return "same1234"
            if "symbolic-ref" in cmd:
                return "main"
            return ""

        monkeypatch.setattr("subprocess.check_output", fake_check_output)
        monkeypatch.setattr("subprocess.check_call", lambda cmd, **kw: None)

        from geno_tools.cli import main
        rc = main(["update", "geno-dev"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "geno-dev" in out

    def test_nonexistent_fails(self, tmp_root, capsys):
        from geno_tools.cli import main
        rc = main(["update", "geno-nonexistent"])
        assert rc == 1
        assert "not installed" in capsys.readouterr().err

    def test_bare_slug_accepted(self, fake_skillset, monkeypatch, capsys):
        fake_skillset("geno-dev")

        def fake_check_output(cmd, **kw):
            if "status" in cmd and "--porcelain" in cmd:
                return ""
            if "branch" in cmd and "--show-current" in cmd:
                return "main"
            if "rev-parse" in cmd:
                return "same1234"
            if "symbolic-ref" in cmd:
                return "main"
            return ""

        monkeypatch.setattr("subprocess.check_output", fake_check_output)
        monkeypatch.setattr("subprocess.check_call", lambda cmd, **kw: None)

        from geno_tools.cli import main
        rc = main(["update", "dev"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "geno-dev" in out

    def test_local_origin_reports_canonical_reinstall_path(
        self, fake_skillset, tmp_path, monkeypatch, capsys
    ):
        fake_skillset("geno-dev")
        local_source = tmp_path / "retired-worktree" / "geno-dev"
        local_source.mkdir(parents=True)

        def fake_check_output(cmd, **kw):
            if "status" in cmd and "--porcelain" in cmd:
                return ""
            if "branch" in cmd and "--show-current" in cmd:
                return "main"
            if "rev-parse" in cmd:
                return "same1234"
            if "symbolic-ref" in cmd:
                return "main"
            if "get-url" in cmd:
                return str(local_source)
            return ""

        monkeypatch.setattr("subprocess.check_output", fake_check_output)
        monkeypatch.setattr("subprocess.check_call", lambda cmd, **kw: None)
        monkeypatch.setattr(
            "geno_tools.skills_manager.registry._cache",
            {"geno-dev": "https://github.com/42euge/geno-dev.git"},
        )

        from geno_tools.cli import main

        assert main(["update", "geno-dev"]) == 0
        out = capsys.readouterr().out
        assert "local source (1)" in out
        assert str(local_source) in out
        assert "already up-to-date" not in out
        assert "geno-tools uninstall geno-dev" in out
        assert (
            "geno-tools install https://github.com/42euge/geno-dev.git" in out
        )


# ── summary output ───────────────────────────────────────────────────────


class TestPrintUpdateSummary:
    def test_shows_all_categories(self, capsys):
        results = [
            commands._UpdateResult("geno-a", "updated", old_rev="aaa", new_rev="bbb"),
            commands._UpdateResult("geno-b", "up-to-date"),
            commands._UpdateResult("geno-c", "skipped", detail="dirty worktree"),
            commands._UpdateResult("geno-d", "error", detail="git fetch failed"),
        ]
        commands._print_update_summary(results)
        out = capsys.readouterr().out
        assert "updated (1)" in out
        assert "up-to-date (1)" in out
        assert "skipped (1)" in out
        assert "errors (1)" in out
        assert "geno-a" in out
        assert "aaa -> bbb" in out
        assert "dirty worktree" in out
        assert "git fetch failed" in out

    def test_omits_empty_categories(self, capsys):
        results = [
            commands._UpdateResult("geno-a", "up-to-date"),
        ]
        commands._print_update_summary(results)
        out = capsys.readouterr().out
        assert "updated" not in out
        assert "skipped" not in out
        assert "errors" not in out
        assert "up-to-date (1)" in out
