"""Atomically select and restore editable skillset development checkouts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

from .. import paths
from . import install


STATE_VERSION = 1
ROLLBACK_VERSION = 1


class DevModeError(RuntimeError):
    """Raised when dev mode cannot switch every managed surface safely."""


def _valid_script_name(name: str) -> bool:
    return bool(name) and name not in {".", ".."} and Path(name).name == name


def run(args: argparse.Namespace) -> int:
    try:
        if args.dev_action == "activate":
            activate(Path(args.checkout))
        elif args.dev_action == "deactivate":
            deactivate(args.name)
        elif args.dev_action == "rollback":
            rollback(args.name)
        elif args.dev_action == "status":
            return status(args.name)
        else:
            raise DevModeError("Use 'geno-tools dev activate|status|deactivate'.")
    except DevModeError as exc:
        print(f"dev mode: {exc}", file=sys.stderr)
        return 1
    return 0


def _checkout_identity(checkout: Path) -> tuple[str, Path]:
    source = checkout.expanduser().resolve()
    if not source.is_dir():
        raise DevModeError(f"checkout does not exist: {source}")

    manifest_name = install._read_manifest_at(source).get("name")
    project_name = (install._read_project(source).get("project") or {}).get("name")
    names = {
        str(name).strip()
        for name in (manifest_name, project_name)
        if isinstance(name, str) and name.strip()
    }
    if not names:
        raise DevModeError(
            f"{source} has no skillset identity in genotools.yaml or pyproject.toml"
        )
    if len(names) != 1:
        raise DevModeError(
            "checkout identity disagrees between genotools.yaml and pyproject.toml: "
            + ", ".join(sorted(names))
        )
    full = paths.normalize(names.pop())
    if not paths.skillset_root(full).is_dir():
        raise DevModeError(
            f"{full} is not installed; run 'geno-tools install {source}' first"
        )
    if source == paths.skillset_worktree(full).resolve():
        raise DevModeError(
            f"{source} is the managed stable checkout; use 'geno-tools dev deactivate {full}'"
        )
    return full, source


def _read_state(full: str, *, strict: bool = True) -> dict | None:
    state_path = paths.skillset_dev_state(full)
    if not state_path.exists():
        return None
    try:
        value = json.loads(state_path.read_text())
    except (OSError, ValueError) as exc:
        if strict:
            raise DevModeError(f"invalid state file {state_path}: {exc}") from exc
        return None
    valid = (
        isinstance(value, dict)
        and value.get("version") == STATE_VERSION
        and isinstance(value.get("checkout"), str)
        and isinstance(value.get("scripts"), list)
        and all(
            isinstance(item, str) and _valid_script_name(item)
            for item in value["scripts"]
        )
        and (value.get("venv") is None or isinstance(value.get("venv"), str))
    )
    if not valid:
        if strict:
            raise DevModeError(f"invalid state file {state_path}: unsupported schema")
        return None
    return value


def _project_details(source: Path) -> tuple[str, dict[str, str]]:
    project = install._read_project(source).get("project") or {}
    version = str(
        install._read_manifest_at(source).get("version")
        or project.get("version")
        or "?"
    )
    scripts = project.get("scripts") or {}
    if not isinstance(scripts, dict):
        raise DevModeError(f"project.scripts must be a table in {source / 'pyproject.toml'}")
    normalized = {str(name): str(target) for name, target in scripts.items()}
    unsafe = [name for name in normalized if not _valid_script_name(name)]
    if unsafe:
        raise DevModeError(
            f"project.scripts contains unsafe names: {', '.join(sorted(unsafe))}"
        )
    return version, normalized


def _dev_venv(full: str, source: Path) -> Path:
    digest = hashlib.sha256(str(source).encode()).hexdigest()[:12]
    return paths.skillset_venvs(full) / f"dev-{digest}"


def _prepare_runtime(full: str, source: Path) -> tuple[Path | None, dict[str, str]]:
    _version, scripts = _project_details(source)
    if not install._read_project(source).get("project"):
        return None, {}

    venv = _dev_venv(full, source)
    existed = venv.exists()
    try:
        installed_scripts = install._create_venv_for_source(source, venv)
    except (OSError, subprocess.CalledProcessError) as exc:
        if not existed:
            shutil.rmtree(venv, ignore_errors=True)
        raise DevModeError(f"could not build development runtime: {exc}") from exc
    if set(installed_scripts) != set(scripts):
        scripts = installed_scripts
    missing = [name for name in scripts if not (venv / "bin" / name).exists()]
    if missing:
        if not existed:
            shutil.rmtree(venv, ignore_errors=True)
        raise DevModeError(
            f"development runtime is missing console scripts: {', '.join(sorted(missing))}"
        )
    return venv, scripts


def _prepare_stable_runtime(full: str) -> tuple[Path | None, dict[str, str]]:
    source = paths.skillset_worktree(full)
    _version, scripts = _project_details(source)
    if not install._read_project(source).get("project"):
        return None, {}
    venv = paths.skillset_venvs(full) / "default"
    if any(not (venv / "bin" / name).exists() for name in scripts):
        try:
            scripts = install._create_venv_if_needed(full)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise DevModeError(f"could not restore stable runtime: {exc}") from exc
    return venv, scripts


def _owned_bin_link(full: str, link: Path) -> bool:
    if not link.is_symlink():
        return False
    try:
        link.resolve().relative_to(paths.skillset_venvs(full).resolve())
    except ValueError:
        return False
    return True


def _snapshot_bin_links(full: str, names: set[str]) -> dict[str, str | None]:
    install.SYSTEM_BIN.mkdir(parents=True, exist_ok=True)
    snapshot: dict[str, str | None] = {}
    for name in sorted(names):
        link = install.SYSTEM_BIN / name
        if link.exists() or link.is_symlink():
            if not _owned_bin_link(full, link):
                raise DevModeError(
                    f"refusing to replace executable not owned by {full}: {link}"
                )
            snapshot[name] = os.readlink(link)
        else:
            snapshot[name] = None
    return snapshot


def _replace_symlink(link: Path, target: str | Path) -> None:
    temporary = link.with_name(f".{link.name}.geno-dev-{uuid.uuid4().hex}")
    try:
        temporary.symlink_to(target)
        os.replace(temporary, link)
    finally:
        if temporary.is_symlink():
            temporary.unlink()


def _apply_bin_links(
    full: str,
    snapshot: dict[str, str | None],
    venv: Path | None,
    scripts: dict[str, str],
) -> None:
    for name in sorted(snapshot):
        link = install.SYSTEM_BIN / name
        if name not in scripts:
            if link.is_symlink():
                link.unlink()
            continue
        if venv is None:
            raise DevModeError(f"{name} has no target runtime")
        target = venv / "bin" / name
        if not target.exists():
            raise DevModeError(f"console script was not installed: {target}")
        _replace_symlink(link, target)


def _restore_bin_links(snapshot: dict[str, str | None]) -> None:
    for name, target in snapshot.items():
        link = install.SYSTEM_BIN / name
        if target is None:
            if link.is_symlink():
                link.unlink()
        else:
            _replace_symlink(link, target)


def _replace_active(full: str, target: str | Path) -> None:
    active = paths.skillset_active(full)
    if not active.is_symlink():
        raise DevModeError(f"managed active link is missing or unsafe: {active}")
    _replace_symlink(active, target)


def _write_state(full: str, state: dict | None) -> None:
    state_path = paths.skillset_dev_state(full)
    if state is None:
        if state_path.exists():
            state_path.unlink()
        return
    state_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".dev-state.", dir=state_path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(state, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, state_path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _rollback_path(full: str) -> Path:
    return paths.skillset_root(full) / "dev-rollback.json"


def preserve_rollback(name: str) -> None:
    """Remember the current stable/dev selection without modifying it."""
    full = paths.normalize(name)
    state = _read_state(full)
    value = {
        "version": ROLLBACK_VERSION,
        "kind": "dev" if state else "stable",
        "state": state,
    }
    destination = _rollback_path(full)
    destination.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def rollback(name: str) -> None:
    """Restore the selection saved by :func:`preserve_rollback`."""
    full = paths.normalize(name)
    source_file = _rollback_path(full)
    try:
        value = json.loads(source_file.read_text())
    except FileNotFoundError as exc:
        raise DevModeError(f"{full} has no rollback selection") from exc
    except (OSError, ValueError) as exc:
        raise DevModeError(f"invalid rollback selection {source_file}: {exc}") from exc
    if value.get("version") != ROLLBACK_VERSION or value.get("kind") not in {
        "stable",
        "dev",
    }:
        raise DevModeError(f"invalid rollback selection {source_file}")
    if value["kind"] == "stable":
        deactivate(full)
    else:
        state = value.get("state")
        if not isinstance(state, dict) or not isinstance(state.get("checkout"), str):
            raise DevModeError(f"invalid rollback selection {source_file}")
        source = Path(state["checkout"])
        venv, scripts = _prepare_runtime(full, source)
        restored = {
            "version": STATE_VERSION,
            "checkout": str(source.resolve()),
            "venv": str(venv) if venv else None,
            "scripts": sorted(scripts),
        }
        _switch(
            full,
            active_target=source,
            venv=venv,
            scripts=scripts,
            state=restored,
        )
        version, _scripts = _project_details(source)
        print(f"rolled back {full} to dev {version}")
        print(f"  source {source}")
    source_file.unlink()


def _restore_state(full: str, previous: bytes | None) -> None:
    state_path = paths.skillset_dev_state(full)
    if previous is None:
        if state_path.exists():
            state_path.unlink()
    else:
        state_path.write_bytes(previous)


def _switch(
    full: str,
    *,
    active_target: str | Path,
    venv: Path | None,
    scripts: dict[str, str],
    state: dict | None,
) -> None:
    active = paths.skillset_active(full)
    if not active.is_symlink():
        raise DevModeError(f"managed active link is missing or unsafe: {active}")
    old_active = os.readlink(active)
    old_source = active.resolve()
    _old_version, old_scripts = _project_details(old_source)
    old_state = _read_state(full, strict=False)
    state_path = paths.skillset_dev_state(full)
    previous_state = state_path.read_bytes() if state_path.exists() else None
    old_script_names = set(old_scripts)
    if old_state:
        old_script_names.update(old_state["scripts"])
    script_names = old_script_names | set(scripts)
    snapshot = _snapshot_bin_links(full, script_names)
    old_skills = set(install._enumerate_registered_skills(full))
    new_skills: set[str] = set()

    try:
        _replace_active(full, active_target)
        _apply_bin_links(full, snapshot, venv, scripts)
        new_skills = set(install._enumerate_registered_skills(full))
        install._install_skills_via_npx(full)
        install._uninstall_skill_names_via_npx(
            sorted(old_skills - new_skills), check=True
        )
        _write_state(full, state)
    except Exception as exc:
        try:
            _replace_active(full, old_active)
            _restore_bin_links(snapshot)
            _restore_state(full, previous_state)
            install._install_skills_via_npx(full)
            install._uninstall_skill_names_via_npx(
                sorted(new_skills - old_skills), check=True
            )
        except Exception as rollback_exc:
            raise DevModeError(
                f"switch failed ({exc}); rollback also failed ({rollback_exc})"
            ) from exc
        if isinstance(exc, DevModeError):
            raise
        raise DevModeError(f"switch failed and was rolled back: {exc}") from exc


def activate(checkout: Path) -> None:
    full, source = _checkout_identity(checkout)
    venv, scripts = _prepare_runtime(full, source)
    state = {
        "version": STATE_VERSION,
        "checkout": str(source),
        "venv": str(venv) if venv else None,
        "scripts": sorted(scripts),
    }
    _switch(
        full,
        active_target=source,
        venv=venv,
        scripts=scripts,
        state=state,
    )
    version, _scripts = _project_details(source)
    print(f"activated {full} dev {version}")
    print(f"  source {source}")
    if venv:
        print(f"  runtime {venv}")


def deactivate(name: str) -> None:
    full = paths.normalize(name)
    if not paths.skillset_root(full).is_dir():
        raise DevModeError(f"{full} is not installed")
    state = _read_state(full)
    if state is None:
        print(f"{full} is already using stable main")
        return
    source = paths.skillset_worktree(full)
    venv, scripts = _prepare_stable_runtime(full)
    _switch(
        full,
        active_target="main",
        venv=venv,
        scripts=scripts,
        state=None,
    )
    version, _scripts = _project_details(source)
    print(f"deactivated {full} dev mode; restored stable {version}")


def _commit(source: Path) -> str:
    try:
        commit = subprocess.check_output(
            ["git", "-C", str(source), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        dirty = subprocess.check_output(
            ["git", "-C", str(source), "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "?"
    return f"{commit}+dirty" if dirty else commit


def active_details(full: str) -> dict:
    state_path = paths.skillset_dev_state(full)
    state = _read_state(full, strict=False)
    state_valid = not state_path.exists() or state is not None
    mode = "dev" if state else "stable"
    source = (
        Path(state["checkout"])
        if state
        else paths.skillset_worktree(full)
    )
    version, scripts = _project_details(source) if source.is_dir() else ("?", {})
    selected_scripts = set(state["scripts"]) if state else set(scripts)
    expected_venv = (
        Path(state["venv"])
        if state and state.get("venv")
        else paths.skillset_venvs(full) / "default"
    )
    consistent = state_valid and paths.skillset_active(full).is_symlink()
    if consistent:
        consistent = paths.skillset_active(full).resolve() == source.resolve()
    if state and set(scripts) != selected_scripts:
        consistent = False
    for name in selected_scripts:
        link = install.SYSTEM_BIN / name
        expected = expected_venv / "bin" / name
        if not link.is_symlink() or link.resolve() != expected.resolve():
            consistent = False
    return {
        "name": full,
        "mode": mode,
        "version": version,
        "commit": _commit(source),
        "source": str(source),
        "consistent": consistent,
    }


def stable_details(full: str) -> dict:
    source = paths.skillset_worktree(full)
    version, _scripts = _project_details(source) if source.is_dir() else ("?", {})
    try:
        branch = subprocess.check_output(
            ["git", "-C", str(source), "branch", "--show-current"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or "?"
    except (OSError, subprocess.CalledProcessError):
        branch = "?"
    return {
        "mode": "stable",
        "version": version,
        "branch": branch,
        "commit": _commit(source),
        "source": str(source),
    }


def selection_details(full: str) -> dict:
    return {
        "active": active_details(full),
        "stable": stable_details(full),
        "rollback": _rollback_path(full).exists(),
    }


def status(name: str | None = None) -> int:
    if name:
        full = paths.normalize(name)
        if not paths.skillset_root(full).is_dir():
            raise DevModeError(f"{full} is not installed")
        names = [full]
    else:
        names = sorted(
            item.name
            for item in paths.ROOT.iterdir()
            if item.is_dir()
            and item.name.startswith("geno-")
            and item.name != "geno-bootstrap"
        ) if paths.ROOT.exists() else []
    if not names:
        print("no installed skillsets")
        return 0

    print("geno-tools dev")
    failures = 0
    for full in names:
        selection = selection_details(full)
        details = selection["active"]
        health = "ok" if details["consistent"] else "DRIFT"
        if health != "ok":
            failures += 1
        print(
            f"  {full:<24} {details['mode']:<6} {details['version']:<10} "
            f"{details['commit']:<14} {health}"
        )
        print(f"    {details['source']}")
        if details["mode"] == "dev":
            stable = selection["stable"]
            print(
                f"    deactivate restores stable {stable['version']} "
                f"{stable['branch']} {stable['commit']}"
            )
            print(f"      {stable['source']}")
        if selection["rollback"]:
            print("    rollback available")
    return 1 if failures else 0
