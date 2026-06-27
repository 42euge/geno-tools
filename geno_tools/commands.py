"""Subcommand dispatch + handler implementations."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

import yaml

from geno_tools import config, discovery, paths, registry

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
        "deps": _deps,
        "doctor": _doctor,
        "discover": _discover,
        "scan": _scan,
        "docs": _docs,
    }
    return handlers[args.cmd](args)


# ── ls ──────────────────────────────────────────────────────────────────────

def _ls(args: argparse.Namespace) -> int:
    if args.available:
        repos = registry.available()
        if not repos:
            print("  no skillsets discovered yet.")
            print("  run /geno-tools-meta-ecosystem-discover to find them,")
            print("  or install directly by git URL: geno-tools install <url>")
            return 0
        for name, url in sorted(repos.items()):
            print(f"  {name:<24} {url}")
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


# ── manifest ───────────────────────────────────────────────────────────────

def _read_manifest(full: str) -> dict:
    worktree = paths.skillset_worktree(full, "main")
    manifest = worktree / "genotools.yaml"
    if not manifest.exists():
        return {}
    try:
        return yaml.safe_load(manifest.read_text()) or {}
    except Exception:
        return {}


def _get_requires(full: str) -> list[str]:
    manifest = _read_manifest(full)
    raw = manifest.get("requires", [])
    if not isinstance(raw, list):
        return []
    return [str(r) for r in raw]


# ── install ─────────────────────────────────────────────────────────────────

def _install(args: argparse.Namespace) -> int:
    if args.here:
        return _todo(f"install --here {args.name}: cwd alias materialization")
    config.ensure_dir()
    return _install_one(args.name, installing=set())


def _install_one(name_or_source: str, *, installing: set[str]) -> int:
    source, name = _resolve_source(name_or_source)
    if name is None:
        name = _peek_repo_name(source)
    full = paths.normalize(name)

    if paths.skillset_root(full).exists():
        print(f"already installed: {full}")
        return 0

    if full in installing:
        print(f"  circular dependency detected: {full}; skipping",
              file=sys.stderr)
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
    requires = _get_requires(full)
    if not requires:
        return
    print(f"  {full} requires: {', '.join(requires)}")
    for dep in requires:
        dep_full = paths.normalize(dep)
        if paths.skillset_root(dep_full).exists():
            continue
        print(f"  installing dependency: {dep}")
        rc = _install_one(dep, installing=installing)
        if rc != 0:
            raise SystemExit(
                f"failed to install dependency {dep} required by {full}"
            )


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

    raise SystemExit(
        f"unknown skillset: {name_or_source}\n"
        f"  not in the discovery cache, not a local path, not a git URL.\n"
        f"  run /geno-tools-meta-ecosystem-discover to refresh the cache,\n"
        f"  or install directly: geno-tools install <git-url>"
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
    skill_dirs = _enumerate_skill_dirs(full)
    if not skill_dirs:
        return
    print(f"  installing {len(skill_dirs)} skill(s) via npx skills (all agents, global)")
    for skill_dir in skill_dirs:
        subprocess.check_call([
            "npx", "--yes", "skills", "add", str(skill_dir),
            "--agent", "*", "--global", "--full-depth", "--yes",
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


def _walk_skill_dirs(root: Path) -> list[Path]:
    """Recursively collect every dir under ``root`` that holds a SKILL.md.

    Applies the shadowing rule: once a directory has its own SKILL.md it is a
    skill leaf — we record it and do NOT descend into it (a nested SKILL.md is
    shadowed by the shallower one, matching ``npx skills`` discovery). Dirs
    without a SKILL.md are pure category dirs and are walked through, not
    recorded. Hidden dirs (``.git`` etc.) are skipped. Results are sorted by
    path for deterministic ordering.
    """
    found: list[Path] = []

    def _walk(d: Path) -> None:
        if (d / "SKILL.md").exists():
            found.append(d)
            return  # shadow: don't descend past a skill leaf
        for child in sorted(d.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                _walk(child)

    if root.exists():
        for child in sorted(root.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                _walk(child)
    return found


def _skill_name(skill_dir: Path, fallback: str) -> str:
    """Read the ``name:`` from a skill's SKILL.md frontmatter.

    Falls back to ``fallback`` (usually the dir name) when frontmatter is
    missing or unparseable. Used so nested skills register under their unique
    fully-qualified name rather than a colliding leaf dir name (e.g. two
    ``install/`` dirs under different categories).
    """
    skill_md = skill_dir / "SKILL.md"
    try:
        text = skill_md.read_text()
        if text.startswith("---"):
            fm = text.split("---", 2)[1]
            data = yaml.safe_load(fm) or {}
            name = data.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
    except (OSError, yaml.YAMLError, IndexError):
        pass
    return fallback


def _enumerate_skill_dirs(full: str) -> list[Path]:
    """Return flat list of skill dirs to register.

    Recursively walks ``skills/`` (arbitrary depth) collecting every dir that
    holds a SKILL.md, applying the shadowing rule. Category dirs (no SKILL.md)
    are traversed, not registered. When sub-skills exist, the umbrella root is
    skipped so ``npx skills add --full-depth`` registers the leaves. For
    skillsets with no sub-skills, the root dir is returned.
    """
    active = paths.skillset_active(full)
    sub = _walk_skill_dirs(active / "skills")
    if sub:
        return sub
    if (active / "SKILL.md").exists():
        return [active]
    return []


def _enumerate_skills(full: str) -> list[str]:
    active = paths.skillset_active(full)
    dirs = _enumerate_skill_dirs(full)
    names = [_skill_name(d, full if d == active else d.name) for d in dirs]
    if (active / "SKILL.md").exists() and active not in dirs:
        names.insert(0, full)
    return names


# ── deps ───────────────────────────────────────────────────────────────────

def _deps(args: argparse.Namespace) -> int:
    full = paths.normalize(args.name)
    if not paths.skillset_root(full).exists():
        print(f"not installed: {full}", file=sys.stderr)
        return 1

    _print_dep_tree(full, indent=0, seen=set())
    return 0


def _print_dep_tree(full: str, indent: int, seen: set[str]) -> None:
    prefix = "  " * indent
    installed = paths.skillset_root(full).exists()
    marker = "" if installed else " (missing)"
    print(f"{prefix}{full}{marker}")

    if full in seen:
        if _get_requires(full):
            print(f"{prefix}  (circular, skipped)")
        return
    seen.add(full)

    if not installed:
        return

    for dep in _get_requires(full):
        dep_full = paths.normalize(dep)
        _print_dep_tree(dep_full, indent + 1, seen)


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
    if args.name:
        full = paths.normalize(args.name)
        if not paths.skillset_root(full).exists():
            print(f"not installed: {full}", file=sys.stderr)
            return 1
        results = [_update_one(full)]
    else:
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
        results = [_update_one(full) for full in installed]

    _print_update_summary(results)
    return 1 if any(r.status == "error" for r in results) else 0


@dataclass
class _UpdateResult:
    name: str
    status: str  # "updated" | "up-to-date" | "skipped" | "error"
    detail: str = ""
    old_rev: str = ""
    new_rev: str = ""


def _update_one(full: str) -> _UpdateResult:
    bare = paths.skillset_git(full)
    worktree = paths.skillset_worktree(full, "main")

    if not worktree.exists():
        return _UpdateResult(full, "error", "main worktree missing")

    if worktree.is_symlink():
        return _UpdateResult(full, "skipped", "dev mode (local symlink)")

    try:
        status = subprocess.check_output(
            ["git", "-C", str(worktree), "status", "--porcelain"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        return _UpdateResult(full, "error", "git status failed")

    if status:
        return _UpdateResult(full, "skipped", "dirty worktree")

    default_branch = _detect_default_branch(bare)

    try:
        current_branch = subprocess.check_output(
            ["git", "-C", str(worktree), "branch", "--show-current"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        return _UpdateResult(full, "error", "cannot detect branch")

    if current_branch != default_branch:
        return _UpdateResult(
            full, "skipped",
            f"on branch '{current_branch}', not '{default_branch}'",
        )

    try:
        old_rev = subprocess.check_output(
            ["git", "-C", str(worktree), "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        old_rev = ""

    print(f"  fetching {full}...")
    try:
        subprocess.check_call(
            ["git", "-C", str(bare), "fetch", "--quiet", "origin"],
        )
    except subprocess.CalledProcessError:
        return _UpdateResult(full, "error", "git fetch failed")

    try:
        subprocess.check_call(
            ["git", "-C", str(worktree), "pull", "--ff-only", "--quiet",
             "origin", default_branch],
        )
    except subprocess.CalledProcessError:
        return _UpdateResult(full, "error", "git pull --ff-only failed (diverged?)")

    try:
        new_rev = subprocess.check_output(
            ["git", "-C", str(worktree), "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        new_rev = ""

    if old_rev == new_rev:
        return _UpdateResult(full, "up-to-date", old_rev=old_rev[:8])

    _maybe_reinstall_venv(full, old_rev, new_rev)
    _install_skills_via_npx(full)

    return _UpdateResult(full, "updated", old_rev=old_rev[:8], new_rev=new_rev[:8])


def _maybe_reinstall_venv(full: str, old_rev: str, new_rev: str) -> None:
    worktree = paths.skillset_worktree(full, "main")
    if not (worktree / "pyproject.toml").exists():
        return

    try:
        changed = subprocess.check_output(
            ["git", "-C", str(worktree), "diff", "--name-only",
             old_rev, new_rev],
            text=True,
        )
    except subprocess.CalledProcessError:
        changed = "pyproject.toml"

    if "pyproject.toml" not in changed:
        return

    venv_dir = paths.skillset_venvs(full) / "default"
    if not venv_dir.exists():
        _create_venv_if_needed(full)
        return

    print(f"  pyproject.toml changed; reinstalling venv...")
    pip = venv_dir / "bin" / "pip"
    try:
        subprocess.check_call(
            [str(pip), "install", "--quiet", "-e", str(worktree)]
        )
    except subprocess.CalledProcessError as e:
        print(f"  warn: venv reinstall failed for {full}: {e}",
              file=sys.stderr)


def _print_update_summary(results: list[_UpdateResult]) -> None:
    updated = [r for r in results if r.status == "updated"]
    up_to_date = [r for r in results if r.status == "up-to-date"]
    skipped = [r for r in results if r.status == "skipped"]
    errors = [r for r in results if r.status == "error"]

    print()
    if updated:
        print(f"updated ({len(updated)}):")
        for r in updated:
            print(f"  {r.name:<24} {r.old_rev} -> {r.new_rev}")
    if up_to_date:
        print(f"already up-to-date ({len(up_to_date)}):")
        for r in up_to_date:
            print(f"  {r.name}")
    if skipped:
        print(f"skipped ({len(skipped)}):")
        for r in skipped:
            print(f"  {r.name:<24} {r.detail}")
    if errors:
        print(f"errors ({len(errors)}):")
        for r in errors:
            print(f"  {r.name:<24} {r.detail}")


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


def _scan(args: argparse.Namespace) -> int:
    srcs = discovery.sources()
    if not srcs:
        print("no discovery sources configured (~/.geno/config.yaml: discovery.sources)")
        return 0

    new = discovery.scan(namespace=args.namespace, dry_run=args.dry_run)
    if not new:
        print("no new candidates found")
        return 0

    action = "found" if args.dry_run else "queued"
    print(f"{action} {len(new)} new candidate(s):")
    for c in new:
        print(f"  [{c.source}] {c.name:<32} {c.url}")

    if not args.dry_run:
        print(f"\ncandidates written to {discovery.CANDIDATES_FILE}")
    return 0


def _docs(args: argparse.Namespace) -> int:
    from geno_tools.docs import compile_docs

    docs_dir = Path(args.docs_dir) if args.docs_dir else None
    if docs_dir is None:
        cwd = Path.cwd()
        if (cwd / "docs").is_dir():
            docs_dir = cwd / "docs"
        elif (cwd / "mkdocs.yml").is_file():
            docs_dir = cwd / "docs"
        else:
            print("Error: cannot find docs/ directory. Use --docs-dir.",
                  file=sys.stderr)
            return 1

    extra = [Path(d) for d in (args.extra_dir or [])]
    compile_docs(docs_dir, extra or None, dry_run=args.dry_run)
    return 0


def _todo(msg: str) -> int:
    print(f"[not yet implemented] {msg}", file=sys.stderr)
    return 2
