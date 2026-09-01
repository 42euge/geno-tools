"""Tests for commands that manage geno-tools itself."""

from geno_tools.cli import main


class TestSelfUpdate:
    def test_reinstalls_cli_and_points_at_skillset_update(self, monkeypatch, capsys):
        calls = []
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/pipx")
        monkeypatch.setattr(
            "subprocess.call", lambda cmd, **kwargs: calls.append(cmd) or 0
        )

        assert main(["system", "update"]) == 0
        assert any(
            call[0] == "/usr/bin/pipx"
            and "install" in call
            and any("github.com/42euge/geno-tools" in arg for arg in call)
            for call in calls
        )
        out = capsys.readouterr().out
        assert "geno-tools update" in out
        # Homebrew is the only install path; no plugin/marketplace channel.
        assert "/plugin" not in out

    def test_no_pipx_points_at_setup(self, monkeypatch, capsys):
        monkeypatch.setattr("shutil.which", lambda _: None)
        monkeypatch.setattr("geno_tools.core.commands._find_pipx", lambda: None)

        assert main(["system", "update"]) == 1
        assert "geno-tools-setup" in capsys.readouterr().out
