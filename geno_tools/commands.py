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


# ── terminal formatting (zero-dep, TTY-aware) ────────────────────────────────

def _is_tty() -> bool:
    """Whether stdout is an interactive terminal (checked at call time, not
    import time — pipx wrappers can make import-time checks unreliable).
    Honors NO_COLOR (https://no-color.org)."""
    import os
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _c(code: str, s: str) -> str:
    """Wrap s in an ANSI SGR code, but only when stdout is a TTY."""
    return f"\033[{code}m{s}\033[0m" if _is_tty() else s


def _bold(s): return _c("1", s)
def _dim(s): return _c("2", s)
def _green(s): return _c("32", s)
def _yellow(s): return _c("33", s)
def _red(s): return _c("31", s)
def _cyan(s): return _c("36", s)


def _rule(label: str = "", width: int = 48) -> str:
    """A light horizontal rule, optionally with a label.

    Uses box-drawing on a TTY, ASCII dashes otherwise (pipe/redirect safe).
    """
    dash = "─" if _is_tty() else "-"
    if label:
        head = f"{dash}{dash} {label} "
        return _dim(head + dash * max(0, width - len(head)))
    return _dim(dash * width)


# State glyph (TTY) + ASCII fallback + color, for drift vs remote.
_STATE_FMT = {
    "in-sync":  ("●", "ok",  _green),
    "ahead":    ("▲", "ahead", _cyan),
    "dirty":    ("✎", "dirty", _yellow),
    "diverged": ("✗", "diverged", _red),
    "offline":  ("·", "offline", _dim),
}


def _fmt_state(state: str) -> str:
    if state.startswith("behind"):
        glyph = "▼" if _is_tty() else "<"
        return _yellow(f"{glyph} {state}")
    glyph, ascii_label, color = _STATE_FMT.get(state, ("", state, _dim))
    g = (glyph + " ") if (_is_tty() and glyph) else ""
    label = state if _is_tty() else ascii_label
    return color(f"{g}{label}")


def dispatch(args: argparse.Namespace) -> int:
    handlers = {
        "ls": _status,            # alias for status (back-compat)
        "status": _status,
        "install": _install,
        "dev": _dev,
        "fork": _fork,
        "use": _use,
        "promote": _promote,
        "update": _self_update,   # update geno-tools itself
        "upgrade": _upgrade,      # upgrade installed skillset(s) — was `update`
        "remove": _remove,
        "deps": _deps,
        "doctor": _doctor,
        "discover": _discover,
        "scan": _scan,
        "docs": _docs,
        "audit": _audit,
        "config": _config_show if getattr(args, "config_cmd", None) == "show"
                  else _config_set,
        "llm": _llm,
        "workspace": _workspace,
        "install-agent": _install_agent,
    }
    return handlers[args.cmd](args)


def _audit(args: argparse.Namespace) -> int:
    """`geno-tools audit [path]` — check a repo against ecosystem conventions."""
    from pathlib import Path

    from geno_tools import audit as auditmod

    target = getattr(args, "path", None) or "."
    results = auditmod.audit(target)
    root = Path(target).resolve()
    order = {"FAIL": 0, "WARN": 1, "INFO": 2, "OK": 3}
    results.sort(key=lambda r: order.get(r[0], 9))
    tag = {"FAIL": _red("FAIL"), "WARN": _yellow("WARN"),
           "INFO": _dim("INFO"), "OK": _green(" OK ")}
    print(_bold(f"audit · {root.name}") + _dim(f"  ({root})"))
    for level, check, detail in results:
        print(f"  [{tag[level]}] {check}" + (_dim(f"  {detail}") if detail else ""))
    fails = sum(1 for r in results if r[0] == "FAIL")
    warns = sum(1 for r in results if r[0] == "WARN")
    print(_rule())
    if fails:
        print(f"  {_red(f'{fails} FAIL')}"
              + (_yellow(f" · {warns} WARN") if warns else "")
              + _dim("  — required checks must pass to be installable"))
    else:
        print(f"  {_green('compliant')}" + (_yellow(f" · {warns} WARN") if warns else ""))
    return 1 if fails else 0


