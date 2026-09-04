import json

import pytest

from geno_tools.sync import package


LOCK = {
    "version": 1,
    "machine": "laptop",
    "generated": "now",
    "skillsets": {
        "geno-dev": {
            "url": "https://example.test/geno-dev.git",
            "branch": "main",
            "sha": "1" * 40,
            "version": "1.0.0",
        },
        "geno-tt": {
            "url": "https://example.test/geno-tt.git",
            "branch": "main",
            "sha": "2" * 40,
            "version": "0.8.1",
        },
    },
    "config": {},
}


SNAPSHOT = {
    "version": 1,
    "machine": "laptop",
    "captured": "now",
    "source": "/tmp/geno-tt",
    "project_version": "0.9.0",
    "branch": "feature",
    "commit": "3" * 40,
    "origin": None,
    "dirty": {"cached": False, "worktree": True, "untracked": 0},
    "fingerprint": "a" * 64,
    "artifacts": {
        "bundle": "YQ==",
        "cached_diff": "",
        "worktree_diff": "Yg==",
        "untracked_tar": "Yw==",
    },
}


def test_build_stable_only_package_keeps_the_v1_lockfile(monkeypatch):
    monkeypatch.setattr(package.lockfile, "build_lockfile", lambda: LOCK)

    value = package.build({"geno-dev": "stable", "geno-tt": "stable"})

    assert value == {
        "protocol": 1,
        "lockfile": LOCK,
        "selections": {
            "geno-dev": {"kind": "stable"},
            "geno-tt": {"kind": "stable"},
        },
    }


def test_build_mixed_package_captures_only_the_selected_active_checkout(monkeypatch):
    monkeypatch.setattr(package.lockfile, "build_lockfile", lambda: LOCK)
    monkeypatch.setattr(
        package.dev,
        "selection_details",
        lambda name: {
            "active": {"mode": "dev", "source": f"/tmp/{name}"},
            "stable": {},
            "rollback": False,
        },
    )
    captured = []
    monkeypatch.setattr(
        package.snapshot,
        "capture",
        lambda source, *, machine: captured.append((str(source), machine)) or SNAPSHOT,
    )

    value = package.build({"geno-dev": "stable", "geno-tt": "active"})

    assert value["selections"]["geno-dev"] == {"kind": "stable"}
    assert value["selections"]["geno-tt"] == {
        "kind": "dev",
        "snapshot": SNAPSHOT,
    }
    assert captured == [("/tmp/geno-tt", "laptop")]


def test_parse_package_round_trips_json_and_reports_decoded_artifact_size():
    value = {
        "protocol": 1,
        "lockfile": LOCK,
        "selections": {
            "geno-dev": {"kind": "stable"},
            "geno-tt": {"kind": "dev", "snapshot": SNAPSHOT},
        },
    }

    assert package.parse(json.dumps(value)) == value
    assert package.artifact_size(value) == 3


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda value: value.update(protocol=2), "protocol 2"),
        (
            lambda value: value["selections"].pop("geno-dev"),
            "exactly match",
        ),
        (
            lambda value: value["selections"]["geno-tt"].update(kind="other"),
            "geno-tt",
        ),
    ],
)
def test_parse_package_rejects_unsupported_protocol_and_selections(mutate, message):
    value = {
        "protocol": 1,
        "lockfile": LOCK,
        "selections": {
            "geno-dev": {"kind": "stable"},
            "geno-tt": {"kind": "dev", "snapshot": SNAPSHOT},
        },
    }
    mutate(value)

    with pytest.raises(package.PackageError, match=message):
        package.parse(value)
