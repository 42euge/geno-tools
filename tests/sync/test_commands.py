import io
import base64
import json
import subprocess

import pytest

from geno_tools.cli import main
from geno_tools.sync import reconcile
from geno_tools.sync.commands import apply as apply_command
from geno_tools.sync.commands import export as export_command
from geno_tools.sync.commands import inventory as inventory_command
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
INVENTORY = {
    "protocol": 1,
    "machine": "laptop",
    "generated": "now",
    "lockfile": LOCK,
    "skillsets": {},
}
REMOTE_INVENTORY = {
    **INVENTORY,
    "machine": "lab",
    "lockfile": REMOTE_LOCK,
}
PACKAGE = {"protocol": 1, "lockfile": LOCK, "selections": {}}
SKILL = {
    "url": "https://example.test/geno-tt.git",
    "branch": "main",
    "sha": "1" * 40,
    "version": "0.8.1",
}
ACTIVE_LOCK = {**LOCK, "skillsets": {"geno-tt": SKILL}}
ACTIVE_INVENTORY = {
    "protocol": 1,
    "machine": "laptop",
    "generated": "now",
    "lockfile": ACTIVE_LOCK,
    "skillsets": {
        "geno-tt": {
            "stable": SKILL,
            "active": {
                "project_version": "0.9.0",
                "branch": "feature",
                "commit": "2" * 40,
                "source": "/tmp/geno-tt",
                "dirty": {"cached": True, "worktree": False, "untracked": 1},
                "fingerprint": "a" * 64,
                "transfer_size": 1024,
            },
            "rollback": False,
        }
    },
}


def completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr=stderr)


@pytest.mark.parametrize(
    "command", ["export", "inventory", "status", "pull", "push", "apply"]
)
def test_sync_subcommands_have_help(command, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["sync", command, "--help"])
    assert exc.value.code == 0


def test_sync_without_command_prints_help(capsys):
    assert main(["sync"]) == 0
    assert "export" in capsys.readouterr().out


@pytest.mark.parametrize("command", ["push", "pull"])
@pytest.mark.parametrize("source", ["ask", "stable", "active"])
def test_sync_transfer_commands_accept_dev_source_policy(
    command, source, monkeypatch
):
    module = push_command if command == "push" else pull_command
    received = []
    monkeypatch.setattr(module, "run", lambda args: received.append(args) or 0)
    arguments = ["sync", command]
    if command == "push":
        arguments.append("lab")
    arguments.extend(["--dev-source", source])

    assert main(arguments) == 0
    assert received[0].dev_source == source


