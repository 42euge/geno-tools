import json

import pytest
import yaml

from geno_tools.core import config
from geno_tools.sync import lockfile


def _git_values(full: str, *arguments: str) -> str:
    values = {
        ("geno-dev", "remote", "get-url", "origin"): "https://example.test/geno-dev.git",
        ("geno-dev", "branch", "--show-current"): "main",
        ("geno-dev", "rev-parse", "HEAD"): "0123456789abcdef",
    }
    return values[(full, *arguments)]


def test_build_lockfile_exports_stable_skillset_and_allowlisted_config(
    fake_skillset, tmp_config, monkeypatch
):
    fake_skillset("geno-dev", has_pyproject=True)
    (tmp_config / "config.yaml").write_text(
        "aliases:\n  command_prefix: gt\n"
        "discovery:\n  sources: []\n"
        "autonomy: 2\n"
        "mode: user\n"
        "llm:\n  endpoint: secret\n"
    )
    monkeypatch.setattr(lockfile, "_git", _git_values)

    value = lockfile.build_lockfile(
        machine="laptop", generated="2026-09-04T00:00:00Z"
    )

    assert value == {
        "version": 1,
        "machine": "laptop",
        "generated": "2026-09-04T00:00:00Z",
        "skillsets": {
            "geno-dev": {
                "url": "https://example.test/geno-dev.git",
                "branch": "main",
                "sha": "0123456789abcdef",
                "version": "0.1.0",
            }
        },
        "config": {
            "aliases": {"command_prefix": "gt"},
            "discovery": {"sources": []},
            "autonomy": 2,
            "mode": "user",
        },
    }
    assert "llm" not in value["config"]


def test_build_lockfile_reads_stable_main_when_dev_mode_is_selected(
    fake_skillset, tmp_config, monkeypatch
):
    root = fake_skillset("geno-dev", has_pyproject=True)
    checkout = root.parent / "checkout"
    checkout.mkdir()
    (checkout / "pyproject.toml").write_text(
        '[project]\nname = "geno-dev"\nversion = "9.9.9"\n'
    )
    (root / "dev-state.json").write_text(
        json.dumps(
            {
                "version": 1,
                "checkout": str(checkout),
                "venv": None,
                "scripts": [],
            }
        )
    )
    monkeypatch.setattr(lockfile, "_git", _git_values)

    value = lockfile.build_lockfile(machine="laptop", generated="now")

    assert value["skillsets"]["geno-dev"]["version"] == "0.1.0"


def test_parse_lockfile_round_trips_json():
    value = {
        "version": 1,
        "machine": "laptop",
        "generated": "now",
        "skillsets": {},
        "config": {},
    }
    assert lockfile.parse_lockfile(json.dumps(value)) == value


@pytest.mark.parametrize(
    "value, message",
    [
        ("not json", "valid JSON"),
        ({"version": True, "skillsets": {}, "config": {}}, "version True"),
        ({"version": 2, "skillsets": {}, "config": {}}, "version 2"),
        (
            {
                "version": 1,
                "machine": "laptop",
                "generated": "now",
                "skillsets": [],
                "config": {},
            },
            "skillsets",
        ),
        (
            {
                "version": 1,
                "machine": "laptop",
                "generated": "now",
                "skillsets": {"geno-dev": {"url": "x"}},
                "config": {},
            },
            "geno-dev",
        ),
    ],
)
def test_parse_lockfile_rejects_invalid_documents(value, message):
    with pytest.raises(lockfile.LockfileError, match=message):
        lockfile.parse_lockfile(value)


def test_apply_portable_config_preserves_machine_local_keys(tmp_config):
    path = tmp_config / "config.yaml"
    path.write_text(
        "aliases:\n  command_prefix: old\n"
        "discovery:\n  sources: []\n"
        "mode: old\n"
        "llm:\n  endpoint: private\n"
    )

    lockfile.apply_portable_config(
        {"aliases": {"command_prefix": "gt"}, "autonomy": 3}
    )

    value = yaml.safe_load(path.read_text())
    assert value["aliases"] == {"command_prefix": "gt"}
    assert value["autonomy"] == 3
    assert value["mode"] == "old"
    assert value["llm"] == {"endpoint": "private"}


def test_config_load_includes_sync_primary_and_supported_scalars(tmp_config):
    (tmp_config / "config.yaml").write_text(
        "sync:\n  primary: lab\nautonomy: 2\nmode: user\nllm:\n  endpoint: private\n"
    )

    value = config.load()

    assert value["sync"] == {"primary": "lab"}
    assert value["autonomy"] == 2
    assert value["mode"] == "user"
    assert "llm" not in value
