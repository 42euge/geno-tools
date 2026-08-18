"""Tests for commands that manage geno-tools itself."""

from geno_tools.cli import main


class TestSelfUpdate:
    def test_reinstalls_cli_and_prints_reload(self, monkeypatch, capsys):
        calls = []
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/pipx")
        monkeypatch.setattr(
            "subprocess.call", lambda cmd, **kwargs: calls.append(cmd) or 0
        )

        assert main(["update"]) == 0
        assert any(
            call[0] == "/usr/bin/pipx"
            and "install" in call
            and any("github.com/42euge/geno-tools" in arg for arg in call)
            for call in calls
        )
        assert "/reload-plugins" in capsys.readouterr().out

    def test_no_pipx_points_at_setup(self, monkeypatch, capsys):
        monkeypatch.setattr("shutil.which", lambda _: None)
        monkeypatch.setattr("geno_tools.core.commands._find_pipx", lambda: None)

        assert main(["update"]) == 1
        assert "geno-tools-setup" in capsys.readouterr().out
