"""Tests for CLI argument parsing — every documented command is present and parseable."""

import pytest

from geno_tools.cli import main


EXPECTED_COMMANDS = [
    "status", "ls", "install", "dev", "fork", "use",
    "promote", "update", "upgrade", "remove", "deps", "doctor", "discover",
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
        monkeypatch.setattr("geno_tools.registry._cache", {})
        rc = main(["ls"])
        assert rc == 0

    def test_ls_available(self, monkeypatch, capsys):
        # `discover` reads registry.read_full() directly (not the _cache view),
        # so patch that — patching _cache alone let the REAL ~/.geno/registry.json
        # leak in, making this pass/fail on machine state.
        monkeypatch.setattr("geno_tools.registry.read_full", lambda: {
            "geno-dev": {"url": "https://example.com/geno-dev.git",
                         "category": "Developer Tools"},
        })
        monkeypatch.setattr("geno_tools.registry.is_stale", lambda *a, **k: False)
        monkeypatch.setattr("geno_tools.discovery.candidates_by_name", lambda: {})
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
