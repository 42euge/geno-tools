"""Tests for CLI argument parsing — every documented command is present and parseable."""

import pytest

from geno_tools.cli import main


EXPECTED_COMMANDS = [
    "install",
    "uninstall",
    "update",
    "status",
    "discover",
    "scan",
    "audit",
    "system",
    "config",
]
EXPECTED_SYSTEM_COMMANDS = ["update", "uninstall"]


class TestCliHelp:
    def test_no_arguments_prints_useful_help(self, capsys):
        assert main([]) == 0

        captured = capsys.readouterr()
        assert captured.err == ""
        assert "Manage skillsets" in captured.out
        assert "Install, uninstall, and update agent skills" in captured.out
        assert "install REF" in captured.out
        assert "uninstall NAME" in captured.out
        assert "update [NAME]" in captured.out
        assert captured.out.index("install REF") < captured.out.index("uninstall NAME")
        assert captured.out.index("uninstall NAME") < captured.out.index("update [NAME]")
        assert "Find and inspect skillsets" in captured.out
        assert "Other commands" in captured.out

    def test_help_exits_zero(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0

    def test_system_without_command_prints_safety_help(self, capsys):
        assert main(["system"]) == 0

        captured = capsys.readouterr()
        assert captured.err == ""
        assert "affect every installed skillset" in captured.out
        assert "geno-tools system uninstall --dry-run" in captured.out
        assert "User data under ~/.geno is always preserved" in captured.out

    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        assert "geno-tools" in capsys.readouterr().out

    @pytest.mark.parametrize("cmd", EXPECTED_COMMANDS)
    def test_command_exists_in_help(self, cmd, capsys):
        with pytest.raises(SystemExit):
            main(["--help"])
        assert cmd in capsys.readouterr().out

    @pytest.mark.parametrize("cmd", EXPECTED_COMMANDS)
    def test_subcommand_help(self, cmd, capsys):
        with pytest.raises(SystemExit) as exc:
            main([cmd, "--help"])
        assert exc.value.code == 0

    @pytest.mark.parametrize("cmd", EXPECTED_SYSTEM_COMMANDS)
    def test_system_subcommand_help(self, cmd, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["system", cmd, "--help"])
        assert exc.value.code == 0

    def test_old_skills_uninstall_points_to_system_command(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["skills", "uninstall"])

        assert exc.value.code == 2
        assert "moved to 'geno-tools system uninstall'" in capsys.readouterr().err

    def test_old_skills_command_points_to_top_level(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["skills", "install"])

        assert exc.value.code == 2
        assert "moved to 'geno-tools install'" in capsys.readouterr().err

    def test_old_upgrade_points_to_update(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["upgrade"])

        assert exc.value.code == 2
        assert "moved to 'geno-tools update'" in capsys.readouterr().err


class TestCliParsing:
    def test_status_no_args(self, tmp_root, no_subprocess, monkeypatch):
        monkeypatch.setattr("geno_tools.skills_manager.registry._cache", {})
        rc = main(["status"])
        assert rc == 0

    def test_discover(self, monkeypatch, capsys):
        # `discover` reads registry.read_full() directly (not the _cache view),
        # so patch that — patching _cache alone let the REAL ~/.geno/registry.json
        # leak in, making this pass/fail on machine state.
        monkeypatch.setattr("geno_tools.skills_manager.registry.read_full", lambda: {
            "geno-dev": {"url": "https://example.com/geno-dev.git",
                         "category": "Developer Tools"},
        })
        monkeypatch.setattr("geno_tools.skills_manager.registry.is_stale", lambda *a, **k: False)
        monkeypatch.setattr("geno_tools.skills_manager.discovery.candidates_by_name", lambda: {})
        rc = main(["discover"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "geno-dev" in out

    def test_install_requires_name(self):
        with pytest.raises(SystemExit) as exc:
            main(["install"])
        assert exc.value.code != 0

    def test_uninstall_requires_name(self):
        with pytest.raises(SystemExit) as exc:
            main(["uninstall"])
        assert exc.value.code != 0

    def test_old_remove_points_to_uninstall(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["remove"])

        assert exc.value.code == 2
        assert "moved to 'geno-tools uninstall'" in capsys.readouterr().err

    def test_deps_is_not_a_registered_command(self):
        with pytest.raises(SystemExit) as exc:
            main(["deps"])
        assert exc.value.code == 2