def test_sync_export_prints_only_json(monkeypatch, capsys):
    monkeypatch.setattr(export_command, "build_lockfile", lambda: LOCK)
    assert main(["sync", "export"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == LOCK


def test_sync_inventory_prints_protocol_metadata(monkeypatch, capsys):
    monkeypatch.setattr(inventory_command, "build_inventory", lambda: INVENTORY)

    assert main(["sync", "inventory"]) == 0
    assert json.loads(capsys.readouterr().out) == INVENTORY


def test_sync_export_builds_package_from_argument_safe_selection_json(
    monkeypatch, capsys
):
    selections = {"geno-dev": "active", "geno-tt": "stable"}
    encoded = base64.urlsafe_b64encode(
        json.dumps(selections, sort_keys=True).encode()
    ).decode()
    received = []
    monkeypatch.setattr(
        export_command.sync_package,
        "build",
        lambda value: received.append(value) or PACKAGE,
    )

    assert main(["sync", "export", "--selection-json", encoded]) == 0
    assert received == [selections]
    assert json.loads(capsys.readouterr().out) == PACKAGE


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
    monkeypatch.setattr(status_command.selection, "inventory", lambda: INVENTORY)
    monkeypatch.setattr(
        status_command,
        "run_remote",
        lambda host, command: calls.append((host.alias, command))
        or completed(stdout=json.dumps(REMOTE_INVENTORY)),
    )

    assert main(["sync", "status"]) == 0
    assert calls == [("lab", ["geno-tools", "sync", "inventory"])]
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
    monkeypatch.setattr(status_command.selection, "inventory", lambda: INVENTORY)
    monkeypatch.setattr(
        status_command,
        "run_remote",
        lambda host, _command: completed(returncode=255, stderr="no route")
        if host.alias == "offline"
        else completed(stdout=json.dumps(REMOTE_INVENTORY)),
    )

    assert main(["sync", "status", "offline", "lab"]) == 0
    out = capsys.readouterr().out
    assert "offline" in out
    assert "lab" in out


def test_sync_status_fails_when_every_host_is_offline(monkeypatch, capsys):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    monkeypatch.setattr(status_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(status_command.selection, "inventory", lambda: INVENTORY)
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
        (completed(stdout="not json"), "invalid inventory"),
    ],
)
def test_sync_status_distinguishes_remote_tool_and_schema_errors(
    result, text, monkeypatch, capsys
):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    monkeypatch.setattr(status_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(status_command.selection, "inventory", lambda: INVENTORY)
    monkeypatch.setattr(status_command, "run_remote", lambda *_args: result)
    assert main(["sync", "status", "lab"]) == 1
    assert text in capsys.readouterr().out


def test_sync_status_requires_active_fingerprints_to_match(monkeypatch, capsys):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    remote = json.loads(json.dumps(ACTIVE_INVENTORY))
    remote["machine"] = "lab"
    remote["lockfile"] = {**ACTIVE_LOCK, "machine": "lab"}
    remote["skillsets"]["geno-tt"]["active"]["fingerprint"] = "b" * 64
    monkeypatch.setattr(status_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(
        status_command.selection, "inventory", lambda: ACTIVE_INVENTORY
    )
    monkeypatch.setattr(
        status_command,
        "run_remote",
        lambda *_args: completed(stdout=json.dumps(remote)),
    )

    assert main(["sync", "status", "lab"]) == 0
    output = capsys.readouterr().out
    assert "fingerprint" in output
    assert "in sync" not in output


def test_sync_status_reports_matching_stable_and_active_state_in_sync(
    monkeypatch, capsys
):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    remote = json.loads(json.dumps(ACTIVE_INVENTORY))
    remote["machine"] = "lab"
    remote["lockfile"] = {**ACTIVE_LOCK, "machine": "lab"}
    monkeypatch.setattr(status_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(
        status_command.selection, "inventory", lambda: ACTIVE_INVENTORY
    )
    monkeypatch.setattr(
        status_command,
        "run_remote",
        lambda *_args: completed(stdout=json.dumps(remote)),
    )

    assert main(["sync", "status", "lab"]) == 0
    assert "in sync" in capsys.readouterr().out


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
        lambda host, command: completed(
            stdout=json.dumps(REMOTE_INVENTORY)
            if command[-1] == "inventory"
            else json.dumps({**PACKAGE, "lockfile": REMOTE_LOCK})
        ),
    )
    monkeypatch.setattr(
        pull_command,
        "reconcile_package",
        lambda source, options: received.append((source, options))
        or reconcile.ReconcileResult((), (), False),
    )

    assert main(
        [
            "sync",
            "pull",
            "--yes",
            "--no-rebuild",
            "--dev-source",
            "stable",
        ]
    ) == 0
    assert received == [
        (
            {**PACKAGE, "lockfile": REMOTE_LOCK},
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


def test_sync_pull_chooses_from_remote_inventory_and_encodes_selection(
    monkeypatch
):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    package = {
        "protocol": 1,
        "lockfile": ACTIVE_LOCK,
        "selections": {"geno-tt": {"kind": "dev", "snapshot": {}}},
    }
    calls = []
    monkeypatch.setattr(pull_command, "load_host_registry", lambda: registry)

    def remote(_host, command):
        calls.append(command)
        if command[-1] == "inventory":
            return completed(stdout=json.dumps(ACTIVE_INVENTORY))
        return completed(stdout=json.dumps(package))

    monkeypatch.setattr(pull_command, "run_remote", remote)
    monkeypatch.setattr(pull_command.sync_package, "parse", lambda value: value)
    monkeypatch.setattr(pull_command.sync_package, "artifact_size", lambda _value: 0)
    monkeypatch.setattr(
        pull_command,
        "reconcile_package",
        lambda *_args: reconcile.ReconcileResult((), (), False),
    )

    assert main(
        ["sync", "pull", "lab", "--dev-source", "active", "--yes"]
    ) == 0
    export_command_line = calls[1]
    assert export_command_line[:3] == ["geno-tools", "sync", "export"]
    encoded = export_command_line[export_command_line.index("--selection-json") + 1]
    assert json.loads(base64.urlsafe_b64decode(encoded)) == {"geno-tt": "active"}


def test_sync_pull_reports_remote_inventory_protocol_mismatch(monkeypatch, capsys):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    monkeypatch.setattr(pull_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(
        pull_command,
        "run_remote",
        lambda *_args: completed(stdout=json.dumps(REMOTE_LOCK)),
    )

    assert main(["sync", "pull", "lab", "--dev-source", "stable"]) == 1
    assert "protocol" in capsys.readouterr().err


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


def test_sync_apply_accepts_a_selection_package(monkeypatch):
    value = {"protocol": 1, "lockfile": LOCK, "selections": {}}
    received = []
    monkeypatch.setattr(apply_command.sys, "stdin", io.StringIO(json.dumps(value)))
    monkeypatch.setattr(
        apply_command,
        "reconcile_package",
        lambda source, options: received.append((source, options))
        or reconcile.ReconcileResult((), (), False),
    )

    assert main(["sync", "apply", "-"]) == 0
    assert received == [(value, reconcile.ReconcileOptions())]


def test_sync_apply_requires_yes_for_packages_over_100_mib(monkeypatch, capsys):
    value = {"protocol": 1, "lockfile": LOCK, "selections": {}}
    monkeypatch.setattr(apply_command.sys, "stdin", io.StringIO(json.dumps(value)))
    monkeypatch.setattr(
        apply_command.sync_package,
        "artifact_size",
        lambda _value: 100 * 1024 * 1024 + 1,
    )
    monkeypatch.setattr(
        apply_command,
        "reconcile_package",
        lambda *_args: pytest.fail("oversize package must not reconcile"),
    )

    assert main(["sync", "apply", "-"]) == 1
    assert "--yes" in capsys.readouterr().err


def test_sync_push_pipes_selected_package_to_remote_apply(monkeypatch):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    calls = []
    monkeypatch.setattr(push_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(push_command.selection, "inventory", lambda: INVENTORY)
    monkeypatch.setattr(push_command.sync_package, "build", lambda _value: PACKAGE)
    monkeypatch.setattr(
        push_command,
        "run_remote",
        lambda host, command, input_text=None: calls.append(
            (host.alias, command, input_text)
        )
        or completed(),
    )

    assert main(
        [
            "sync",
            "push",
            "lab",
            "--yes",
            "--no-rebuild",
            "--dev-source",
            "stable",
        ]
    ) == 0
    assert calls == [
        (
            "lab",
            ["geno-tools", "sync", "apply", "-", "--yes", "--no-rebuild"],
            json.dumps(PACKAGE, sort_keys=True),
        )
    ]


def test_sync_push_prompts_per_skillset_and_passes_the_choices(monkeypatch):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    received = []
    monkeypatch.setattr(push_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(
        push_command.selection, "inventory", lambda: ACTIVE_INVENTORY
    )
    monkeypatch.setattr(push_command.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(
        push_command.terminal,
        "choose_one",
        lambda candidate, remaining: "active",
    )
    monkeypatch.setattr(
        push_command.sync_package,
        "build",
        lambda choices: received.append(choices) or PACKAGE,
    )
    monkeypatch.setattr(push_command, "run_remote", lambda *_args, **_kw: completed())

    assert main(["sync", "push", "lab"]) == 0
    assert received == [{"geno-tt": "active"}]


def test_sync_push_dry_run_fetches_inventory_but_sends_no_package(
    monkeypatch, capsys
):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    calls = []
    monkeypatch.setattr(push_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(push_command.selection, "inventory", lambda: INVENTORY)
    monkeypatch.setattr(
        push_command,
        "run_remote",
        lambda _host, command, input_text=None: calls.append((command, input_text))
        or completed(stdout=json.dumps(REMOTE_INVENTORY)),
    )

    assert main(
        ["sync", "push", "lab", "--dry-run", "--dev-source", "stable"]
    ) == 0
    assert calls == [(["geno-tools", "sync", "inventory"], None)]
    assert "in sync" in capsys.readouterr().out


def test_sync_push_large_transfer_confirmation_does_not_approve_removals(
    monkeypatch
):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    commands = []
    monkeypatch.setattr(push_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(
        push_command.selection, "inventory", lambda: ACTIVE_INVENTORY
    )
    monkeypatch.setattr(push_command.sync_package, "build", lambda _value: PACKAGE)
    monkeypatch.setattr(
        push_command.sync_package,
        "artifact_size",
        lambda _value: 100 * 1024 * 1024 + 1,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    monkeypatch.setattr(
        push_command,
        "run_remote",
        lambda _host, command, input_text=None: commands.append(command) or completed(),
    )

    assert main(
        ["sync", "push", "lab", "--dev-source", "active"]
    ) == 0
    assert "--allow-large" in commands[0]
    assert "--yes" not in commands[0]


def test_sync_push_propagates_dry_run_and_transport_failure(
    monkeypatch, capsys
):
    registry = HostRegistry(None, {"lab": Host("lab", "buildbox", False)})
    commands = []
    monkeypatch.setattr(push_command, "load_host_registry", lambda: registry)
    monkeypatch.setattr(push_command.selection, "inventory", lambda: INVENTORY)
    monkeypatch.setattr(
        push_command,
        "run_remote",
        lambda _host, command, input_text=None: commands.append((command, input_text))
        or completed(returncode=5, stderr="failed"),
    )

    assert main(
        [
            "sync",
            "push",
            "lab",
            "--dry-run",
            "--dev-source",
            "stable",
        ]
    ) == 1
    assert commands == [(["geno-tools", "sync", "inventory"], None)]
    assert "lab" in capsys.readouterr().err