# ── status / available ──────────────────────────────────────────────────────

def _installed_skillsets() -> list[str]:
    if not paths.ROOT.exists():
        return []
    return sorted(
        p.name for p in paths.ROOT.iterdir()
        if p.is_dir() and p.name.startswith("geno-")
        and p.name not in ("geno-bootstrap",)
    )


def _status(args: argparse.Namespace) -> int:
    """`geno-tools status` — installed skillsets, versions, drift vs remote.

    Back-compat: `geno-tools ls --available` still routes to the registry list.
    """
    if getattr(args, "available", False):
        return _available(args)

    installed = _installed_skillsets()
    print(_bold("geno-tools"))
    if not installed:
        print(_rule("installed"))
        print(_dim("  no skillsets installed."))
        print(_dim("  geno-tools discover   # see what you can install"))
        return 0

    print(_rule(f"installed · {len(installed)}"))
    rows = [_skillset_status(full, check_remote=True) for full in installed]
    name_w = max(len(r["name"]) for r in rows)
    ver_w = max(len(r["version"]) for r in rows)
    for r in rows:
        ref = _dim(f"{r['variant']}@{r['commit']}")
        line = (f"  {_bold(r['name'].ljust(name_w))}  "
                f"{r['version'].ljust(ver_w)}  {ref}")
        if r["state"]:
            line += f"  {_fmt_state(r['state'])}"
        print(line)
    behind = [r for r in rows if r["state"].startswith("behind")]
    if behind:
        print()
        print(_dim(f"  {len(behind)} behind remote — geno-tools upgrade"))
    return 0


def _available(args: argparse.Namespace) -> int:
    """Deprecated alias for `discover` (prints the grouped discoverable list)."""
    return _discover(args)


# Category print order: known geno-ecosystem buckets first, then any extras,
# then Uncategorized last.
_CATEGORY_ORDER = [
    "Core Framework", "Developer Tools", "Workspaces & Data",
    "Modalities & Capabilities", "Applied Research", "Interfaces & Comms",
]


def _discover(args: argparse.Namespace) -> int:
    """`geno-tools discover` — find & list installable skillsets, by category.

    Prints the cached list (instant); auto-refreshes via curl when the cache is
    missing or stale (>30 min), or when --refresh is passed.
    """
    refresh = getattr(args, "refresh", False)
    if refresh or registry.is_stale():
        why = "forced" if refresh else ("missing" if registry.cache_age_seconds() is None else "stale")
        print(_dim(f"  refreshing discovery cache ({why})…"))
        try:
            registry.discover_now()
        except Exception as e:
            print(_dim(f"  refresh failed ({e}); showing cached results"))

    entries = registry.read_full()
    print(_bold("geno-tools"))
    if not entries:
        print(_rule("discover"))
        print(_dim("  no skillsets found (no network, empty cache)."))
        print(_dim("  retry:  geno-tools discover --refresh"))
        print(_dim("  or install directly:  geno-tools install <git-url>"))
        return 0

    installed = set(_installed_skillsets())
    by_cat: dict[str, list[str]] = {}
    for name in entries:
        by_cat.setdefault(entries[name].get("category", "Uncategorized"), []).append(name)
    order = ([c for c in _CATEGORY_ORDER if c in by_cat]
             + sorted(c for c in by_cat if c not in _CATEGORY_ORDER and c != "Uncategorized")
             + (["Uncategorized"] if "Uncategorized" in by_cat else []))

    print(_rule(f"discover · {len(entries)}"))
    name_w = max(len(n) for n in entries)
    for cat in order:
        print(_cyan(f"  {cat}"))
        for name in sorted(by_cat[cat]):
            mark = _green("✓ installed") if name in installed else _dim(entries[name]["url"])
            print(f"    {_bold(name.ljust(name_w))}  {mark}")
    return 0


