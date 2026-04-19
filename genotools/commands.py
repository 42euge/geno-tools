"""Subcommand dispatch + handler implementations."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from genotools import bootstrap, paths, registry


# Where venv binaries get symlinked so SKILL.md can call them as bare names.
SYSTEM_BIN = Path.home() / ".local" / "bin"


# ── Dispatch ────────────────────────────────────────────────────────────────

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
    }
    return handlers[args.cmd](args)


# ── ls ──────────────────────────────────────────────────────────────────────

def _ls(args: argparse.Namespace) -> int:
    if args.available:
        for name, url in registry.available().items():
            print(f"  {name:<12} {url}")
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
        full = paths.normalize(args.name)
        if not paths.skillset_root(full).exists():
            print(f"not installed globally: {full} "
                  f"(install first: geno-tools install {paths.short(full)})", file=sys.stderr)
            return 1
        n = bootstrap.materialize_cwd_aliases([full])
        print(f"✓ materialized {n} alias(es) in <cwd>/.claude/skills/")
        return 0

    source, name = _resolve_source(args.name)
    if name is None:
        name = _peek_repo_name(source)
    full = paths.normalize(name)

    if paths.skillset_root(full).exists():
        print(f"already installed: {full} "
              f"(remove first: geno-tools remove {paths.short(full)})", file=sys.stderr)
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
        bootstrap.ensure_hook_registered()
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise

    print(f"✓ installed {full}")
    return 0


# ── remove ──────────────────────────────────────────────────────────────────

def _remove(args: argparse.Namespace) -> int:
    full = paths.normalize(args.name)
    root = paths.skillset_root(full)
    if not root.exists():
        print(f"not installed: {full}", file=sys.stderr)
        return 1

    bootstrap.remove_cwd_aliases(full)
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

    # If no skillsets remain, remove the SessionStart hook.
    remaining = [
        p.name for p in paths.ROOT.iterdir()
        if p.is_dir() and p.name.startswith("geno-")
    ] if paths.ROOT.exists() else []
    if not remaining:
        bootstrap.remove_hook()

    print(f"removed {full}")
    return 0


# ── source resolution ───────────────────────────────────────────────────────

def _resolve_source(name_or_source: str) -> tuple[str, str | None]:
    """Return (source, known_name). Known_name is set only for registry hits."""
    url = registry.resolve(name_or_source)
    if url:
        return url, name_or_source

    p = Path(name_or_source).expanduser()
    if p.exists() and p.is_dir():
        return str(p.resolve()), None

    if name_or_source.startswith(("http://", "https://", "git@")) \
       or name_or_source.endswith(".git"):
        return name_or_source, None

    raise SystemExit(
        f"unknown skillset: {name_or_source} (not in registry, not a path, not a git URL)"
    )


def _peek_repo_name(source: str) -> str:
    """Determine the canonical skillset name from a source URL or path.

    Priority:
      1. pyproject.toml [project].name (cloned shallow if remote)
      2. Repo basename (URL tail or directory name)
    """
    p = Path(source)
    if p.exists() and p.is_dir():
        name = _read_pyproject_name(p)
        return name or p.name

    # Remote URL: shallow clone to staging.
    staging = paths.ROOT / ".staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    try:
        subprocess.check_call(
            ["git", "clone", "--depth", "1", "--quiet", source, str(staging / "repo")]
        )
        name = _read_pyproject_name(staging / "repo")
        if name:
            return name
        # Fall back to URL tail
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
    subprocess.check_call(["git", "clone", "--bare", "--quiet", source, str(bare)])

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
    """Create venv + editable install if the worktree has a Python project.

    Returns a dict of {script_name: script_target} from [project.scripts],
    or {} if no Python project.
    """
    worktree = paths.skillset_worktree(full, "main")
    pyproject = worktree / "pyproject.toml"
    if not pyproject.exists():
        return {}

    data = tomllib.loads(pyproject.read_text())
    project = data.get("project", {})
    deps = project.get("dependencies", []) or []
    scripts = project.get("scripts", {}) or {}

    # If no [project] table at all, skip venv.
    if not project:
        return {}

    venv_dir = paths.skillset_venvs(full) / "default"
    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    print(f"  creating venv: {venv_dir}")
    subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])

    pip = venv_dir / "bin" / "pip"
    subprocess.check_call([str(pip), "install", "--quiet", "--upgrade", "pip"])

    if deps:
        print(f"  installing deps: {', '.join(deps)}")
        subprocess.check_call([str(pip), "install", "--quiet", *deps])

    # Editable install of the project itself materializes [project.scripts] binaries.
    print(f"  installing package (editable)")
    subprocess.check_call([str(pip), "install", "--quiet", "-e", str(worktree)])

    return scripts


def _materialize_bin_symlinks(full: str, scripts: dict[str, str]) -> None:
    """Symlink each [project.scripts] entry into ~/.local/bin/."""
    if not scripts:
        return
    SYSTEM_BIN.mkdir(parents=True, exist_ok=True)
    venv_bin = paths.skillset_venvs(full) / "default" / "bin"
    for name in scripts:
        src = venv_bin / name
        if not src.exists():
            print(f"  warn: expected venv binary not found: {src}", file=sys.stderr)
            continue
        dst = SYSTEM_BIN / name
        if dst.is_symlink() or dst.exists():
            existing = dst.readlink() if dst.is_symlink() else None
            if existing == src:
                continue  # already correct
            print(f"  warn: {dst} already exists; skipping", file=sys.stderr)
            continue
        dst.symlink_to(src)
        print(f"  ↳ {dst} -> {src}")


def _remove_bin_symlinks(full: str) -> None:
    """Drop ~/.local/bin/ symlinks that point into this skillset's venv."""
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
        # Resolve to absolute for comparison
        target_abs = (entry.parent / target).resolve()
        if str(target_abs).startswith(str(venv_bin)):
            entry.unlink()
            print(f"  ↳ removed {entry}")


