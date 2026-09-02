"""Install a skillset and register its skills with target agents."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import yaml

from geno_tools.core import config

from .. import agents, paths, registry

SYSTEM_BIN = Path.home() / ".local" / "bin"


def run(args: argparse.Namespace) -> int:
    config.ensure_dir()
    return _install_one(args.name, installing=set())


def _read_manifest(full: str) -> dict:
    return _read_manifest_at(paths.skillset_worktree(full))


def _read_manifest_at(source: Path) -> dict:
    manifest = source / "genotools.yaml"
    if not manifest.exists():
        return {}
    try:
        return yaml.safe_load(manifest.read_text()) or {}
    except Exception:
        return {}


def _get_requires(full: str) -> list[str]:
    raw = _read_manifest(full).get("requires", [])
    if not isinstance(raw, list):
        return []
    return [str(requirement) for requirement in raw]


def _install_one(name_or_source: str, *, installing: set[str]) -> int:
    source, name = _resolve_source(name_or_source)
    if name is None:
        name = _peek_repo_name(source)
    full = paths.normalize(name)

    if paths.skillset_root(full).exists():
        print(f"already installed: {full}")
        return 0

    if full in installing:
        print(f"  circular dependency detected: {full}; skipping", file=sys.stderr)
        return 1
    installing.add(full)

    print(f"installing {full} from {source}")
    root = paths.skillset_root(full)
    root.mkdir(parents=True)
    try:
        _clone_and_worktree(source, full)
        _install_requires(full, installing)
        scripts = _create_venv_if_needed(full)
        _materialize_bin_symlinks(full, scripts)
        paths.skillset_active(full).symlink_to("main")
        _install_skills_via_npx(full)
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise

    print(f"installed {full}")
    return 0


def _install_requires(full: str, installing: set[str]) -> None:
    requirements = _get_requires(full)
    if not requirements:
        return
    print(f"  {full} requires: {', '.join(requirements)}")
    for dependency in requirements:
        if paths.skillset_root(paths.normalize(dependency)).exists():
            continue
        print(f"  installing dependency: {dependency}")
        if _install_one(dependency, installing=installing) != 0:
            raise SystemExit(
                f"failed to install dependency {dependency} required by {full}"
            )


def _resolve_source(name_or_source: str) -> tuple[str, str | None]:
    url = registry.resolve(name_or_source)
    if url:
        return url, name_or_source

    path = Path(name_or_source).expanduser()
    if path.exists() and path.is_dir():
        return str(path.resolve()), None

    if name_or_source.startswith(("http://", "https://", "git@")) or name_or_source.endswith(".git"):
        return name_or_source, None

    raise SystemExit(
        f"unknown skillset: {name_or_source}\n"
        "  not in the discovery cache, not a local path, not a git URL.\n"
        "  run /geno-tools-meta-ecosystem-discover to refresh the cache,\n"
        "  or install directly: geno-tools install <git-url>"
    )


def _peek_repo_name(source: str) -> str:
    path = Path(source)
    if path.exists() and path.is_dir():
        return _read_pyproject_name(path) or path.name

    staging = paths.ROOT / ".staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    try:
        subprocess.check_call(
            ["git", "clone", "--depth", "1", "--quiet", source, str(staging / "repo")]
        )
        name = _read_pyproject_name(staging / "repo")
        return name or source.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _read_pyproject_name(repo_dir: Path) -> str | None:
    return (_read_project(repo_dir).get("project") or {}).get("name")


def _read_project(repo_dir: Path) -> dict:
    pyproject = repo_dir / "pyproject.toml"
    if not pyproject.exists():
        return {}
    try:
        return tomllib.loads(pyproject.read_text())
    except tomllib.TOMLDecodeError:
        return {}


def _clone_and_worktree(source: str, full: str) -> None:
    bare = paths.skillset_git(full)
    subprocess.check_call(["git", "clone", "--bare", "--quiet", source, str(bare)])
    subprocess.check_call(
        [
            "git",
            "-C",
            str(bare),
            "worktree",
            "add",
            str(paths.skillset_worktree(full)),
            _detect_default_branch(bare),
        ]
    )


def _detect_default_branch(bare_repo: Path) -> str:
    output = subprocess.check_output(
        ["git", "-C", str(bare_repo), "symbolic-ref", "--short", "HEAD"],
        text=True,
    ).strip()
    return output or "main"


def _create_venv_if_needed(full: str) -> dict[str, str]:
    worktree = paths.skillset_worktree(full)
    return _create_venv_for_source(
        worktree,
        paths.skillset_venvs(full) / "default",
    )


def _create_venv_for_source(source: Path, venv_dir: Path) -> dict[str, str]:
    project = _read_project(source).get("project", {})
    if not project:
        return {}

    dependencies = project.get("dependencies", []) or []
    scripts = project.get("scripts", {}) or {}
    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    print(f"  creating venv: {venv_dir}")
    subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])

    pip = venv_dir / "bin" / "pip"
    subprocess.check_call([str(pip), "install", "--quiet", "--upgrade", "pip"])
    if dependencies:
        print(f"  installing deps: {', '.join(dependencies)}")
        subprocess.check_call([str(pip), "install", "--quiet", *dependencies])

    print("  installing package (editable)")
    subprocess.check_call([str(pip), "install", "--quiet", "-e", str(source)])
    return scripts


def _materialize_bin_symlinks(full: str, scripts: dict[str, str]) -> None:
    if not scripts:
        return
    SYSTEM_BIN.mkdir(parents=True, exist_ok=True)
    venv_bin = paths.skillset_venvs(full) / "default" / "bin"
    for name in scripts:
        source = venv_bin / name
        if not source.exists():
            print(f"  warn: expected venv binary not found: {source}", file=sys.stderr)
            continue
        destination = SYSTEM_BIN / name
        if destination.is_symlink() or destination.exists():
            existing = destination.readlink() if destination.is_symlink() else None
            if existing == source:
                continue
            print(f"  warn: {destination} already exists; skipping", file=sys.stderr)
            continue
        destination.symlink_to(source)
        print(f"  -> {destination} -> {source}")


def _remove_bin_symlinks(full: str, *, system_bin: Path | None = None) -> None:
    bin_dir = system_bin or SYSTEM_BIN
    if not bin_dir.exists():
        return
    venvs = paths.skillset_venvs(full)
    for entry in bin_dir.iterdir():
        if not entry.is_symlink():
            continue
        try:
            target = entry.readlink()
        except OSError:
            continue
        try:
            (entry.parent / target).resolve().relative_to(venvs.resolve())
        except ValueError:
            continue
        else:
            entry.unlink()
            print(f"  -> removed {entry}")


def _install_skills_via_npx(full: str, agent: str = "*") -> None:
    skill_dirs = _enumerate_skill_dirs(full)
    if not skill_dirs:
        return
    active = paths.skillset_active(full)
    root = active / "skills" if (active / "skills").is_dir() else active
    agent_names = agents.detect_installed() or ["*"] if agent == "*" else [agent]
    scope = "all agents" if agent_names == ["*"] else ", ".join(agent_names)
    print(
        f"  registering {len(skill_dirs)} skill(s) via npx skills "
        f"({scope}, global) — one pass over {root}"
    )
    subprocess.check_call(
        [
            "npx",
            "--yes",
            "skills",
            "add",
            str(root),
            "--agent",
            *agent_names,
            "--global",
            "--full-depth",
            "--yes",
        ]
    )


def _uninstall_skills_via_npx(full: str) -> None:
    _uninstall_skill_names_via_npx(_enumerate_skills(full))


def _uninstall_skill_names_via_npx(
    skill_names: list[str], *, check: bool = False
) -> None:
    skill_names = sorted(set(skill_names))
    if not skill_names:
        return
    print(f"  uninstalling {len(skill_names)} skill(s) via npx skills")
    subprocess.run(
        ["npx", "--yes", "skills", "remove", "--global", "--yes", *skill_names],
        check=check,
    )


def _walk_skill_dirs(root: Path) -> list[Path]:
    found: list[Path] = []

    def walk(directory: Path) -> None:
        if (directory / "SKILL.md").exists():
            found.append(directory)
            return
        for child in sorted(directory.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                walk(child)

    if root.exists():
        for child in sorted(root.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                walk(child)
    return found


def _skill_name(skill_dir: Path, fallback: str) -> str:
    try:
        text = (skill_dir / "SKILL.md").read_text()
        if text.startswith("---"):
            data = yaml.safe_load(text.split("---", 2)[1]) or {}
            name = data.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
    except (OSError, yaml.YAMLError, IndexError):
        pass
    return fallback


def _enumerate_skill_dirs(full: str) -> list[Path]:
    active = paths.skillset_active(full)
    nested = _walk_skill_dirs(active / "skills")
    if nested:
        return nested
    if (active / "SKILL.md").exists():
        return [active]
    return []


def _enumerate_skills(full: str) -> list[str]:
    active = paths.skillset_active(full)
    directories = _enumerate_skill_dirs(full)
    names = _enumerate_registered_skills(full)
    if (active / "SKILL.md").exists() and active not in directories:
        names.insert(0, full)
    return names


def _enumerate_registered_skills(full: str) -> list[str]:
    """Return exactly the names registered by `_install_skills_via_npx`."""
    active = paths.skillset_active(full)
    return [
        _skill_name(directory, full if directory == active else directory.name)
        for directory in _enumerate_skill_dirs(full)
    ]
