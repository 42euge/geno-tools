"""Tests for `geno-tools launch` — profile → container composition (P5)."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest
import yaml

from geno_tools import commands, mcp, paths, profiles


@pytest.fixture()
def env(tmp_path, tmp_root, monkeypatch):
    """A launch-ready world: PROFILES_DIR, an installed skillset with an
    'exp' variant worktree, a file MCP catalog, and geno-iso 'present'.

    Depends on tmp_root so paths.ROOT is redirected to a temp dir.
    """
    prof_dir = tmp_path / "profiles"
    prof_dir.mkdir()
    monkeypatch.setattr(paths, "PROFILES_DIR", prof_dir)

    # installed skillset geno-x with main + exp worktree holding skills/
    root = paths.skillset_root("geno-x")
    (root / "main" / "skills").mkdir(parents=True)
    (root / ".worktrees" / "exp" / "skills" / "demo").mkdir(parents=True)
    (root / "active").symlink_to("main")

    # file MCP catalog
    cat = tmp_path / "cat.yaml"
    cat.write_text(yaml.safe_dump({"core": {"url": "http://x/core"}}))
    monkeypatch.setattr(mcp, "_discovered", True)
    monkeypatch.setattr(mcp, "sources", lambda: [{"kind": "file", "path": str(cat)}])

    # geno-iso 'installed'
    monkeypatch.setattr("shutil.which", lambda n: "/usr/bin/geno-iso")

    # record the container invocation instead of running it
    calls = {}
    def _call(cmd, *a, **kw):
        calls["cmd"] = cmd
        calls["env"] = kw.get("env", {})
        return 0
    monkeypatch.setattr("subprocess.call", _call)

    _write = prof_dir / "eng.yaml"
    _write.write_text(yaml.safe_dump({
        "agents": ["claude-code"],
        "skills": [{"name": "geno-x", "variant": "exp"}],
        "mcp": ["core"],
    }))
    return types.SimpleNamespace(calls=calls, root=root)


def _args(**kw):
    base = dict(agent="claude-code", profile="eng", workspace=".",
                ephemeral=False, dry_run=False)
    base.update(kw)
    return types.SimpleNamespace(**base)


class TestLaunch:
    def test_builds_geno_iso_invocation(self, env):
        rc = commands._launch(_args())
        assert rc == 0
        cmd = env.calls["cmd"]
        assert cmd[:5] == ["geno-iso", "run", "--agent", "claude", "--profile"]
        assert "bare" in cmd
        assert "--mcp-config" in cmd

    def test_variant_worktree_bind_mounted(self, env):
        commands._launch(_args())
        mounts = json.loads(env.calls["env"]["GENO_ISO_MOUNTS"])
        assert len(mounts) == 1
        host, dest = mounts[0]
        assert host.endswith(str(Path(".worktrees") / "exp" / "skills"))
        assert dest == "/home/agent/.claude/skills/geno-x"

    def test_mcp_config_written(self, env):
        commands._launch(_args())
        cmd = env.calls["cmd"]
        cfg = Path(cmd[cmd.index("--mcp-config") + 1])
        data = json.loads(cfg.read_text())
        assert data == {"mcpServers": {"core": {"url": "http://x/core"}}}

    def test_ephemeral_flag(self, env):
        commands._launch(_args(ephemeral=True))
        assert "--rm" in env.calls["cmd"]

    def test_dry_run_does_not_call(self, env):
        rc = commands._launch(_args(dry_run=True))
        assert rc == 0
        assert "cmd" not in env.calls  # subprocess.call never hit

    def test_agent_not_in_profile(self, env):
        rc = commands._launch(_args(agent="codex"))
        assert rc == 1

    def test_unknown_agent(self, env):
        rc = commands._launch(_args(agent="nope"))
        assert rc == 1

    def test_missing_skillset_errors(self, env, monkeypatch):
        (paths.PROFILES_DIR / "bad.yaml").write_text(yaml.safe_dump({
            "agents": ["claude-code"], "skills": ["geno-absent"]}))
        rc = commands._launch(_args(profile="bad"))
        assert rc == 1

    def test_requires_geno_iso(self, env, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda n: None)
        rc = commands._launch(_args())
        assert rc == 1
