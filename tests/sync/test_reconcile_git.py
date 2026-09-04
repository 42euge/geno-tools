import subprocess
from pathlib import Path
import json

from geno_tools.skills_manager import paths
from geno_tools.skills_manager.commands import dev, install, remove, upgrade
from geno_tools.sync import lockfile, reconcile, snapshot


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


def test_reconcile_installs_the_source_branch_instead_of_the_remote_default(
    tmp_path, tmp_root, tmp_config, monkeypatch
):
    monkeypatch.setattr(install, "_install_skills_via_npx", lambda *_a, **_kw: None)
    repository, _main_sha = create_skillset(tmp_path, "geno-branch")
    subprocess.run(
        ["git", "-C", str(repository), "switch", "-q", "-c", "feature"],
        check=True,
    )
    (repository / "payload.txt").write_text("feature\n")
    feature_sha = commit(repository, "feature")
    subprocess.run(
        ["git", "-C", str(repository), "switch", "-q", "main"], check=True
    )
    source = lock("geno-branch", repository, feature_sha)
    source["skillsets"]["geno-branch"]["branch"] = "feature"

    result = reconcile.reconcile(source, reconcile.ReconcileOptions(yes=True))

    managed = paths.skillset_worktree("geno-branch")
    assert result.failures == ()
    assert git(managed, "branch", "--show-current") == "feature"
    assert git(managed, "rev-parse", "HEAD") == feature_sha


def test_reconcile_installs_the_recorded_commit_not_a_newer_branch_tip(
    tmp_path, tmp_root, tmp_config, monkeypatch
):
    monkeypatch.setattr(install, "_install_skills_via_npx", lambda *_a, **_kw: None)
    repository, recorded_sha = create_skillset(tmp_path, "geno-recorded")
    source = lock("geno-recorded", repository, recorded_sha)
    (repository / "payload.txt").write_text("newer\n")
    commit(repository, "newer branch tip")

    result = reconcile.reconcile(source, reconcile.ReconcileOptions(yes=True))

    managed = paths.skillset_worktree("geno-recorded")
    assert result.failures == ()
    assert git(managed, "rev-parse", "HEAD") == recorded_sha
    assert (managed / "payload.txt").read_text() == "one\n"


def test_reconcile_moves_an_existing_stable_checkout_to_the_recorded_commit(
    tmp_path, tmp_root, tmp_config, monkeypatch
):
    monkeypatch.setattr(install, "_install_skills_via_npx", lambda *_a, **_kw: None)
    monkeypatch.setattr(upgrade, "_install_skills_via_npx", lambda *_a, **_kw: None)
    monkeypatch.setattr(
        upgrade, "_uninstall_skill_names_via_npx", lambda *_a, **_kw: None
    )
    repository, first_sha = create_skillset(tmp_path, "geno-rewind")
    first = lock("geno-rewind", repository, first_sha)
    reconcile.reconcile(first, reconcile.ReconcileOptions(yes=True))
    (repository / "payload.txt").write_text("newer\n")
    second_sha = commit(repository, "newer branch tip")
    second = lock("geno-rewind", repository, second_sha)
    reconcile.reconcile(second, reconcile.ReconcileOptions(yes=True))

    result = reconcile.reconcile(first, reconcile.ReconcileOptions(yes=True))

    managed = paths.skillset_worktree("geno-rewind")
    assert result.failures == ()
    assert git(managed, "rev-parse", "HEAD") == first_sha
    assert (managed / "payload.txt").read_text() == "one\n"


def create_selection_fixture(tmp_path, tmp_root, tmp_config, monkeypatch):
    name = "geno-selected"
    root = tmp_root / name
    stable = root / "main"
    stable.mkdir(parents=True)
    subprocess.run(
        ["git", "-C", str(stable), "init", "-q", "-b", "main"], check=True
    )
    (stable / "genotools.yaml").write_text(
        f'name: {name}\nversion: "1.0.0"\n'
    )
    (stable / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: stable\n---\n"
    )
    subprocess.run(["git", "-C", str(stable), "add", "."], check=True)
    commit(stable, "stable")
    origin = tmp_path / "stable-origin.git"
    subprocess.run(
        ["git", "clone", "-q", "--bare", str(stable), str(origin)], check=True
    )
    subprocess.run(
        ["git", "-C", str(stable), "remote", "add", "origin", str(origin)],
        check=True,
    )
    (root / "active").symlink_to("main")

    source = tmp_path / "external" / name
    source.mkdir(parents=True)
    subprocess.run(
        ["git", "-C", str(source), "init", "-q", "-b", "feature"], check=True
    )
    (source / "genotools.yaml").write_text(
        f'name: {name}\nversion: "2.0.0"\n'
    )
    (source / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: dev\n---\n"
    )
    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
    commit(source, "dev")

    monkeypatch.setattr(install, "SYSTEM_BIN", tmp_path / "bin")
    monkeypatch.setattr(install, "_install_skills_via_npx", lambda *_args: None)
    monkeypatch.setattr(
        install, "_uninstall_skill_names_via_npx", lambda *_args, **_kwargs: None
    )
    stable_lock = lockfile.build_lockfile(machine="source", generated="now")
    payload = snapshot.capture(source, machine="source")
    return name, root, stable, source, stable_lock, payload