# ── npx skills ──────────────────────────────────────────────────────────────

def _install_skills_via_npx(full: str) -> None:
    active = paths.skillset_active(full)
    print(f"  installing skills via npx skills (claude-code, global)")
    subprocess.check_call([
        "npx", "--yes", "skills", "add", str(active),
        "--agent", "claude-code", "--global", "--skill", "*", "--yes",
    ])


def _uninstall_skills_via_npx(full: str) -> None:
    skill_names = _enumerate_skills(full)
    if not skill_names:
        return
    print(f"  uninstalling {len(skill_names)} skill(s) via npx skills")
    cmd = ["npx", "--yes", "skills", "remove", "--global", "--yes", *skill_names]
    subprocess.run(cmd, check=False)


def _enumerate_skills(full: str) -> list[str]:
    """Return skill folder names in the active worktree's skills/ dir."""
    skills_dir = paths.skillset_active(full) / "skills"
    if not skills_dir.exists():
        return []
    return sorted(p.name for p in skills_dir.iterdir()
                  if p.is_dir() and (p / "SKILL.md").exists())


# ── fork ────────────────────────────────────────────────────────────────────

def _fork(args: argparse.Namespace) -> int:
    full = paths.normalize(args.name)
    if not paths.skillset_root(full).exists():
        print(f"not installed: {full}", file=sys.stderr)
        return 1

    variant = args.variant
    if variant in ("main", "active"):
        print(f"reserved variant name: {variant}", file=sys.stderr)
        return 1

    worktree = paths.skillset_worktree(full, variant)
    if worktree.exists():
        print(f"variant already exists: {full}@{variant}", file=sys.stderr)
        return 1

    main_wt = paths.skillset_worktree(full, "main")
    if main_wt.is_symlink():
        print(f"can't fork: {full} is in dev mode (no bare repo). "
              "Switch to a normal install first.", file=sys.stderr)
        return 1

    bare = paths.skillset_git(full)
    print(f"forking {full}@{variant}")
    subprocess.check_call([
        "git", "-C", str(bare), "worktree", "add", "-b", variant, str(worktree),
    ])

    if args.isolated_venv:
        _create_venv_for_variant(full, variant, worktree)

    print(f"✓ forked {full}@{variant}")
    return 0


def _create_venv_for_variant(full: str, variant: str, worktree: Path) -> None:
    pyproject = worktree / "pyproject.toml"
    if not pyproject.exists():
        print(f"  no pyproject.toml; skipping venv")
        return
    data = tomllib.loads(pyproject.read_text())
    project = data.get("project", {})
    deps = project.get("dependencies", []) or []
    if not project:
        return

    venv_dir = paths.skillset_venvs(full) / variant
    print(f"  creating isolated venv: {venv_dir}")
    subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
    pip = venv_dir / "bin" / "pip"
    subprocess.check_call([str(pip), "install", "--quiet", "--upgrade", "pip"])
    if deps:
        subprocess.check_call([str(pip), "install", "--quiet", *deps])
    subprocess.check_call([str(pip), "install", "--quiet", "-e", str(worktree)])


# ── use ─────────────────────────────────────────────────────────────────────

