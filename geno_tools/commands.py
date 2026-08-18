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
    if args.cmd == "skills":
        from geno_tools.skills import dispatch as dispatch_skills
        return dispatch_skills(args)

    handlers = {
        "status": _status,
        "update": _self_update,   # update geno-tools itself
        "config": _config_show if getattr(args, "config_cmd", None) == "show"
                  else _config_set,
    }
    return handlers[args.cmd](args)


# ── status / available ──────────────────────────────────────────────────────

def _installed_skillsets() -> list[str]:
    if not paths.ROOT.exists():
        return []
    return sorted(
        p.name for p in paths.ROOT.iterdir()
        if p.is_dir() and p.name.startswith("geno-")
        and p.name not in ("geno-bootstrap",)
    )


def _status(_: argparse.Namespace) -> int:
    """`geno-tools status` — installed skillsets, versions, drift vs remote."""
    installed = _installed_skillsets()
    print(_bold("geno-tools"))
    if not installed:
        print(_rule("installed"))
        print(_dim("  no skillsets installed."))
        print(_dim("  geno-tools skills discover   # see what you can install"))
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
        print(_dim(f"  {len(behind)} behind remote — geno-tools skills upgrade"))
    return 0


# Category print order: known geno-ecosystem buckets first, then any extras,
# then Uncategorized last.
_CATEGORY_ORDER = [
    "Core Framework", "Developer Tools", "Workspaces & Data",
    "Modalities & Capabilities", "Applied Research", "Interfaces & Comms",
]


