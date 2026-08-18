"""Tests for `geno-tools skills uninstall` — the inverse of install.

The central guarantee: it removes geno-tools' own footprint but NEVER deletes
user data living in ~/.geno. All destructive ops target temp dirs.
"""

from __future__ import annotations

import types
from pathlib import Path

import pytest

from geno_tools import commands, paths


@pytest.fixture()
def fake_install(tmp_path, monkeypatch):
    """Simulate a geno-tools skills install footprint under a temp HOME."""
    home = tmp_path
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    # rebind module-level path constants derived from home
    monkeypatch.setattr(paths, "ROOT", home / ".geno-tools")
    monkeypatch.setattr(paths, "GENO_DIR", home / ".geno")
    monkeypatch.setattr(commands, "SYSTEM_BIN", home / ".local" / "bin")
    monkeypatch.setattr(commands, "_AGENT_SKILL_DIRS",
                        [home / ".claude" / "skills", home / ".agents" / "skills"])
    monkeypatch.setattr(commands, "_CC_PLUGIN_DIRS",
                        [home / ".claude" / "plugins" / "cache" / "geno-tools"])
    # never actually shell out to npx
    monkeypatch.setattr(commands, "_uninstall_skills_via_npx", lambda n: None)
    monkeypatch.setattr(commands, "_clean_agent_json_configs", lambda: None)

    # skillsets
    (home / ".geno-tools" / "geno-notes" / "main").mkdir(parents=True)
    (home / ".geno-tools" / "geno-loops" / "main").mkdir(parents=True)
    # own state
    (home / ".geno").mkdir()
    for f in ("config.yaml", "registry.json", "bootstrap.log"):
        (home / ".geno" / f).write_text("x")
    (home / ".geno" / "traces").mkdir()
    (home / ".geno" / "health").mkdir()
    (home / ".geno" / "profiles").mkdir()
    # USER DATA — must survive
    (home / ".geno" / "recordings").mkdir()
    (home / ".geno" / "vault").mkdir()
    (home / ".geno" / "my-notes.md").write_text("precious")
    # agent skills
    (home / ".claude" / "skills" / "geno-notes").mkdir(parents=True)
    (home / ".claude" / "skills" / "geno-tools").mkdir(parents=True)
    (home / ".agents" / "skills" / "geno-loops").mkdir(parents=True)
    # plugin clone
    (home / ".claude" / "plugins" / "cache" / "geno-tools").mkdir(parents=True)
    return home


def _args(**kw):
    base = dict(dry_run=False, yes=True)
    base.update(kw)
    return types.SimpleNamespace(**base)


def test_dry_run_deletes_nothing(fake_install):
    commands._uninstall(_args(dry_run=True))
    assert (fake_install / ".geno-tools" / "geno-notes").exists()
    assert (fake_install / ".claude" / "skills" / "geno-tools").exists()
    assert (fake_install / ".geno" / "config.yaml").exists()


def test_removes_skillsets_and_registrations(fake_install):
    commands._uninstall(_args())
    assert not (fake_install / ".geno-tools").exists()  # emptied → removed
    assert not (fake_install / ".claude" / "skills" / "geno-notes").exists()
    assert not (fake_install / ".claude" / "skills" / "geno-tools").exists()
    assert not (fake_install / ".agents" / "skills" / "geno-loops").exists()
    assert not (fake_install / ".claude" / "plugins" / "cache" / "geno-tools").exists()


def test_user_data_preserved_by_default(fake_install):
    commands._uninstall(_args())
    # own state is kept
    assert (fake_install / ".geno" / "config.yaml").exists()
    # user data always kept
    assert (fake_install / ".geno" / "recordings").exists()
    assert (fake_install / ".geno" / "vault").exists()
    assert (fake_install / ".geno" / "my-notes.md").read_text() == "precious"


def test_only_managed_bin_symlinks_removed(fake_install, monkeypatch):
    binp = fake_install / ".local" / "bin"
    binp.mkdir(parents=True)
    # a geno-managed symlink (points into ~/.geno-tools)
    managed = binp / "geno-notes"
    managed.symlink_to(fake_install / ".geno-tools" / "geno-notes" / "main" / "bin" / "x")
    # an UNRELATED symlink that must be left alone
    other = binp / "ripgrep"
    other.symlink_to(fake_install / "somewhere" / "rg")
    commands._uninstall(_args())
    assert not managed.exists()
    assert other.is_symlink()  # untouched


def test_nothing_installed_is_safe(tmp_path, monkeypatch):
    home = tmp_path
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    monkeypatch.setattr(paths, "ROOT", home / ".geno-tools")
    monkeypatch.setattr(paths, "GENO_DIR", home / ".geno")
    monkeypatch.setattr(commands, "SYSTEM_BIN", home / ".local" / "bin")
    monkeypatch.setattr(commands, "_AGENT_SKILL_DIRS", [])
    monkeypatch.setattr(commands, "_CC_PLUGIN_DIRS", [])
    monkeypatch.setattr(commands, "_clean_agent_json_configs", lambda: None)
    rc = commands._uninstall(_args())
    assert rc == 0
