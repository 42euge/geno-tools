import subprocess
from pathlib import Path

from geno_tools.skills_manager import paths
from geno_tools.skills_manager.commands import install, remove, upgrade
from geno_tools.sync import reconcile


def git(repository: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repository), *arguments], text=True
    ).strip()


def commit(repository: Path, message: str) -> str:
    subprocess.check_call(
        [
            "git",
            "-C",
            str(repository),
            "-c",
            "user.name=Sync Test",
            "-c",
            "user.email=sync@example.test",
            "commit",
            "-q",
            "-am",
            message,
        ]
    )
    return git(repository, "rev-parse", "HEAD")


def create_skillset(tmp_path: Path, name: str) -> tuple[Path, str]:
    repository = tmp_path / "origins" / f"{name}.git"
    repository.mkdir(parents=True)
    subprocess.check_call(["git", "-C", str(repository), "init", "-q", "-b", "main"])
    (repository / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: fixture\n---\n# {name}\n"
    )
    (repository / "genotools.yaml").write_text(
        f'name: {name}\nversion: "1.0.0"\n'
    )
    (repository / "payload.txt").write_text("one\n")
    subprocess.check_call(["git", "-C", str(repository), "add", "."])
    sha = commit(repository, "initial")
    return repository, sha


def lock(name: str, repository: Path, sha: str) -> dict:
    return {
        "version": 1,
        "machine": "source",
        "generated": "now",
        "skillsets": {
            name: {
                "url": repository.as_uri(),
                "branch": "main",
                "sha": sha,
                "version": "1.0.0",
            }
        },
        "config": {},
    }


def test_reconcile_real_managed_repo_install_update_remove_and_idempotency(
    tmp_path, tmp_root, tmp_config, monkeypatch
):
    monkeypatch.setattr(install, "_install_skills_via_npx", lambda *_args, **_kw: None)
    monkeypatch.setattr(remove, "_uninstall_skills_via_npx", lambda *_args, **_kw: None)
    monkeypatch.setattr(upgrade, "_install_skills_via_npx", lambda *_args, **_kw: None)
    monkeypatch.setattr(
        upgrade, "_uninstall_skill_names_via_npx", lambda *_args, **_kw: None
    )
    repository, first_sha = create_skillset(tmp_path, "geno-real")
    source = lock("geno-real", repository, first_sha)

    installed = reconcile.reconcile(source, reconcile.ReconcileOptions(yes=True))

    managed = paths.skillset_worktree("geno-real")
    assert managed.is_dir()
    assert paths.skillset_active("geno-real").resolve() == managed.resolve()
    assert git(managed, "branch", "--show-current") == "main"
    assert git(managed, "rev-parse", "HEAD") == first_sha
    assert [(action.name, action.kind) for action in installed.actions] == [
        ("geno-real", "install")
    ]

    unchanged = reconcile.reconcile(source, reconcile.ReconcileOptions(yes=True))
    assert unchanged.actions == ()
    assert unchanged.changed is False

    (repository / "payload.txt").write_text("two\n")
    second_sha = commit(repository, "advance")
    updated = reconcile.reconcile(
        lock("geno-real", repository, second_sha),
        reconcile.ReconcileOptions(yes=True),
    )

    assert git(managed, "rev-parse", "HEAD") == second_sha
    assert [(action.name, action.kind) for action in updated.actions] == [
        ("geno-real", "update")
    ]

    empty = {
        "version": 1,
        "machine": "source",
        "generated": "later",
        "skillsets": {},
        "config": {},
    }
    removed = reconcile.reconcile(empty, reconcile.ReconcileOptions(yes=True))
    assert not paths.skillset_root("geno-real").exists()
    assert [(action.name, action.kind) for action in removed.actions] == [
        ("geno-real", "remove")
    ]