def _use(args: argparse.Namespace) -> int:
    name, sep, variant = args.spec.partition("@")
    if not sep or not variant:
        print(f"expected <name>@<variant>, got: {args.spec}", file=sys.stderr)
        return 1
    full = paths.normalize(name)

    if not paths.skillset_root(full).exists():
        print(f"not installed: {full}", file=sys.stderr)
        return 1

    if args.here:
        target_path = paths.skillset_worktree(full, variant)
        if not target_path.exists():
            print(f"variant not found: {full}@{variant}", file=sys.stderr)
            return 1
        # Remove existing cwd aliases for this skillset, then re-materialize
        # pointing at the variant's skills.
        bootstrap.remove_cwd_aliases(full)
        cwd_skills = Path.cwd() / ".claude" / "skills"
        cwd_skills.mkdir(parents=True, exist_ok=True)
        skills_dir = target_path / "skills"
        if skills_dir.exists():
            tool = paths.short(full)
            for skill_dir in sorted(skills_dir.iterdir()):
                if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
                    continue
                skill_name = skill_dir.name
                if skill_name == full:
                    alias = f"gt-{tool}"
                else:
                    rest = skill_name.removeprefix(f"{full}-")
                    alias = f"gt-{rest}" if rest != skill_name else f"gt-{skill_name}"
                alias_path = cwd_skills / alias
                if alias_path.is_symlink() or alias_path.exists():
                    alias_path.unlink()
                alias_path.symlink_to(skill_dir.resolve())
                print(f"  ↳ {alias} -> {skill_name} (variant: {variant})")
        print(f"✓ cwd aliases for {full}: {variant}")
        return 0

    target_path = paths.skillset_worktree(full, variant)
    if not target_path.exists():
        print(f"variant not found: {full}@{variant}", file=sys.stderr)
        return 1

    # Determine the relative target for the active symlink.
    target_rel = "main" if variant == "main" else f".worktrees/{variant}"

    active = paths.skillset_active(full)
    if active.is_symlink() or active.exists():
        active.unlink()
    active.symlink_to(target_rel)

    # If the variant has its own venv, repoint ~/.local/bin/ symlinks to it.
    variant_venv = paths.skillset_venvs(full) / variant
    if variant_venv.exists():
        _repoint_bin_symlinks(full, variant)
    # else: shared venv — bin symlinks already point at venvs/default/, no change needed.

    # Refresh skill installs (npx skills copies, doesn't symlink, so we need to re-add).
    _install_skills_via_npx(full)

    print(f"✓ active variant for {full}: {variant}")
    return 0


def _repoint_bin_symlinks(full: str, variant: str) -> None:
    """Replace ~/.local/bin/ symlinks pointing into another venv with this variant's."""
    if not SYSTEM_BIN.exists():
        return
    venvs_root = paths.skillset_venvs(full)
    target_bin = venvs_root / variant / "bin"
    if not target_bin.exists():
        return

    for entry in SYSTEM_BIN.iterdir():
        if not entry.is_symlink():
            continue
        try:
            link_target = (entry.parent / entry.readlink()).resolve()
        except OSError:
            continue
        # If the symlink already points into this skillset's venvs/, repoint to the variant.
        if not str(link_target).startswith(str(venvs_root.resolve())):
            continue
        new_target = target_bin / entry.name
        if not new_target.exists():
            continue
        entry.unlink()
        entry.symlink_to(new_target)
        print(f"  ↳ repointed {entry} -> {new_target}")


# ── dev ─────────────────────────────────────────────────────────────────────

def _dev(args: argparse.Namespace) -> int:
    """Install with main as a symlink to a local checkout (live edits)."""
    src = Path(args.path).expanduser().resolve()
    if not src.is_dir():
        print(f"not a directory: {src}", file=sys.stderr)
        return 1

    full = paths.normalize(args.name)

    if paths.skillset_root(full).exists():
        print(f"already installed: {full} "
              f"(remove first: geno-tools remove {paths.short(full)})", file=sys.stderr)
        return 1

    print(f"dev-linking {full} -> {src}")
    root = paths.skillset_root(full)
    root.mkdir(parents=True)
    try:
        # No bare repo, no worktree: main IS a symlink to the live checkout.
        # `fork` won't work in dev mode (no bare repo); user must `remove` and
        # `install` from the proper source to enable variant management.
        paths.skillset_worktree(full, "main").symlink_to(src)
        scripts = _create_venv_for_dev(full, src)
        _materialize_bin_symlinks(full, scripts)
        paths.skillset_active(full).symlink_to("main")
        _install_skills_via_npx(full)
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise

    print(f"✓ dev-linked {full}")
    return 0