def _discover(args: argparse.Namespace) -> int:
    """`geno-tools skills discover` — list installable skillsets by category.

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
        print(_dim("  retry:  geno-tools skills discover --refresh"))
        print(_dim("  or install directly:  geno-tools skills install <git-url>"))
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
    """Version, short commit, and optionally remote drift.

    state (with check_remote): in-sync, behind <sha>, ahead, diverged, dirty,
    or offline. Empty without check_remote.
    """
    worktree = paths.skillset_worktree(full)
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

    if check_remote:
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

    return {"name": full, "version": version, "variant": "main",
            "commit": commit, "state": state}


# ── manifest ───────────────────────────────────────────────────────────────

def _read_manifest(full: str) -> dict:
    worktree = paths.skillset_worktree(full)
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
        f"  or install directly: geno-tools skills install <git-url>"
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
        str(paths.skillset_worktree(full)), default_branch,
    ])


def _detect_default_branch(bare_repo: Path) -> str:
    out = subprocess.check_output(
        ["git", "-C", str(bare_repo), "symbolic-ref", "--short", "HEAD"],
        text=True,
    ).strip()
    return out or "main"


# ── venv ────────────────────────────────────────────────────────────────────

def _create_venv_if_needed(full: str) -> dict[str, str]:
    worktree = paths.skillset_worktree(full)
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

def _install_skills_via_npx(full: str, agent: str = "*") -> None:
    """Register a skillset's skills with `npx skills` in ONE call.

    `npx skills add <dir> --full-depth` already walks the whole skills tree and
    discovers every leaf (applying its own shadowing rule), so we hand it the
    skillset root once instead of looping per leaf — a single banner, a single
    summary, and any per-agent failures reported once instead of N times.
    """
    skill_dirs = _enumerate_skill_dirs(full)
    if not skill_dirs:
        return
    # Point npx at the skills/ tree root (or the umbrella root for flat
    # skillsets) and let --full-depth find the leaves in one pass.
    active = paths.skillset_active(full)
    root = active / "skills" if (active / "skills").is_dir() else active

    # Scope --agent to the agents actually on this machine. Passing "*" makes
    # npx try all ~76 agents it knows and emit a failure line for each one that
    # can't do global installs (Eve, PromptScript, …). Fall back to "*" if we
    # detect nothing, so an unfamiliar setup still gets registered.
    if agent == "*":
        from geno_tools import agents
        detected = agents.detect_installed()
        agents = detected or ["*"]
    else:
        agents = [agent]

    scope = "all agents" if agents == ["*"] else ", ".join(agents)
    print(f"  registering {len(skill_dirs)} skill(s) via npx skills "
          f"({scope}, global) — one pass over {root}")
    subprocess.check_call([
        "npx", "--yes", "skills", "add", str(root),
        "--agent", *agents, "--global", "--full-depth", "--yes",
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


# ── uninstall (inverse of install) ────────────────────────────────────────────

# Agent skills dirs npx registers into.
_AGENT_SKILL_DIRS = [
    Path.home() / ".claude" / "skills",
    Path.home() / ".agents" / "skills",
    Path.home() / ".codex" / "skills",
    Path.home() / ".cursor" / "skills",
    Path.home() / ".gemini" / "skills",
    Path.home() / ".gemini" / "antigravity" / "skills",
    Path.home() / ".copilot" / "skills",
]

_CC_PLUGIN_DIRS = [
    Path.home() / ".claude" / "plugins" / "cache" / "geno-tools",
    Path.home() / ".claude" / "plugins" / "data" / "geno-tools-geno-tools",
    Path.home() / ".claude" / "plugins" / "data" / "geno-tools-skills-dir",
    _CC_MARKETPLACE,
]


def _uninstall(args: argparse.Namespace) -> int:
    """`geno-tools skills uninstall` — the faithful inverse of install.

    Removes installed skillsets, venvs, bin symlinks, agent skill
    registrations, and Claude Code plugin/marketplace clones. State and user
    data under ~/.geno are kept and reported.

    The pipx/brew package removal is the one step a running process can't do to
    itself cleanly, so we print the exact command instead of self-deleting.
    """
    # ── plan: enumerate everything, delete nothing yet ──
    skillsets = _installed_skillsets() if paths.ROOT.exists() else []

    agent_skills: list[Path] = []
    for d in _AGENT_SKILL_DIRS:
        if not d.exists():
            continue
        for entry in sorted(d.iterdir()):
            if entry.name.startswith(("geno-", "geno-tools", "geno-iso")):
                agent_skills.append(entry)

    bin_links: list[Path] = []
    if SYSTEM_BIN.exists():
        managed_prefix = str(paths.ROOT)
        for entry in SYSTEM_BIN.iterdir():
            if not entry.is_symlink():
                continue
            try:
                target = (entry.parent / entry.readlink()).resolve()
            except OSError:
                continue
            if str(target).startswith(managed_prefix):
                bin_links.append(entry)

    plugin_dirs = [d for d in _CC_PLUGIN_DIRS if d.exists()]

    # Everything under ~/.geno is retained.
    kept_user_data: list[Path] = []
    if paths.GENO_DIR.exists():
        for entry in sorted(paths.GENO_DIR.iterdir()):
            if not entry.name.startswith("."):
                kept_user_data.append(entry)

    # ── report ──
    print(_bold("geno-tools skills uninstall"))
    print(_rule("plan"))

    def _section(title, items, render=lambda p: str(p)):
        print(_bold(f"  {title} ({len(items)})"))
        for it in items:
            print(f"    {_red('remove')}  {render(it)}")
        if not items:
            print(_dim("    (none)"))

    _section(f"skillsets under {paths.ROOT}", skillsets,
             lambda n: f"{paths.ROOT}/{n}")
    _section("agent skill registrations", agent_skills)
    _section("bin symlinks", bin_links)
    _section("Claude Code plugin/marketplace clones", plugin_dirs)
    print()
    print(_bold(f"  {_green('KEPT')} — your data, never touched:"))
    if kept_user_data:
        for it in kept_user_data:
            print(f"    keep    {it}")
    else:
        print(_dim("    (no user data found in ~/.geno)"))

    total = (len(skillsets) + len(agent_skills) + len(bin_links)
             + len(plugin_dirs))
    print()
    if total == 0:
        print(_green("nothing to remove — geno-tools is not installed here."))
        # still print the package-removal hint below

    if args.dry_run:
        print(_dim("dry-run — nothing was deleted."))
        _print_pkg_removal_hint()
        return 0

    if total > 0 and not args.yes:
        try:
            resp = input(f"remove {total} item(s)? [y/N] ").strip().lower()
        except EOFError:
            resp = ""
        if resp not in ("y", "yes"):
            print("aborted.")
            return 1

    # ── execute ──
    for name in skillsets:
        _uninstall_skills_via_npx(name)
        _remove_bin_symlinks(name)
        shutil.rmtree(paths.skillset_root(name), ignore_errors=True)
        print(f"  removed skillset {name}")
    for s in agent_skills:
        shutil.rmtree(s, ignore_errors=True) if s.is_dir() and not s.is_symlink() else s.unlink(missing_ok=True)
        print(f"  removed {s}")
    for b in bin_links:
        b.unlink(missing_ok=True)
        print(f"  removed {b}")
    for d in plugin_dirs:
        shutil.rmtree(d, ignore_errors=True)
        print(f"  removed {d}")
    # if ~/.geno-tools is now empty, remove it
    if paths.ROOT.exists() and not any(paths.ROOT.iterdir()):
        shutil.rmtree(paths.ROOT, ignore_errors=True)
        print(f"  removed empty {paths.ROOT}")

    # clean geno-tools entries from Claude JSON configs
    _clean_agent_json_configs()

    print(_green("\nuninstalled geno-tools' on-disk footprint."))
    _print_pkg_removal_hint()
    return 0


def _print_pkg_removal_hint() -> None:
    """The package itself must be removed by the package manager, not by a
    process removing its own interpreter mid-run."""
    print()
    print(_bold("last step — remove the CLI package (a process can't delete itself):"))
    print("  pipx uninstall geno-tools        # if installed via pipx")
    print(_dim("  # or, if installed via Homebrew:"))
    print("  brew uninstall 42euge/geno/geno  # NOTE: may cascade shared deps; check `brew uses`")


def _clean_agent_json_configs() -> None:
    """Remove geno-tools plugin/marketplace entries from agent JSON configs.

    Edits settings.json / .claude.json in place, preserving all other keys and
    any historical usage records.
    """
    import json as _json
    targets = [
        home / ".claude" / "settings.json"
        for home in [Path.home()]
    ] + [Path.home() / ".claude.json"]
    for p in targets:
        if not p.exists():
            continue
        try:
            data = _json.loads(p.read_text())
        except Exception:  # noqa: BLE001
            continue
        changed = False
        for key in ("enabledPlugins", "extraKnownMarketplaces", "installedPlugins"):
            v = data.get(key)
            if isinstance(v, dict):
                for k in [k for k in v if "geno-tools" in k or "geno-iso" in k]:
                    del v[k]
                    changed = True
        if changed:
            p.write_text(_json.dumps(data, indent=2) + "\n")
            print(f"  cleaned geno entries from {p}")


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
    worktree = paths.skillset_worktree(full)

    if not worktree.exists():
        return _UpdateResult(full, "error", "main worktree missing")

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
    worktree = paths.skillset_worktree(full)
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


# ── config subcommand ─────────────────────────────────────────────────────────

def _config_show(args: argparse.Namespace) -> int:
    """`geno-tools config show` — print current config, redacting secrets."""
    from geno_tools import config as cfg
    print(yaml.safe_dump(cfg.load(), sort_keys=False).rstrip())
    return 0


def _config_set(args: argparse.Namespace) -> int:
    """`geno-tools config set <key> <value>` — set a config value."""
    from geno_tools import config as cfg
    cfg.set_config(args.key, args.value)
    if _is_tty():
        print(f"set {args.key} in ~/.geno/config.yaml")
    return 0
