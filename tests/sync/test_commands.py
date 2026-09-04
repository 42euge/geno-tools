import io
import json
import subprocess

import pytest

from geno_tools.cli import main
from geno_tools.sync import reconcile
from geno_tools.sync.commands import apply as apply_command
from geno_tools.sync.commands import export as export_command
from geno_tools.sync.commands import pull as pull_command
from geno_tools.sync.commands import push as push_command
from geno_tools.sync.commands import status as status_command
from geno_tools.sync.transport import Host, HostRegistry


LOCK = {
    "version": 1,
    "machine": "laptop",
    "generated": "now",
    "skillsets": {},
    "config": {},
}
REMOTE_LOCK = {**LOCK, "machine": "lab"}


def completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr=stderr)


@pytest.mark.parametrize("command", ["export", "status", "pull", "push", "apply"])
def test_sync_subcommands_have_help(command, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["sync", command, "--help"])
    assert exc.value.code == 0


def test_sync_without_command_prints_help(capsys):
    assert main(["sync"]) == 0
    assert "export" in capsys.readouterr().out


def test_sync_export_prints_only_json(monkeypatch, capsys):
    monkeypatch.setattr(export_command, "build_lockfile", lambda: LOCK)
    assert main(["sync", "export"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == LOCK


def test_sync_status_defaults_to_all_non_local_hosts(monkeypatch, capsys):
    registry = HostRegistry(
        "local",
        {
            "local": Host("local", "localhost", True),
            "lab": Host("lab", "buildbox", False),
        },
    )
    calls = []
    monkeypatch.setattr(status_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(status_command, "build_lockfile", lambda: LOCK)
    monkeypatch.setattr(
        status_command,
        "run_remote",
        lambda host, command: calls.append((host.alias, command))
        or completed(stdout=json.dumps(REMOTE_LOCK)),
    )

    assert main(["sync", "status"]) == 0
    assert calls == [("lab", ["geno-tools", "sync", "export"])]
    assert "lab" in capsys.readouterr().out


def test_sync_status_continues_after_offline_host(monkeypatch, capsys):
    registry = HostRegistry(
        None,
        {
            "offline": Host("offline", "down", False),
            "lab": Host("lab", "buildbox", False),
        },
    )
    monkeypatch.setattr(status_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(status_command, "build_lockfile", lambda: LOCK)
    monkeypatch.setattr(
        status_command,
        "run_remote",
        lambda host, _command: completed(returncode=255, stderr="no route")
        if host.alias == "offline"
        else completed(stdout=json.dumps(REMOTE_LOCK)),
    )

    assert main(["sync", "status", "offline", "lab"]) == 0
    out = capsys.readouterr().out
    assert "offline" in out
    assert "lab" in out


def test_sync_status_fails_when_every_host_is_offline(monkeypatch, capsys):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    monkeypatch.setattr(status_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(status_command, "build_lockfile", lambda: LOCK)
    monkeypatch.setattr(
        status_command,
        "run_remote",
        lambda _host, _command: completed(returncode=255, stderr="no route"),
    )
    assert main(["sync", "status", "lab"]) == 1
    assert "offline" in capsys.readouterr().out


@pytest.mark.parametrize(
    "result, text",
    [
        (completed(returncode=127, stderr="command not found"), "not installed"),
        (completed(stdout="not json"), "invalid lockfile"),
    ],
)
def test_sync_status_distinguishes_remote_tool_and_schema_errors(
    result, text, monkeypatch, capsys
):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    monkeypatch.setattr(status_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(status_command, "build_lockfile", lambda: LOCK)
    monkeypatch.setattr(status_command, "run_remote", lambda *_args: result)
    assert main(["sync", "status", "lab"]) == 1
    assert text in capsys.readouterr().out


def test_sync_pull_uses_primary_and_reconciles_remote_export(monkeypatch):
    registry = HostRegistry(
        "tt-default",
        {
            "tt-default": Host("tt-default", "otherbox", False),
            "lab": Host("lab", "buildbox", False),
        },
    )
    received = []
    monkeypatch.setattr(pull_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(
        pull_command.config, "load", lambda: {"sync": {"primary": "lab"}}
    )
    monkeypatch.setattr(
        pull_command,
        "run_remote",
        lambda host, command: completed(stdout=json.dumps(REMOTE_LOCK)),
    )
    monkeypatch.setattr(
        pull_command,
        "reconcile_installation",
        lambda source, options: received.append((source, options))
        or reconcile.ReconcileResult((), (), False),
    )

    assert main(["sync", "pull", "--yes", "--no-rebuild"]) == 0
    assert received == [
        (
            REMOTE_LOCK,
            reconcile.ReconcileOptions(yes=True, rebuild=False),
        )
    ]


def test_sync_pull_without_host_or_primary_fails(monkeypatch, capsys):
    registry = HostRegistry("lab", {"lab": Host("lab", "buildbox", False)})
    monkeypatch.setattr(pull_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(
        pull_command.config, "load", lambda: {"sync": {"primary": ""}}
    )
    assert main(["sync", "pull"]) == 1
    assert "sync.primary" in capsys.readouterr().err


def test_sync_apply_reads_stdin_and_reconciles(monkeypatch):
    received = []
    monkeypatch.setattr(apply_command.sys, "stdin", io.StringIO(json.dumps(REMOTE_LOCK)))
    monkeypatch.setattr(
        apply_command,
        "reconcile_installation",
        lambda source, options: received.append((source, options))
        or reconcile.ReconcileResult((), (), False),
    )

    assert main(["sync", "apply", "-", "--dry-run"]) == 0
    assert received == [
        (REMOTE_LOCK, reconcile.ReconcileOptions(dry_run=True))
    ]


def test_sync_apply_rejects_malformed_stdin_without_reconciling(monkeypatch, capsys):
    monkeypatch.setattr(apply_command.sys, "stdin", io.StringIO("bad"))
    monkeypatch.setattr(
        apply_command,
        "reconcile_installation",
        lambda *_args: pytest.fail("malformed input must not reconcile"),
    )
    assert main(["sync", "apply", "-"]) == 1
    assert "valid JSON" in capsys.readouterr().err


def test_sync_push_pipes_local_lockfile_to_remote_apply(monkeypatch):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    calls = []
    monkeypatch.setattr(push_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(push_command, "build_lockfile", lambda: LOCK)
    monkeypatch.setattr(
        push_command,
        "run_remote",
        lambda host, command, input_text=None: calls.append(
            (host.alias, command, input_text)
        )
        or completed(),
    )

    assert main(["sync", "push", "lab", "--yes", "--no-rebuild"]) == 0
    assert calls == [
        (
            "lab",
            ["geno-tools", "sync", "apply", "-", "--yes", "--no-rebuild"],
            json.dumps(LOCK, sort_keys=True),
        )
    ]


def test_sync_push_propagates_dry_run_and_transport_failure(
    monkeypatch, capsys
):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    commands = []
    monkeypatch.setattr(push_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(push_command, "build_lockfile", lambda: LOCK)
    monkeypatch.setattr(
        push_command,
        "run_remote",
        lambda _host, command, input_text=None: commands.append(command)
        or completed(returncode=5, stderr="failed"),
    )

    assert main(["sync", "push", "lab", "--dry-run"]) == 1
    assert "--dry-run" in commands[0]
    assert "lab" in capsys.readouterr().err
