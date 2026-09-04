from types import SimpleNamespace

import pytest

from geno_tools.sync import reconcile


def entry(name: str, sha: str = "new") -> dict[str, str]:
    return {
        "url": f"https://example.test/{name}.git",
        "branch": "main",
        "sha": sha,
        "version": "1.0.0",
    }


def lock(skillsets=None, config=None):
    return {
        "version": 1,
        "machine": "fixture",
        "generated": "now",
        "skillsets": dict(skillsets or {}),
        "config": dict(config or {}),
    }


class StatefulOperations:
    def __init__(self, monkeypatch, initial, source, *, config=None):
        self.state = dict(initial)
        self.source = source
        self.config = dict(config or {})
        self.calls = []
        self.requires = {}
        self.update_status = {}
        self.update_error = set()
        self.install_error = set()
        self.remove_error = set()
        monkeypatch.setattr(reconcile, "build_lockfile", self.export)
        monkeypatch.setattr(reconcile, "dirty_skillsets", lambda: [])
        monkeypatch.setattr(reconcile, "_install_one", self.install)
        monkeypatch.setattr(reconcile, "_update_one", self.update)
        monkeypatch.setattr(reconcile.remove, "run", self.remove)
        monkeypatch.setattr(reconcile, "_get_requires", self.get_requires)
        monkeypatch.setattr(reconcile, "apply_portable_config", self.apply_config)

    def export(self):
        return lock(self.state, self.config)

    def install(self, url, *, installing, branch=None):
        name = url.removesuffix(".git").rsplit("/", 1)[-1]
        self.calls.append(("install", name))
        if name in self.install_error:
            raise RuntimeError("clone failed")
        self.state[name] = self.source["skillsets"][name]
        for dependency in self.requires.get(name, []):
            self.state[dependency] = entry(dependency)
        return 0

    def update(self, name, *, force_venv_rebuild=False):
        self.calls.append(("update", name, force_venv_rebuild))
        if name in self.update_error:
            raise RuntimeError("update exploded")
        status = self.update_status.get(name, "updated")
        if status == "updated":
            self.state[name] = self.source["skillsets"][name]
        return SimpleNamespace(status=status, detail="on branch 'feature'")

    def remove(self, args):
        self.calls.append(("remove", args.name))
        if args.name in self.remove_error:
            raise RuntimeError("remove exploded")
        self.state.pop(args.name, None)
        return 0

    def get_requires(self, name):
        return self.requires.get(name, [])

    def apply_config(self, value):
        self.calls.append(("config", dict(value)))
        self.config.update(value)


def test_reconcile_installs_updates_and_removes_to_match_source(monkeypatch):
    source = lock(
        {"geno-a": entry("geno-a"), "geno-b": entry("geno-b")},
        {"mode": "user"},
    )
    operations = StatefulOperations(
        monkeypatch,
        {"geno-b": entry("geno-b", "old"), "geno-extra": entry("geno-extra")},
        source,
    )

    result = reconcile.reconcile(source, reconcile.ReconcileOptions(yes=True))

    assert operations.export()["skillsets"] == source["skillsets"]
    assert operations.config == source["config"]
    assert [(action.name, action.kind) for action in result.actions] == [
        ("geno-a", "install"),
        ("geno-b", "update"),
        ("geno-extra", "remove"),
        ("config", "apply"),
    ]
    assert result.failures == ()
    assert result.changed is True


def test_reconcile_aborts_dirty_preflight_before_mutation(monkeypatch):
    source = lock({"geno-a": entry("geno-a")})
    operations = StatefulOperations(monkeypatch, {}, source)
    monkeypatch.setattr(reconcile, "dirty_skillsets", lambda: ["geno-work"])

    with pytest.raises(reconcile.ReconcileError, match="geno-work"):
        reconcile.reconcile(source, reconcile.ReconcileOptions(yes=True))

    assert operations.calls == []


def test_reconcile_dry_run_reports_plan_without_mutation(monkeypatch):
    source = lock({"geno-a": entry("geno-a")})
    operations = StatefulOperations(
        monkeypatch, {"geno-extra": entry("geno-extra")}, source
    )

    result = reconcile.reconcile(
        source,
        reconcile.ReconcileOptions(dry_run=True),
        confirm=lambda _names: pytest.fail("dry-run must not prompt"),
    )

    assert [(action.name, action.kind) for action in result.actions] == [
        ("geno-a", "install"),
        ("geno-extra", "remove"),
    ]
    assert operations.calls == []
    assert operations.state == {"geno-extra": entry("geno-extra")}