def _create_venv_for_dev(full: str, src: Path) -> dict[str, str]:
    """Like _create_venv_if_needed but installs editable from the local src path."""
    pyproject = src / "pyproject.toml"
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
    subprocess.check_call([str(pip), "install", "--quiet", "--upgrade", "pip"])
    if deps:
        print(f"  installing deps: {', '.join(deps)}")
        subprocess.check_call([str(pip), "install", "--quiet", *deps])
    print(f"  installing package (editable, dev)")
    subprocess.check_call([str(pip), "install", "--quiet", "-e", str(src)])

    return scripts


# ── promote ────────────────────────────────────────────────────────────────

def _promote(args: argparse.Namespace) -> int:
    full = paths.normalize(args.name)
    variant = args.variant
    if variant in ("main", "active"):
        print(f"reserved variant name: {variant}", file=sys.stderr)
        return 1

    main_wt = paths.skillset_worktree(full, "main")
    variant_wt = paths.skillset_worktree(full, variant)
    if not main_wt.exists():
        print(f"main worktree missing: {main_wt}", file=sys.stderr)
        return 1
    if not variant_wt.exists():
        print(f"variant not found: {full}@{variant}", file=sys.stderr)
        return 1

    # Refuse to promote in dev mode (main is a symlink to a live checkout).
    if main_wt.is_symlink():
        print(f"can't promote: {full} is in dev mode (main is a symlink). "
              "Switch to a normal install first.", file=sys.stderr)
        return 1

    print(f"promoting {full}@{variant} -> main")
    subprocess.check_call(["git", "-C", str(main_wt), "merge", "--no-edit", variant])
    print(f"✓ merged into main; push when ready")
    return 0


# ── update ─────────────────────────────────────────────────────────────────

def _update(args: argparse.Namespace) -> int:
    if args.name:
        names = [paths.normalize(args.name)]
    else:
        if not paths.ROOT.exists():
            print("no skillsets installed")
            return 0
        names = sorted(
            p.name for p in paths.ROOT.iterdir()
            if p.is_dir() and p.name.startswith("geno-")
            and p.name not in ("geno-bootstrap",)
        )

    rc = 0
    for full in names:
        main_wt = paths.skillset_worktree(full, "main")
        if not main_wt.exists():
            print(f"{full}: main worktree missing", file=sys.stderr)
            rc = 1
            continue
        if main_wt.is_symlink():
            print(f"{full}: dev mode, source is live ({main_wt.readlink()})")
            continue
        print(f"{full}: pulling…")
        result = subprocess.run(
            ["git", "-C", str(main_wt), "pull", "--ff-only"],
            check=False,
        )
        if result.returncode != 0:
            rc = result.returncode
    return rc


# ── doctor ─────────────────────────────────────────────────────────────────

def _doctor(_: argparse.Namespace) -> int:
    if not paths.ROOT.exists():
        print("no ~/.geno-tools/; nothing to check")
        return 0

    issues = 0
    installed = sorted(
        p.name for p in paths.ROOT.iterdir()
        if p.is_dir() and p.name.startswith("geno-")
        and p.name not in ("geno-bootstrap",)
    )
    if not installed:
        print("no skillsets installed")
        return 0

    for full in installed:
        print(f"{full}:")
        root = paths.skillset_root(full)

        active = paths.skillset_active(full)
        if not active.is_symlink():
            print(f"  ✗ active symlink missing")
            issues += 1
        else:
            target = root / active.readlink()
            if not target.exists():
                print(f"  ✗ active points to missing target: {target}")
                issues += 1
            else:
                print(f"  ✓ active -> {active.readlink()}")

        main_wt = paths.skillset_worktree(full, "main")
        if not main_wt.exists():
            print(f"  ✗ main worktree missing")
            issues += 1

        # Per-variant worktree checks
        worktrees_root = root / ".worktrees"
        if worktrees_root.exists():
            for v in sorted(p.name for p in worktrees_root.iterdir() if p.is_dir()):
                if not (worktrees_root / v).exists():
                    print(f"  ✗ variant worktree dir missing: {v}")
                    issues += 1

        # Venv check (only if pyproject exists in active worktree)
        if (active / "pyproject.toml").exists():
            venv = paths.skillset_venvs(full) / "default"
            if not venv.exists():
                print(f"  ! pyproject present but no venv at {venv}")
                # Not a hard issue — could be intentional

    if issues:
        print(f"\n{issues} issue(s) found")
        return 1
    print("\nall good")
    return 0


def _todo(msg: str) -> int:
    print(f"[not yet implemented] {msg}", file=sys.stderr)
    return 2
