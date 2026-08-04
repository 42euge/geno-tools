"""Tests for geno-iso bind-mount support (P4).

Verifies that extra (host, container) mounts are threaded into the docker run
command for both the persistent and ephemeral paths. subprocess is mocked;
no real docker is invoked.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from geno_tools.iso import docker


class _Recorder:
    def __init__(self):
        self.cmds: list[list[str]] = []

    def __call__(self, cmd, *a, **kw):
        self.cmds.append(cmd)
        class R:
            returncode = 0
            stdout = ""
        return R()


def _mount_pairs(cmd: list[str]) -> list[str]:
    """Extract the values following each -v flag."""
    return [cmd[i + 1] for i, tok in enumerate(cmd) if tok == "-v"]


def test_create_container_adds_mounts(tmp_path, monkeypatch):
    rec = _Recorder()
    monkeypatch.setattr("subprocess.run", rec)
    monkeypatch.setattr(docker, "container_exists", lambda n: False)
    monkeypatch.setattr(docker, "_seed_settings", lambda *a, **k: None)
    monkeypatch.setattr(docker, "image_latest", lambda *a, **k: "img:latest")

    variant = tmp_path / "worktrees" / "exp"
    variant.mkdir(parents=True)
    docker.create_container(
        "demo", tmp_path / "ws", tmp_path / ".env",
        mounts=[(str(variant), "/home/agent/.claude/skills/geno-x")],
    )
    run_cmd = rec.cmds[-1]
    vs = _mount_pairs(run_cmd)
    # workspace mount + our variant mount
    assert any(v.endswith(":/home/agent/workspace") for v in vs)
    assert any(v.endswith(":/home/agent/.claude/skills/geno-x") for v in vs)


def test_run_ephemeral_adds_mounts(tmp_path, monkeypatch):
    rec = _Recorder()
    monkeypatch.setattr("subprocess.run", rec)
    monkeypatch.setattr(docker, "image_latest", lambda *a, **k: "img:latest")

    variant = tmp_path / "wt"
    variant.mkdir()
    docker.run_ephemeral(
        tmp_path / "ws", tmp_path / ".env",
        claude_args=["-p", "hi"],
        mounts=[(str(variant), "/home/agent/.claude/skills/geno-y")],
    )
    cmd = rec.cmds[-1]
    assert "--rm" in cmd
    vs = _mount_pairs(cmd)
    assert any(v.endswith(":/home/agent/.claude/skills/geno-y") for v in vs)


def test_no_mounts_is_backward_compatible(tmp_path, monkeypatch):
    rec = _Recorder()
    monkeypatch.setattr("subprocess.run", rec)
    monkeypatch.setattr(docker, "container_exists", lambda n: False)
    monkeypatch.setattr(docker, "_seed_settings", lambda *a, **k: None)
    monkeypatch.setattr(docker, "image_latest", lambda *a, **k: "img:latest")

    docker.create_container("demo", tmp_path / "ws", tmp_path / ".env")
    vs = _mount_pairs(rec.cmds[-1])
    assert len(vs) == 1  # only the workspace mount
