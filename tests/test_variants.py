"""Tests for the variant machinery: fork / use / promote.

These build a REAL git bare repo + worktree (git is available in CI) so the
worktree/branch/merge behavior is exercised for real. The npx skills
registration call is mocked (it needs the network).
"""

from __future__ import annotations

import subprocess
import types
from pathlib import Path

import pytest

from geno_tools import commands, paths


def _git(cwd: Path, *args: str) -> None:
    subprocess.check_call(["git", "-C", str(cwd), *args])


@pytest.fixture()
def installed_skillset(tmp_root: Path, monkeypatch: pytest.MonkeyPatch):
    """Create a real git-backed skillset laid out like _install_one leaves it.

    ~/.geno-tools/geno-demo/
        .git/            (bare)
        main/            (worktree on the default branch)
        active -> main
    Returns the skillset root. npx registration is stubbed to record calls.
    """
    full = "geno-demo"
    root = paths.skillset_root(full)
    root.mkdir(parents=True)

    # Seed a normal repo, then create the bare clone the layout expects.
    seed = tmp_root / "_seed"
    seed.mkdir()
    _git(seed, "init", "-q", "-b", "main")
    _git(seed, "config", "user.email", "t@t")
    _git(seed, "config", "user.name", "t")
    (seed / "SKILL.md").write_text(
        "---\nname: geno-demo\ndescription: demo\n---\n# demo\n"
    )
    _git(seed, "add", "-A")
    _git(seed, "commit", "-q", "-m", "init")

    bare = paths.skillset_git(full)
    subprocess.check_call(["git", "clone", "--bare", "--quiet",
                           str(seed), str(bare)])
    subprocess.check_call([
        "git", "-C", str(bare), "worktree", "add",
        str(paths.skillset_worktree(full, "main")), "main",
    ])
    paths.skillset_active(full).symlink_to("main")

    # Stub the npx registration so use/promote don't hit the network.
    calls: list[list[str]] = []
    monkeypatch.setattr(commands, "_install_skills_via_npx",
                        lambda f, agent="*": calls.append([f, agent]))
    return types.SimpleNamespace(full=full, root=root, npx_calls=calls)


def _args(**kw):
    return types.SimpleNamespace(**kw)


class TestFork:
    def test_creates_worktree_and_branch(self, installed_skillset):
        rc = commands._fork(_args(name="geno-demo", variant="exp",
                                  isolated_venv=False))
        assert rc == 0
        wt = paths.skillset_worktree("geno-demo", "exp")
        assert wt.exists()
        assert (wt / "SKILL.md").exists()
        # branch exists in the bare repo
        branches = subprocess.check_output(
            ["git", "-C", str(paths.skillset_git("geno-demo")),
             "branch", "--list", "exp"], text=True)
        assert "exp" in branches

    def test_does_not_flip_active(self, installed_skillset):
        commands._fork(_args(name="geno-demo", variant="exp",
                             isolated_venv=False))
        assert paths.skillset_active("geno-demo").readlink() == Path("main")

    def test_rejects_reserved_main(self, installed_skillset):
        rc = commands._fork(_args(name="geno-demo", variant="main",
                                  isolated_venv=False))
        assert rc == 1

    def test_rejects_duplicate_variant(self, installed_skillset):
        commands._fork(_args(name="geno-demo", variant="exp",
                             isolated_venv=False))
        rc = commands._fork(_args(name="geno-demo", variant="exp",
                                  isolated_venv=False))
        assert rc == 1

    def test_not_installed(self, tmp_root, monkeypatch):
        monkeypatch.setattr(commands, "_install_skills_via_npx",
                            lambda *a, **k: None)
        rc = commands._fork(_args(name="geno-missing", variant="exp",
                                  isolated_venv=False))
        assert rc == 1


class TestUse:
    def test_flips_active_and_reregisters(self, installed_skillset):
        commands._fork(_args(name="geno-demo", variant="exp",
                             isolated_venv=False))
        rc = commands._use(_args(spec="geno-demo@exp", here=False))
        assert rc == 0
        active = paths.skillset_active("geno-demo").readlink()
        assert str(active) == str(Path(".worktrees") / "exp")
        assert installed_skillset.npx_calls  # re-registered

    def test_back_to_main(self, installed_skillset):
        commands._fork(_args(name="geno-demo", variant="exp",
                             isolated_venv=False))
        commands._use(_args(spec="geno-demo@exp", here=False))
        rc = commands._use(_args(spec="geno-demo@main", here=False))
        assert rc == 0
        assert paths.skillset_active("geno-demo").readlink() == Path("main")

    def test_missing_variant(self, installed_skillset):
        rc = commands._use(_args(spec="geno-demo@nope", here=False))
        assert rc == 1

    def test_bad_spec(self, installed_skillset):
        rc = commands._use(_args(spec="geno-demo", here=False))
        assert rc == 1


class TestPromote:
    def _commit_on_variant(self, full: str, variant: str) -> None:
        wt = paths.skillset_worktree(full, variant)
        (wt / "NEW.md").write_text("new file\n")
        _git(wt, "config", "user.email", "t@t")
        _git(wt, "config", "user.name", "t")
        _git(wt, "add", "-A")
        _git(wt, "commit", "-q", "-m", "variant change")

    def test_ff_merges_into_main(self, installed_skillset):
        commands._fork(_args(name="geno-demo", variant="exp",
                             isolated_venv=False))
        self._commit_on_variant("geno-demo", "exp")
        rc = commands._promote(_args(name="geno-demo", variant="exp"))
        assert rc == 0
        main_wt = paths.skillset_worktree("geno-demo", "main")
        assert (main_wt / "NEW.md").exists()

    def test_flips_active_back_when_on_variant(self, installed_skillset):
        commands._fork(_args(name="geno-demo", variant="exp",
                             isolated_venv=False))
        self._commit_on_variant("geno-demo", "exp")
        commands._use(_args(spec="geno-demo@exp", here=False))
        commands._promote(_args(name="geno-demo", variant="exp"))
        assert paths.skillset_active("geno-demo").readlink() == Path("main")

    def test_rejects_dirty_variant(self, installed_skillset):
        commands._fork(_args(name="geno-demo", variant="exp",
                             isolated_venv=False))
        wt = paths.skillset_worktree("geno-demo", "exp")
        (wt / "dirty.txt").write_text("uncommitted\n")
        rc = commands._promote(_args(name="geno-demo", variant="exp"))
        assert rc == 1

    def test_missing_variant(self, installed_skillset):
        rc = commands._promote(_args(name="geno-demo", variant="nope"))
        assert rc == 1