def package_for(name, stable_lock, kind, payload=None):
    selected = {"kind": kind}
    if payload is not None:
        selected["snapshot"] = payload
    return {
        "protocol": 1,
        "lockfile": stable_lock,
        "selections": {name: selected},
    }


def test_reconcile_package_installs_stable_from_bundle_when_origin_is_unreachable(
    tmp_path, tmp_root, tmp_config, monkeypatch
):
    name = "geno-local-stable"
    source = tmp_path / "local-stable"
    source.mkdir()
    subprocess.run(
        ["git", "-C", str(source), "init", "-q", "-b", "main"], check=True
    )
    (source / "genotools.yaml").write_text(
        f'name: {name}\nversion: "3.0.0"\n'
    )
    (source / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: local only\n---\n"
    )
    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
    source_sha = commit(source, "local stable")
    stable_snapshot = snapshot.capture(source, machine="source")
    value = {
        "protocol": 1,
        "lockfile": {
            "version": 1,
            "machine": "source",
            "generated": "now",
            "skillsets": {
                name: {
                    "url": "https://unreachable.invalid/geno-local-stable.git",
                    "branch": "main",
                    "sha": source_sha,
                    "version": "3.0.0",
                }
            },
            "config": {},
        },
        "selections": {
            name: {"kind": "stable", "stable_snapshot": stable_snapshot}
        },
    }
    monkeypatch.setattr(install, "_install_skills_via_npx", lambda *_args: None)

    result = reconcile.reconcile_package(value, reconcile.ReconcileOptions(yes=True))

    managed = paths.skillset_worktree(name)
    assert result.failures == ()
    assert git(managed, "rev-parse", "HEAD") == source_sha
    assert git(paths.skillset_git(name), "remote", "get-url", "origin") == (
        "https://unreachable.invalid/geno-local-stable.git"
    )


def test_reconcile_package_selects_stable_and_preserves_dev_rollback(
    tmp_path, tmp_root, tmp_config, monkeypatch
):
    name, root, stable, source, stable_lock, _payload = create_selection_fixture(
        tmp_path, tmp_root, tmp_config, monkeypatch
    )
    dev.activate(source)
    (source / "dirty.txt").write_text("must remain untouched\n")

    result = reconcile.reconcile_package(
        package_for(name, stable_lock, "stable"),
        reconcile.ReconcileOptions(yes=True),
    )

    assert result.failures == ()
    assert paths.skillset_active(name).resolve() == stable.resolve()
    rollback = json.loads((root / "dev-rollback.json").read_text())
    assert rollback["kind"] == "dev"
    assert rollback["state"]["checkout"] == str(source.resolve())
    assert (source / "dirty.txt").read_text() == "must remain untouched\n"


def test_reconcile_package_materializes_dev_and_is_idempotent(
    tmp_path, tmp_root, tmp_config, monkeypatch
):
    name, root, stable, _source, stable_lock, payload = create_selection_fixture(
        tmp_path, tmp_root, tmp_config, monkeypatch
    )
    value = package_for(name, stable_lock, "dev", payload)

    first = reconcile.reconcile_package(value, reconcile.ReconcileOptions(yes=True))
    active = paths.skillset_active(name).resolve()
    second = reconcile.reconcile_package(value, reconcile.ReconcileOptions(yes=True))

    assert first.failures == ()
    assert [(action.name, action.kind) for action in first.actions] == [
        (name, "activate-dev")
    ]
    assert active.parent == root / "snapshots"
    assert active.name == payload["fingerprint"]
    state = json.loads(paths.skillset_dev_state(name).read_text())
    assert state["checkout"] == str(active)
    assert state["snapshot"] == {
        "machine": "source",
        "captured": payload["captured"],
        "source": str(_source),
        "fingerprint": payload["fingerprint"],
        "commit": payload["commit"],
        "branch": "feature",
    }
    assert second.actions == ()
    assert paths.skillset_active(name).resolve() == active
    dev.deactivate(name)
    assert paths.skillset_active(name).resolve() == stable.resolve()


def test_reconcile_package_rejects_bad_snapshot_before_replacing_external_dev(
    tmp_path, tmp_root, tmp_config, monkeypatch
):
    name, root, _stable, source, stable_lock, payload = create_selection_fixture(
        tmp_path, tmp_root, tmp_config, monkeypatch
    )
    dev.activate(source)
    bad = {**payload, "fingerprint": "0" * 64}

    result = reconcile.reconcile_package(
        package_for(name, stable_lock, "dev", bad),
        reconcile.ReconcileOptions(yes=True),
    )

    assert result.failures[0].name == name
    assert result.failures[0].kind == "activate-dev"
    assert paths.skillset_active(name).resolve() == source.resolve()
    assert not (root / "dev-rollback.json").exists()
