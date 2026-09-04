import subprocess

import pytest

from geno_tools.sync import transport


def _ok() -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], 0, stdout="{}\n", stderr="")


def test_load_host_registry_resolves_localhost_and_ssh_target(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        'default_host = "local"\n[hosts]\nlocal = "localhost"\nlab = "buildbox"\n'
    )

    registry = transport.load_host_registry(path)

    assert registry.default_host == "local"
    assert registry.hosts["local"] == transport.Host("local", "localhost", True)
    assert registry.hosts["lab"] == transport.Host("lab", "buildbox", False)


@pytest.mark.parametrize(
    "contents, message",
    [
        (None, "tt add-host"),
        ("not = toml =", "invalid"),
        ('default_host = "local"\n', "no hosts"),
        ('[hosts]\nlab = 2\n', "string destination"),
    ],
)
def test_load_host_registry_rejects_unusable_config(tmp_path, contents, message):
    path = tmp_path / "config.toml"
    if contents is not None:
        path.write_text(contents)
    with pytest.raises(transport.TransportError, match=message):
        transport.load_host_registry(path)


def test_resolve_host_rejects_unknown_alias(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[hosts]\nlab = "buildbox"\n')
    registry = transport.load_host_registry(path)
    with pytest.raises(transport.TransportError, match="unknown host.*missing"):
        transport.resolve_host("missing", registry)


def test_run_uses_direct_command_for_localhost(monkeypatch):
    calls = []
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs)) or _ok(),
    )

    result = transport.run(
        transport.Host("local", "localhost", True),
        ["geno-tools", "sync", "export"],
    )

    assert result.returncode == 0
    assert calls == [
        (
            ["geno-tools", "sync", "export"],
            {
                "text": True,
                "capture_output": True,
                "input": None,
                "check": False,
            },
        )
    ]


def test_run_quotes_remote_command_and_preserves_stdin(monkeypatch):
    calls = []
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs)) or _ok(),
    )

    transport.run(
        transport.Host("lab", "buildbox", False),
        ["geno-tools", "sync", "apply", "-"],
        input_text='{"version": 1}',
    )

    assert calls == [
        (
            ["ssh", "buildbox", "geno-tools sync apply -"],
            {
                "text": True,
                "capture_output": True,
                "input": '{"version": 1}',
                "check": False,
            },
        )
    ]
