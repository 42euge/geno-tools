"""Managed development checkout activation and rollback."""

from __future__ import annotations

import json
import os
from pathlib import Path
import textwrap

import pytest

from geno_tools.cli import main
from geno_tools.skills_manager import paths
from geno_tools.skills_manager.commands import dev, install


def _write_project(root: Path, *, name: str, version: str, skill: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "genotools.yaml").write_text(
        f'name: {name}\nversion: "{version}"\n'
    )
    (root / "pyproject.toml").write_text(textwrap.dedent(f"""\
        [project]
        name = "{name}"
        version = "{version}"
        dependencies = []

        [project.scripts]
        tt = "fake_tt.cli:main"
    """))
    skill_dir = root / "skills" / skill
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(textwrap.dedent(f"""\
        ---
        name: {skill}
        description: Use when testing {skill}.
        ---
        # {skill}
    """))


@pytest.fixture()
def installed_dev_fixture(tmp_root, tmp_path, monkeypatch):
    root = tmp_root / "geno-tt"
    main_checkout = root / "main"
    _write_project(
        main_checkout,
        name="geno-tt",
        version="0.8.1",
        skill="geno-tt-stable",
    )
    (root / "active").symlink_to("main")
    (root / ".git").mkdir()

    default_venv = root / "venvs" / "default"
    (default_venv / "bin").mkdir(parents=True)
    (default_venv / "bin" / "tt").write_text("stable\n")

    system_bin = tmp_path / "bin"
    system_bin.mkdir()
    (system_bin / "tt").symlink_to(default_venv / "bin" / "tt")
    monkeypatch.setattr(install, "SYSTEM_BIN", system_bin)

    checkout = tmp_path / "rectangle-window-management" / "geno-tt"
    _write_project(
        checkout,
        name="geno-tt",
        version="0.9.0",
        skill="geno-tt-windows-control",
    )

    created_runtimes = []

    def create_runtime(source, venv):
        created_runtimes.append((source, venv))
        (venv / "bin").mkdir(parents=True, exist_ok=True)
        (venv / "bin" / "tt").write_text("dev\n")
        return {"tt": "fake_tt.cli:main"}

    monkeypatch.setattr(install, "_create_venv_for_source", create_runtime)
    monkeypatch.setattr(
        install,
        "_uninstall_skill_names_via_npx",
        lambda names, **kwargs: None,
    )
    registrations = []
    monkeypatch.setattr(
        install,
        "_install_skills_via_npx",
        lambda full: registrations.append(paths.skillset_active(full).resolve()),
    )
    return {
        "root": root,
        "main": main_checkout,
        "checkout": checkout,
        "default_venv": default_venv,
        "system_bin": system_bin,
        "created_runtimes": created_runtimes,
        "registrations": registrations,
    }


def test_activate_builds_managed_runtime_without_checkout_venv(installed_dev_fixture):
    item = installed_dev_fixture

    dev.activate(item["checkout"])

    state = json.loads(paths.skillset_dev_state("geno-tt").read_text())
    assert state["checkout"] == str(item["checkout"].resolve())
    assert Path(state["venv"]).parent == item["root"] / "venvs"
    assert Path(state["venv"]).name.startswith("dev-")
    assert not (item["checkout"] / ".venv").exists()
    assert paths.skillset_active("geno-tt").resolve() == item["checkout"].resolve()
    assert (item["system_bin"] / "tt").resolve() == Path(state["venv"]) / "bin" / "tt"
    assert item["registrations"] == [item["checkout"].resolve()]


def test_deactivate_restores_main_runtime_skills_and_links(installed_dev_fixture):
    item = installed_dev_fixture
    dev.activate(item["checkout"])

    dev.deactivate("geno-tt")

    assert not paths.skillset_dev_state("geno-tt").exists()
    assert os.readlink(paths.skillset_active("geno-tt")) == "main"
    assert paths.skillset_active("geno-tt").resolve() == item["main"].resolve()
    assert (item["system_bin"] / "tt").resolve() == item["default_venv"] / "bin" / "tt"
    assert item["registrations"][-1] == item["main"].resolve()


def test_registration_failure_rolls_back_every_managed_surface(
    installed_dev_fixture, monkeypatch,
):
    item = installed_dev_fixture
    calls = []

    def fail_for_dev(full):
        source = paths.skillset_active(full).resolve()
        calls.append(source)
        if source == item["checkout"].resolve():
            raise RuntimeError("npx failed")

    monkeypatch.setattr(install, "_install_skills_via_npx", fail_for_dev)

    with pytest.raises(dev.DevModeError, match="rolled back"):
        dev.activate(item["checkout"])

    assert paths.skillset_active("geno-tt").resolve() == item["main"].resolve()
    assert (item["system_bin"] / "tt").resolve() == item["default_venv"] / "bin" / "tt"
    assert not paths.skillset_dev_state("geno-tt").exists()
    assert calls == [item["checkout"].resolve(), item["main"].resolve()]


