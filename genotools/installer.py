"""Install / dev / remove / update / doctor orchestration."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from genotools import linkdb, manifest as manifest_mod, registry, targets
from genotools.linkdb import SkillsetEntry
from genotools.paths import (
    skillset_configs,
    skillset_repo,
    skillset_root,
    skillset_scripts,
    skillset_venvs,
)


# ── Public API ──────────────────────────────────────────────────────────────

def install(
    *,
    name_or_source: str,
    agents: list[str],
    copy: bool = False,
    project: bool = False,
) -> int:
    source, resolved_name = _resolve_source(name_or_source)

    # If we don't know the name yet (git URL / local path), clone into a temp
    # location, read manifest, then move into place under the right name.
    if resolved_name is None:
        tmp_repo = skillset_root("__staging__") / "repo"
        _wipe(tmp_repo.parent)
        _fetch(source, tmp_repo)
        m = manifest_mod.load(tmp_repo)
        resolved_name = m.name
        target_root = skillset_root(resolved_name)
        if target_root.exists():
            _wipe(tmp_repo.parent)
            print(f"geno-{resolved_name} already installed; use `update` or `remove` first",
                  file=sys.stderr)
            return 1
        target_root.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tmp_repo), str(skillset_repo(resolved_name)))
        _wipe(tmp_repo.parent)  # tmp __staging__ root
    else:
        target_root = skillset_root(resolved_name)
        if target_root.exists():
            print(f"geno-{resolved_name} already installed; use `update` or `remove` first",
                  file=sys.stderr)
            return 1
        target_root.mkdir(parents=True, exist_ok=True)
        _fetch(source, skillset_repo(resolved_name))

    return _finish_install(
        name=resolved_name,
        source=source,
        mode="git",
        agents=agents,
        copy=copy,
        project=project,
    )


def dev_link(*, name: str, local_path: str, agents: list[str]) -> int:
    src = Path(local_path).expanduser().resolve()
    if not src.is_dir():
        print(f"not a directory: {src}", file=sys.stderr)
        return 1
    if not (src / "genotools.yaml").exists():
        print(f"missing genotools.yaml in {src}", file=sys.stderr)
        return 1

    # If installed, blow away the existing install (it'll be replayed as dev).
    if skillset_root(name).exists():
        remove(name=name, keep_data=True)

    target_root = skillset_root(name)
    target_root.mkdir(parents=True, exist_ok=True)
    skillset_repo(name).symlink_to(src)

    return _finish_install(
        name=name,
        source=str(src),
        mode="dev",
        agents=agents,
        copy=False,
        project=False,
    )


def remove(*, name: str, keep_data: bool = False) -> int:
    db = linkdb.load()
    entry = db.get(name)
    if entry is None:
        print(f"geno-{name} not installed", file=sys.stderr)
        return 1

    for path_str in reversed(entry.links):
        p = Path(path_str)
        if not (p.is_symlink() or p.exists()):
            continue
        try:
            if p.is_dir() and not p.is_symlink():
                # Only remove if empty — protects user-added content.
                try:
                    p.rmdir()
                except OSError:
                    pass
            else:
                p.unlink()
        except OSError as exc:
            print(f"  warn: could not remove {p}: {exc}", file=sys.stderr)

    if keep_data:
        # Preserve configs/ and venvs/; drop repo/ and scripts/ only.
        _wipe(skillset_repo(name))
        _wipe(skillset_scripts(name))
    else:
        _wipe(skillset_root(name))

    db.drop(name)
    linkdb.save(db)
    print(f"removed geno-{name}")
    return 0


def update(*, name: str | None) -> int:
    db = linkdb.load()
    names = [name] if name else [e.name for e in db.skillsets()]
    if name and name not in db.entries:
        print(f"geno-{name} not installed", file=sys.stderr)
        return 1

    rc = 0
    for n in names:
        entry = db.entries[n]
        if entry.mode == "dev":
            print(f"geno-{n}: dev mode, source is live ({entry.source})")
            continue
        repo = skillset_repo(n)
        print(f"geno-{n}: pulling…")
        r = subprocess.run(["git", "-C", str(repo), "pull", "--ff-only"])
        if r.returncode != 0:
            rc = r.returncode
    return rc


def doctor() -> int:
    db = linkdb.load()
    if not db.entries:
        print("no skillsets installed")
        return 0
    bad = 0
    for entry in db.skillsets():
        print(f"geno-{entry.name} ({entry.mode}) → {entry.source}")
        repo = skillset_repo(entry.name)
        if not repo.exists():
            print(f"  MISSING repo: {repo}")
            bad += 1
        for link in entry.links:
            p = Path(link)
            if not (p.is_symlink() or p.exists()):
                print(f"  MISSING link: {p}")
                bad += 1
    if bad:
        print(f"{bad} issue(s) found")
        return 1
    print("all good")
    return 0


# ── Internals ───────────────────────────────────────────────────────────────

def _resolve_source(name_or_source: str) -> tuple[str, str | None]:
    """Return (source, name-if-known).

    Registered short names resolve to (git_url, name). Git URLs and local paths
    return (source, None) — name is derived from the manifest after fetch.
    """
    url = registry.resolve(name_or_source)
    if url is not None:
        return url, name_or_source

    path = Path(name_or_source).expanduser()
    if path.exists() and path.is_dir():
        return str(path.resolve()), None

    if name_or_source.startswith(("http://", "https://", "git@")) \
       or name_or_source.endswith(".git"):
        return name_or_source, None

    raise ValueError(
        f"unknown skillset: {name_or_source} "
        f"(not in registry, not a path, not a git URL)"
    )


def _fetch(source: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    src_path = Path(source)
    if src_path.exists():
        # Local path — copy for independence; use `dev` if you want a live symlink.
        shutil.copytree(src_path, dest)
    else:
        subprocess.check_call(["git", "clone", source, str(dest)])


def _finish_install(
    *,
    name: str,
    source: str,
    mode: str,
    agents: list[str],
    copy: bool,
    project: bool,
) -> int:
    repo = skillset_repo(name)
    m = manifest_mod.load(repo)
    entry = SkillsetEntry(name=name, source=source, mode=mode, agents=list(agents))

    # venvs, scripts, configs
    if m.venv is not None:
        _create_venv(name, m.venv)
    _link_runtime(entry, repo, m)
    _copy_configs(entry, repo, m)

    # targets
    for agent in agents:
        adapter = targets.get(agent)
        written = adapter.install(repo_dir=repo, manifest=m, copy=copy, project=project)
        for p in written:
            linkdb.record_link(entry, p)

    db = linkdb.load()
    db.put(entry)
    linkdb.save(db)

    print(f"installed geno-{name} ({mode}) → {', '.join(agents)}")
    return 0


def _create_venv(name: str, venv) -> None:
    venv_dir = skillset_venvs(name) / venv.name
    if venv_dir.exists():
        return
    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    print(f"  creating venv: {venv_dir}")
    subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
    if venv.deps:
        pip = venv_dir / "bin" / "pip"
        subprocess.check_call([str(pip), "install", "--upgrade", "pip"])
        subprocess.check_call([str(pip), "install", *venv.deps])


def _link_runtime(entry: SkillsetEntry, repo: Path, m) -> None:
    for spec in m.runtime:
        src = (repo / spec.src).resolve()
        dst = skillset_scripts(entry.name) / spec.dst
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_symlink() or dst.exists():
            if dst.is_dir() and not dst.is_symlink():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        dst.symlink_to(src)
        linkdb.record_link(entry, dst)


def _copy_configs(entry: SkillsetEntry, repo: Path, m) -> None:
    for spec in m.config:
        src = repo / spec.src
        dst = skillset_configs(entry.name) / spec.dst
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            continue  # copy-once: preserve user edits
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        linkdb.record_config(entry, dst)


def _wipe(path: Path) -> None:
    if path.is_symlink():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path, ignore_errors=True)