def _skillset_status(full: str, *, check_remote: bool) -> dict:
    """version + active variant + short commit + (optionally) remote drift.

    state (with check_remote): in-sync, behind <sha>, ahead, diverged, dirty,
    or offline. Empty without check_remote.
    """
    active = paths.skillset_active(full)
    variant = active.readlink().name if active.is_symlink() else "?"
    worktree = paths.skillset_worktree(full, variant)
    version = str(_read_manifest(full).get("version", "?"))

    def _git(*a) -> str:
        try:
            return subprocess.check_output(
                ["git", "-C", str(worktree), *a],
                text=True, stderr=subprocess.DEVNULL,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""

    commit = _git("rev-parse", "--short", "HEAD") or "?"
    state = ""

    # `active -> <variant>` is always a symlink; dev mode is when the *worktree*
    # itself is a symlink to a local checkout — only then skip the remote check.
    if check_remote and not worktree.is_symlink():
        if _git("status", "--porcelain"):
            state = "dirty"
        else:
            branch = _git("branch", "--show-current") or "main"
            try:
                out = subprocess.check_output(
                    ["git", "-C", str(worktree), "ls-remote", "origin",
                     f"refs/heads/{branch}"],
                    text=True, stderr=subprocess.DEVNULL, timeout=10,
                ).strip()
                remote = out.split()[0] if out else ""
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                remote = ""
                state = "offline"
            if remote:
                local = _git("rev-parse", "HEAD")

                def _ancestor(a: str, b: str) -> bool:
                    return subprocess.call(
                        ["git", "-C", str(worktree), "merge-base",
                         "--is-ancestor", a, b],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

                if remote == local:
                    state = "in-sync"
                elif _ancestor(local, remote):
                    state = f"behind {remote[:7]}"
                elif _ancestor(remote, local):
                    state = "ahead"
                else:
                    state = "diverged"

    return {"name": full, "version": version, "variant": variant,
            "commit": commit, "state": state}


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


REPO_URL = "https://github.com/42euge/geno-tools.git"
_CC_MARKETPLACE = Path.home() / ".claude" / "plugins" / "marketplaces" / "geno-tools"


def _self_update(args: argparse.Namespace) -> int:
    """`geno-tools update` — update geno-tools itself to the latest version.

    Does the disk-level half a subprocess can do:
      1. reinstall the `geno-tools` CLI from the latest published source (pipx);
      2. refresh the Claude Code marketplace clone, if present.
    The final plugin reload must happen inside the agent — we print that step,
    since a CLI can't issue Claude Code's `/reload-plugins` slash command.
    """
    print(_bold("geno-tools update"))
    print(_rule("self-update"))
    ok = True

    # 1. CLI binary → latest from GitHub (pipx preferred; never pip --user/PEP668)
    pipx = shutil.which("pipx") or _find_pipx()
    if pipx:
        print(_dim(f"  reinstalling CLI via pipx from {REPO_URL} …"))
        rc = subprocess.call([pipx, "install", "--force", f"git+{REPO_URL}"])
        if rc == 0:
            print(_green("  ✓ CLI updated"))
        else:
            ok = False
            print(_red("  ✗ pipx install failed — run /geno-tools-setup"))
    else:
        ok = False
        print(_yellow("  ! pipx not found — run /geno-tools-setup to install the CLI"))

    # 2. Refresh the Claude Code marketplace clone (so /plugin install gets latest)
    if (_CC_MARKETPLACE / ".git").exists():
        print(_dim("  refreshing Claude Code marketplace clone …"))
        rc = subprocess.call(
            ["git", "-C", str(_CC_MARKETPLACE), "pull", "--quiet", "--ff-only"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(_green("  ✓ marketplace refreshed") if rc == 0
              else _yellow("  ! marketplace refresh skipped (diverged?)"))

    # 3. The one step a subprocess can't do — tell the user.
    print()
    print(_dim("  to load the new plugin in Claude Code, run:"))
    print("    /plugin install geno-tools@geno-tools")
    print("    /reload-plugins")
    print(_dim("  (Codex/Antigravity: re-run the plugin install for your agent)"))
    return 0 if ok else 1


def _find_pipx() -> str | None:
    """Locate pipx even when it's off a non-interactive PATH (macOS Python bin)."""
    for p in [Path.home() / ".local" / "bin" / "pipx",
              *Path.home().glob("Library/Python/*/bin/pipx")]:
        if p.exists():
            return str(p)
    return None


def _upgrade(args: argparse.Namespace) -> int:
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


# ── config subcommand ─────────────────────────────────────────────────────────

def _config_show(args: argparse.Namespace) -> int:
    """`geno-tools config show` — print current config, redacting secrets."""
    import json as _json
    from geno_tools import config as cfg
    data = cfg.load()
    # Redact token
    if "llm" in data:
        data = {**data, "llm": {**data["llm"], "token": "***" if cfg.get_llm().get("token") else ""}}
    print(yaml.safe_dump(data, sort_keys=False).rstrip())
    settings = cfg._SETTINGS_FILE
    if settings.exists():
        print(f"\n# token set in {settings}: yes")
    else:
        print(f"\n# token not yet set — run: geno-tools config set llm.token <token>")
    return 0


def _config_set(args: argparse.Namespace) -> int:
    """`geno-tools config set <key> <value>` — set a config value."""
    from geno_tools import config as cfg
    cfg.set_config(args.key, args.value)
    dest = "~/.geno/settings.json" if args.key in ("llm.token",) else "~/.geno/config.yaml"
    if _is_tty():
        print(f"set {args.key} in {dest}")
    return 0


# ── llm subcommand ────────────────────────────────────────────────────────────

def _llm(args: argparse.Namespace) -> int:
    """`geno-tools llm <sub>` dispatcher."""
    sub = getattr(args, "llm_cmd", None) or "probe"
    if sub == "probe":
        return _llm_probe(args)
    if sub == "suggest":
        return _llm_suggest(args)
    print(f"Unknown llm subcommand '{sub}'. Use: probe, suggest", file=sys.stderr)
    return 1


def _llm_probe(args: argparse.Namespace) -> int:
    """`geno-tools llm probe` — discover models on the LiteLLM endpoint and benchmark them."""
    from geno_tools import config as cfg, llm as gllm
    lc = cfg.get_llm()
    endpoint = lc.get("endpoint", "").strip()
    token = lc.get("token", "")
    timeout = int(lc.get("timeout", 10))

    if not endpoint:
        print("No LLM endpoint configured. Run:\n  geno-tools config set llm.endpoint <url>",
              file=sys.stderr)
        return 1

    bold = _bold if _is_tty() else lambda s: s
    dim = _dim if _is_tty() else lambda s: s
    green = _green if _is_tty() else lambda s: s
    red = _red if _is_tty() else lambda s: s

    print(f"Discovering models at {endpoint} …")
    try:
        models = gllm.discover_models(endpoint, token, timeout)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"Found {len(models)} model(s). Probing (this may take a moment)…\n")

    results = gllm.probe_all(endpoint, token, concurrency=8, timeout=timeout)

    # Print ranked table
    w = max((len(r["model"]) for r in results), default=10)
    print(f"{'#':<3}  {'MODEL':<{w}}  {'TTFT':>7}  {'TOTAL':>7}  STATUS")
    print("-" * (w + 28))
    for i, r in enumerate(results, 1):
        status = green("ok") if r["ok"] else red(r["error"][:40])
        ttft = f"{r['ttft_ms']}ms" if r["ok"] else "—"
        total = f"{r['total_ms']}ms" if r["ok"] else "—"
        print(f"{i:<3}  {r['model']:<{w}}  {ttft:>7}  {total:>7}  {status}")

    # Persist rankings to config.yaml
    ok_results = [r for r in results if r["ok"]]
    rankings = [{"model": r["model"], "ttft_ms": r["ttft_ms"]} for r in ok_results]
    cfg.set_config("llm.model_rankings", rankings)  # type: ignore[arg-type]

    # Persist top model if none configured
    if not lc.get("model") and ok_results:
        top = ok_results[0]["model"]
        cfg.set_config("llm.model", top)
        print(f"\n{bold('Top model saved')}: {top}")

    print(f"\nRankings written to ~/.geno/config.yaml")
    return 0


def _llm_suggest(args: argparse.Namespace) -> int:
    """`geno-tools llm suggest --cwd ... --job ... --title ...`
    Print a suggested dot-notation tab name to stdout."""
    from geno_tools import config as cfg, llm as gllm
    lc = cfg.get_llm()
    endpoint = lc.get("endpoint", "").strip()
    token = lc.get("token", "")
    timeout = int(lc.get("timeout", 10))

    # Pick model: explicit flag > configured > top ranking
    model = getattr(args, "model", None) or lc.get("model", "")
    if not model:
        rankings = lc.get("model_rankings") or []
        if rankings:
            model = rankings[0].get("model", "")
    if not model:
        print("", end="")  # no suggestion — caller falls back to manual input
        return 0
    if not endpoint:
        print("", end="")
        return 0

    name = gllm.suggest_name(
        endpoint, token, model,
        cwd=getattr(args, "cwd", "") or "",
        job=getattr(args, "job", "") or "",
        title=getattr(args, "title", "") or "",
        timeout=timeout,
    )
    print(name, end="")
    return 0


# ---------------------------------------------------------------------------
# VS Code workspace management
# ---------------------------------------------------------------------------

def _workspace(args: argparse.Namespace) -> int:
    """`geno-tools workspace <sub>` — find, open, and create .code-workspace files."""
    sub = getattr(args, "ws_cmd", None) or "ls"
    if sub == "ls":
        return _workspace_ls(args)
    if sub == "open":
        return _workspace_open(args)
    if sub == "create":
        return _workspace_create(args)
    print(f"Unknown workspace subcommand '{sub}'. Use: ls, open, create", file=sys.stderr)
    return 1


def _find_workspaces(root: Path | None = None) -> list[Path]:
    """Recursively find all *.code-workspace files under root (default ~/code)."""
    import glob
    search_root = root or (Path.home() / "code")
    if not search_root.exists():
        return []
    return sorted(Path(p) for p in glob.glob(
        str(search_root / "**" / "*.code-workspace"), recursive=True
    ))


def _workspace_ls(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser() if getattr(args, "root", None) else None
    workspaces = _find_workspaces(root)
    if not workspaces:
        print("No .code-workspace files found.")
        return 0
    bold = _bold if _is_tty() else lambda s: s
    dim = _dim if _is_tty() else lambda s: s
    home = Path.home()
    for i, ws in enumerate(workspaces, 1):
        try:
            display = "~/" + str(ws.relative_to(home))
        except ValueError:
            display = str(ws)
        print(f"  {i:<3} {bold(ws.stem):<40} {dim(display)}")
    print(f"\n{len(workspaces)} workspace(s). Open with: geno-tools workspace open <name|index>")
    return 0


def _workspace_open(args: argparse.Namespace) -> int:
    import shutil, subprocess as _sp
    target = getattr(args, "target", None)
    if not target:
        print("Usage: geno-tools workspace open <name|path|index>", file=sys.stderr)
        return 1

    root = Path(getattr(args, "root", None) or "").expanduser() or None
    workspaces = _find_workspaces(root)

    # Resolve: exact path, then index, then name match
    ws_path: Path | None = None
    p = Path(target).expanduser()
    if p.suffix == ".code-workspace" and p.exists():
        ws_path = p
    elif target.isdigit():
        idx = int(target) - 1
        if 0 <= idx < len(workspaces):
            ws_path = workspaces[idx]
    else:
        matches = [w for w in workspaces
                   if w.stem.lower() == target.lower()
                   or target.lower() in w.stem.lower()]
        if len(matches) == 1:
            ws_path = matches[0]
        elif len(matches) > 1:
            print(f"Ambiguous: {len(matches)} workspaces match '{target}':")
            for m in matches:
                print(f"  {m}")
            return 1

    if not ws_path:
        print(f"No workspace found matching '{target}'. Run: geno-tools workspace ls",
              file=sys.stderr)
        return 1

    code_bin = shutil.which("code") or shutil.which("code-insiders")
    if not code_bin:
        print("'code' not found on PATH. Install VS Code and run: Shell Command: Install 'code' command in PATH",
              file=sys.stderr)
        return 1

    print(f"Opening {ws_path.name} …")
    _sp.Popen([code_bin, str(ws_path)])
    return 0


def _workspace_create(args: argparse.Namespace) -> int:
    import json as _json
    name = getattr(args, "name", None)
    paths_arg = getattr(args, "paths", None) or []
    if not name:
        print("Usage: geno-tools workspace create <name> [path ...]", file=sys.stderr)
        return 1

    out_dir = Path(getattr(args, "output", None) or ".").expanduser()
    out_path = out_dir / f"{name}.code-workspace"

    folders = [{"path": str(Path(p).expanduser())} for p in paths_arg] if paths_arg else []
    workspace = {"folders": folders, "settings": {}}
    out_path.write_text(_json.dumps(workspace, indent=2) + "\n")
    print(f"Created {out_path}")
    if not paths_arg:
        print("  Tip: add folders with VS Code's 'Add Folder to Workspace…' or edit the JSON directly.")
    return 0


# ── install-agent ────────────────────────────────────────────────────────────

_AGENT_TARGETS = {
    "claude-code":  ("~/.claude",              "plugin.json"),
    "codex":        ("~/.codex",               "plugin.json"),
    "antigravity":  ("~/.antigravity",         "plugin.json"),
}


def _install_agent(args: argparse.Namespace) -> int:
    """`geno-tools install-agent <agent> [-m manifest] [--dry-run] [--list]`

    Writes a skill manifest into a coding agent's config directory so the agent
    discovers all installed geno-* skillsets.
    """
    import json as _json

    if getattr(args, "list_agents", False):
        print(f"{'AGENT':<16}  CONFIG DIR")
        print(f"{'-----':<16}  ----------")
        for name, (cfg, _) in sorted(_AGENT_TARGETS.items()):
            resolved = str(Path(cfg).expanduser())
            exists = " ✓" if Path(resolved).exists() else ""
            print(f"{name:<16}  {resolved}{exists}")
        return 0

    agent = getattr(args, "agent", None)
    if not agent:
        print("Usage: geno-tools install-agent <agent> [options]", file=sys.stderr)
        print("       geno-tools install-agent --list", file=sys.stderr)
        return 1

    if agent not in _AGENT_TARGETS:
        print(f"Unknown agent {agent!r}. Known: {', '.join(sorted(_AGENT_TARGETS))}", file=sys.stderr)
        return 1

    cfg_dir_raw, plugin_file = _AGENT_TARGETS[agent]
    cfg_dir = Path(cfg_dir_raw).expanduser()
    dest = cfg_dir / plugin_file

    manifest_path = getattr(args, "manifest", None)
    if manifest_path:
        manifest = _json.loads(Path(manifest_path).read_text())
    else:
        skill_dirs = []
        if paths.ROOT.exists():
            for entry in sorted(paths.ROOT.iterdir()):
                if not entry.is_dir():
                    continue
                active_skills = entry / "active" / "skills"
                if active_skills.exists():
                    skill_dirs.append(str(active_skills))
        manifest = {
            "name": "geno",
            "version": "0.1.0",
            "description": "Geno ecosystem — agentic workspace orchestration",
            "repository": "https://github.com/42euge/geno-tools",
            "skills": skill_dirs,
        }

    out = _json.dumps(manifest, indent=2) + "\n"
    print(f"agent:    {agent}")
    print(f"config:   {cfg_dir}")
    print(f"manifest: {dest}")
    print(f"skills:   {len(manifest.get('skills', []))} entries")

    if getattr(args, "dry_run", False):
        print("\n[dry-run] would write:")
        print(out)
        return 0

    cfg_dir.mkdir(parents=True, exist_ok=True)
    dest.write_text(out)
    print(f"\n✓ installed geno skills into {dest}")
    return 0
