"""Tests for CLI argument parsing — every documented command is present and parseable."""

import pytest

from genotools.cli import main


EXPECTED_COMMANDS = [
    "ls", "install", "dev", "fork", "use",
    "promote", "update", "remove", "deps", "doctor", "discover",
]


class TestCliHelp:
    def test_help_exits_zero(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0

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


class TestCliParsing:
    def test_ls_no_args(self, tmp_root, no_subprocess, monkeypatch):
        monkeypatch.setattr("genotools.registry._cache", {})
        rc = main(["ls"])
        assert rc == 0

    def test_ls_available(self, monkeypatch, capsys):
        monkeypatch.setattr("genotools.registry._cache", {
            "geno-dev": "https://example.com/geno-dev.git",
        })
        monkeypatch.setattr("genotools.discovery.candidates_by_name", lambda: {})
        rc = main(["ls", "--available"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "geno-dev" in out

    def test_install_requires_name(self):
        with pytest.raises(SystemExit) as exc:
            main(["install"])
        assert exc.value.code != 0

    def test_remove_requires_name(self):
        with pytest.raises(SystemExit) as exc:
            main(["remove"])
        assert exc.value.code != 0

    def test_deps_requires_name(self):
        with pytest.raises(SystemExit) as exc:
            main(["deps"])
        assert exc.value.code != 0