def test_reconcile_declined_removal_mutates_nothing(monkeypatch):
    source = lock({"geno-a": entry("geno-a")})
    operations = StatefulOperations(
        monkeypatch, {"geno-extra": entry("geno-extra")}, source
    )

    with pytest.raises(reconcile.ReconcileError, match="cancelled"):
        reconcile.reconcile(
            source,
            reconcile.ReconcileOptions(),
            confirm=lambda names: names == [],
        )

    assert operations.calls == []


def test_confirm_removals_refuses_when_standard_input_is_exhausted(monkeypatch):
    monkeypatch.setattr(
        "builtins.input", lambda _prompt: (_ for _ in ()).throw(EOFError())
    )
    assert reconcile.confirm_removals(["geno-extra"]) is False


def test_reconcile_collects_skipped_update_as_failure(monkeypatch):
    source = lock({"geno-a": entry("geno-a")})
    operations = StatefulOperations(
        monkeypatch, {"geno-a": entry("geno-a", "old")}, source
    )
    operations.update_status["geno-a"] = "skipped"

    result = reconcile.reconcile(source, reconcile.ReconcileOptions(yes=True))

    assert result.failures == (
        reconcile.ReconcileAction("geno-a", "update", "on branch 'feature'"),
    )
    assert result.changed is False


def test_reconcile_continues_after_independent_install_failure(monkeypatch):
    source = lock({"geno-a": entry("geno-a"), "geno-b": entry("geno-b")})
    operations = StatefulOperations(
        monkeypatch, {"geno-b": entry("geno-b", "old")}, source
    )
    operations.install_error.add("geno-a")

    result = reconcile.reconcile(source, reconcile.ReconcileOptions(yes=True))

    assert operations.state["geno-b"] == entry("geno-b")
    assert result.failures[0].name == "geno-a"
    assert result.failures[0].kind == "install"


def test_reconcile_collects_unexpected_update_and_remove_failures(monkeypatch):
    source = lock({"geno-update": entry("geno-update")})
    operations = StatefulOperations(
        monkeypatch,
        {
            "geno-update": entry("geno-update", "old"),
            "geno-remove": entry("geno-remove"),
        },
        source,
    )
    operations.update_error.add("geno-update")
    operations.remove_error.add("geno-remove")

    result = reconcile.reconcile(source, reconcile.ReconcileOptions(yes=True))

    assert result.failures == (
        reconcile.ReconcileAction("geno-update", "update", "update exploded"),
        reconcile.ReconcileAction("geno-remove", "remove", "remove exploded"),
    )


def test_reconcile_no_rebuild_reconciles_git_without_venv(monkeypatch):
    source = lock({"geno-a": entry("geno-a")})
    operations = StatefulOperations(
        monkeypatch, {"geno-a": entry("geno-a", "old")}, source
    )

    reconcile.reconcile(
        source, reconcile.ReconcileOptions(yes=True, rebuild=False)
    )

    assert operations.calls == [("update", "geno-a", False)]


def test_reconcile_second_run_is_idempotent(monkeypatch):
    source = lock({"geno-a": entry("geno-a")}, {"mode": "user"})
    operations = StatefulOperations(monkeypatch, {}, source)

    first = reconcile.reconcile(source, reconcile.ReconcileOptions(yes=True))
    second = reconcile.reconcile(source, reconcile.ReconcileOptions(yes=True))

    assert first.changed is True
    assert second.actions == ()
    assert second.changed is False


def test_reconcile_preserves_dependency_absent_from_source_lockfile(monkeypatch):
    source = lock({"geno-app": entry("geno-app")})
    operations = StatefulOperations(monkeypatch, {}, source)
    operations.requires["geno-app"] = ["geno-lib"]

    first = reconcile.reconcile(source, reconcile.ReconcileOptions(yes=True))
    second = reconcile.reconcile(
        source,
        reconcile.ReconcileOptions(),
        confirm=lambda names: pytest.fail(f"protected dependency prompted: {names}"),
    )

    assert set(operations.state) == {"geno-app", "geno-lib"}
    assert all(call != ("remove", "geno-lib") for call in operations.calls)
    assert first.changed is True
    assert second.actions == ()