def test_unregistration_failure_rolls_back_every_managed_surface(
    installed_dev_fixture, monkeypatch,
):
    item = installed_dev_fixture
    calls = []

    def fail_for_stable_skill(names, *, check=False):
        calls.append((names, check))
        if names == ["geno-tt-stable"]:
            raise RuntimeError("npx remove failed")

    monkeypatch.setattr(
        install, "_uninstall_skill_names_via_npx", fail_for_stable_skill
    )

    with pytest.raises(dev.DevModeError, match="rolled back"):
        dev.activate(item["checkout"])

    assert paths.skillset_active("geno-tt").resolve() == item["main"].resolve()
    assert (item["system_bin"] / "tt").resolve() == item["default_venv"] / "bin" / "tt"
    assert not paths.skillset_dev_state("geno-tt").exists()
    assert calls == [
        (["geno-tt-stable"], True),
        (["geno-tt-windows-control"], True),
    ]


def test_activate_refuses_checkout_identity_mismatch(installed_dev_fixture):
    item = installed_dev_fixture
    (item["checkout"] / "genotools.yaml").write_text(
        'name: geno-other\nversion: "0.9.0"\n'
    )

    with pytest.raises(dev.DevModeError, match="identity disagrees"):
        dev.activate(item["checkout"])

    assert paths.skillset_active("geno-tt").resolve() == item["main"].resolve()


def test_activate_refuses_unowned_executable(installed_dev_fixture):
    item = installed_dev_fixture
    link = item["system_bin"] / "tt"
    link.unlink()
    link.write_text("someone else's command\n")

    with pytest.raises(dev.DevModeError, match="not owned"):
        dev.activate(item["checkout"])

    assert paths.skillset_active("geno-tt").resolve() == item["main"].resolve()
    assert link.read_text() == "someone else's command\n"


def test_status_reports_mode_source_and_consistency(installed_dev_fixture, capsys):
    item = installed_dev_fixture
    dev.activate(item["checkout"])
    capsys.readouterr()

    assert dev.status("geno-tt") == 0
    output = capsys.readouterr().out

    assert "geno-tt" in output
    assert "dev" in output
    assert "0.9.0" in output
    assert str(item["checkout"]) in output
    assert "ok" in output


def test_dev_cli_routes_activate_status_and_deactivate(installed_dev_fixture, capsys):
    item = installed_dev_fixture

    assert main(["dev", "activate", str(item["checkout"])]) == 0
    assert main(["dev", "status", "geno-tt"]) == 0
    assert main(["dev", "deactivate", "geno-tt"]) == 0

    output = capsys.readouterr().out
    assert "activated geno-tt dev 0.9.0" in output
    assert "deactivated geno-tt dev mode" in output


def test_invalid_state_fails_closed(installed_dev_fixture):
    state = paths.skillset_dev_state("geno-tt")
    state.write_text("not json\n")

    with pytest.raises(dev.DevModeError, match="invalid state"):
        dev.deactivate("geno-tt")


def test_invalid_state_rejects_unsafe_script_name(installed_dev_fixture):
    state = paths.skillset_dev_state("geno-tt")
    state.write_text(json.dumps({
        "version": 1,
        "checkout": "/tmp/geno-tt",
        "venv": "/tmp/venv",
        "scripts": ["../outside"],
    }))

    with pytest.raises(dev.DevModeError, match="invalid state"):
        dev.deactivate("geno-tt")


def test_status_reports_invalid_state_as_drift(installed_dev_fixture, capsys):
    state = paths.skillset_dev_state("geno-tt")
    state.write_text("not json\n")

    assert dev.status("geno-tt") == 1

    assert "DRIFT" in capsys.readouterr().out


def test_deactivate_removes_script_recorded_before_source_changed(
    installed_dev_fixture,
):
    item = installed_dev_fixture
    dev.activate(item["checkout"])

    state_path = paths.skillset_dev_state("geno-tt")
    state = json.loads(state_path.read_text())
    state["scripts"].append("tt-helper")
    state_path.write_text(json.dumps(state))
    helper = Path(state["venv"]) / "bin" / "tt-helper"
    helper.write_text("dev helper\n")
    (item["system_bin"] / "tt-helper").symlink_to(helper)

    dev.deactivate("geno-tt")

    assert not (item["system_bin"] / "tt-helper").exists()


def test_dev_venv_is_stable_per_checkout_path(installed_dev_fixture):
    item = installed_dev_fixture

    first = dev._dev_venv("geno-tt", item["checkout"])
    second = dev._dev_venv("geno-tt", item["checkout"].resolve())

    assert first == second
    assert first.parent == item["root"] / "venvs"
