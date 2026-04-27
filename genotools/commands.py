"""Subcommand dispatch + handler implementations."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from genotools import discovery, paths, registry

SYSTEM_BIN = Path.home() / ".local" / "bin"


def dispatch(args: argparse.Namespace) -> int:
    handlers = {
        "ls": _ls,
        "install": _install,
        "dev": _dev,
        "fork": _fork,
        "use": _use,
        "promote": _promote,
        "update": _update,
        "remove": _remove,
        "doctor": _doctor,
        "discover": _discover,
    }
    return handlers[args.cmd](args)


# ── ls ──────────────────────────────────────────────────────────────────────

def _ls(args: argparse.Namespace) -> int:
    if args.available:
        for name, url in registry.available().items():
            print(f"  {name:<24} {url}")
        for name, url in discovery.candidates_by_name().items():
            if name in registry.available():
                continue
            print(f"  {name:<24} {url}  (discovered)")
        return 0

    if not paths.ROOT.exists():
        print("no skillsets installed")
        return 0

    installed = sorted(
        p.name for p in paths.ROOT.iterdir()
        if p.is_dir() and p.name.startswith("geno-")
        and p.name not in ("geno-bootstrap",)
    )
    if not installed:
        print("no skillsets installed")
        return 0

    for full in installed:
        active = paths.skillset_active(full)
        target = active.readlink().name if active.is_symlink() else "?"
        print(f"  {full:<24} active: {target}")
    return 0


# ── install ─────────────────────────────────────────────────────────────────

def _install(args: argparse.Namespace) -> int:
    if args.here:
        return _todo(f"install --here {args.name}: cwd alias materialization")

    source, name = _resolve_source(args.name)
    if name is None:
        name = _peek_repo_name(source)
    full = paths.normalize(name)

    if paths.skillset_root(full).exists():
        print(f"already installed: {full} "
              f"(remove first: geno-tools remove {full})", file=sys.stderr)
        return 1

    print(f"installing {full} from {source}")
    root = paths.skillset_root(full)
    root.mkdir(parents=True)
    try:
        _clone_and_worktree(source, full)
        scripts = _create_venv_if_needed(full)
        _materialize_bin_symlinks(full, scripts)
        paths.skillset_active(full).symlink_to("main")
        _install_skills_via_npx(full)
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise

    print(f"installed {full}")
    return 0


# ── remove ──────────────────────────────────────────────────────────────────

def _remove(args: argparse.Namespace) -> int:
    full = paths.normalize(args.name)
    root = paths.skillset_root(full)
    if not root.exists():
        print(f"not installed: {full}", file=sys.stderr)
        return 1

    _uninstall_skills_via_npx(full)
    _remove_bin_symlinks(full)

    if args.keep_data:
        for child in root.iterdir():
            if child.name in ("venvs", ".worktrees"):
                continue
            if child.is_symlink() or child.is_file():
                child.unlink()
            else:
                shutil.rmtree(child, ignore_errors=True)
    else:
        shutil.rmtree(root, ignore_errors=True)

    print(f"removed {full}")
    return 0


# ── source resolution ───────────────────────────────────────────────────────

def _resolve_source(name_or_source: str) -> tuple[str, str | None]:
    url = registry.resolve(name_or_source)
    if url:
        return url, name_or_source

    p = Path(name_or_source).expanduser()
    if p.exists() and p.is_dir():
        return str(p.resolve()), None

    if name_or_source.startswith(("http://", "https://", "git@")) \
       or name_or_source.endswith(".git"):
        return name_or_source, None

    discovered = discovery.candidates_by_name()
    if name_or_source in discovered:
        return discovered[name_or_source], name_or_source

    raise SystemExit(
        f"unknown skillset: {name_or_source} "
        f"(not in registry, not in discovery sources, not a path, not a git URL)"
    )


def _peek_repo_name(source: str) -> str:
    p = Path(source)
    if p.exists() and p.is_dir():
        name = _read_pyproject_name(p)
        return name or p.name

    staging = paths.ROOT / ".staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    try:
        subprocess.check_call(
            ["git", "clone", "--depth", "1", "--quiet", source,
             str(staging / "repo")]
        )
        name = _read_pyproject_name(staging / "repo")
        if name:
            return name
        return source.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _read_pyproject_name(repo_dir: Path) -> str | None:
    pj = repo_dir / "pyproject.toml"
    if not pj.exists():
        return None
    try:
        data = tomllib.loads(pj.read_text())
    except tomllib.TOMLDecodeError:
        return None
    return (data.get("project") or {}).get("name")


# ── git ─────────────────────────────────────────────────────────────────────

def _clone_and_worktree(source: str, full: str) -> None:
    bare = paths.skillset_git(full)
    subprocess.check_call(
        ["git", "clone", "--bare", "--quiet", source, str(bare)]
    )
    default_branch = _detect_default_branch(bare)
    subprocess.check_call([
        "git", "-C", str(bare), "worktree", "add",
        str(paths.skillset_worktree(full, "main")), default_branch,
    ])


def _detect_default_branch(bare_repo: Path) -> str:
    out = subprocess.check_output(
        ["git", "-C", str(bare_repo), "symbolic-ref", "--short", "HEAD"],
        text=True,
    ).strip()
    return out or "main"


# ── venv ────────────────────────────────────────────────────────────────────

def _create_venv_if_needed(full: str) -> dict[str, str]:
    worktree = paths.skillset_worktree(full, "main")
    pyproject = worktree / "pyproject.toml"
    if not pyproject.exists():
        return {}

    data = tomllib.loads(pyproject.read_text())
    project = data.get("project", {})
    if not project:
        return {}

    deps = project.get("dependencies", []) or []
    scripts = project.get("scripts", {}) or {}

    venv_dir = paths.skillset_venvs(full) / "default"
    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    print(f"  creating venv: {venv_dir}")
    subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])

    pip = venv_dir / "bin" / "pip"
    subprocess.check_call(
        [str(pip), "install", "--quiet", "--upgrade", "pip"]
    )

    if deps:
        print(f"  installing deps: {', '.join(deps)}")
        subprocess.check_call([str(pip), "install", "--quiet", *deps])

    print(f"  installing package (editable)")
    subprocess.check_call(
        [str(pip), "install", "--quiet", "-e", str(worktree)]
    )

    return scripts


def _materialize_bin_symlinks(full: str, scripts: dict[str, str]) -> None:
    if not scripts:
        return
    SYSTEM_BIN.mkdir(parents=True, exist_ok=True)
    venv_bin = paths.skillset_venvs(full) / "default" / "bin"
    for name in scripts:
        src = venv_bin / name
        if not src.exists():
            print(f"  warn: expected venv binary not found: {src}",
                  file=sys.stderr)
            continue
        dst = SYSTEM_BIN / name
        if dst.is_symlink() or dst.exists():
            existing = dst.readlink() if dst.is_symlink() else None
            if existing == src:
                continue
            print(f"  warn: {dst} already exists; skipping", file=sys.stderr)
            continue
        dst.symlink_to(src)
        print(f"  -> {dst} -> {src}")


def _remove_bin_symlinks(full: str) -> None:
    if not SYSTEM_BIN.exists():
        return
    venv_bin = paths.skillset_venvs(full) / "default" / "bin"
    for entry in SYSTEM_BIN.iterdir():
        if not entry.is_symlink():
            continue
        try:
            target = entry.readlink()
        except OSError:
            continue
        target_abs = (entry.parent / target).resolve()
        if str(target_abs).startswith(str(venv_bin)):
            entry.unlink()
            print(f"  -> removed {entry}")


# ── npx skills ──────────────────────────────────────────────────────────────

def _install_skills_via_npx(full: str) -> None:
    active = paths.skillset_active(full)
    print(f"  installing skills via npx skills (all agents, global)")
    subprocess.check_call([
        "npx", "--yes", "skills", "add", str(active),
        "--agent", "*", "--global", "--skill", "*", "--yes",
    ])


def _uninstall_skills_via_npx(full: str) -> None:
    skill_names = _enumerate_skills(full)
    if not skill_names:
        return
    print(f"  uninstalling {len(skill_names)} skill(s) via npx skills")
    subprocess.run(
        ["npx", "--yes", "skills", "remove", "--global", "--yes",
         *skill_names],
        check=False,
    )


def _enumerate_skills(full: str) -> list[str]:
    active = paths.skillset_active(full)
    names: list[str] = []
    # Root-level SKILL.md → the skill name is the skillset name itself.
    if (active / "SKILL.md").exists():
        names.append(full)
    # Sub-skills in a skills/ directory.
    skills_dir = active / "skills"
    if skills_dir.exists():
        names.extend(sorted(
            p.name for p in skills_dir.iterdir()
            if p.is_dir() and (p / "SKILL.md").exists()
        ))
    return names


# ── stubs (later phases) ────────────────────────────────────────────────────

def _dev(args: argparse.Namespace) -> int:
    return _todo(f"dev {args.name} {args.path}")


def _fork(args: argparse.Namespace) -> int:
    return _todo(f"fork {args.name} {args.variant}")


def _use(args: argparse.Namespace) -> int:
    return _todo(f"use {args.spec}")


def _promote(args: argparse.Namespace) -> int:
    return _todo(f"promote {args.name} {args.variant}")


def _update(args: argparse.Namespace) -> int:
    return _todo(f"update {args.name or '<all>'}")


def _doctor(_: argparse.Namespace) -> int:
    return _todo("doctor")


def _discover(_: argparse.Namespace) -> int:
    srcs = discovery.sources()
    if not srcs:
        print("no discovery sources configured (~/.geno/config.yaml: discovery.sources)")
        return 0

    found = discovery.candidates()
    if not found:
        print("no candidates found across configured sources")
        return 0

    for c in found:
        marker = "" if c.has_skill_md else "  (no SKILL.md — skipped)"
        print(f"  [{c.source}] {c.name:<32} {c.url}{marker}")
    return 0


def _todo(msg: str) -> int:
    print(f"[not yet implemented] {msg}", file=sys.stderr)
    return 2
