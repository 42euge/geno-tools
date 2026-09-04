import pytest

from geno_tools.sync import selection


INVENTORY = {
    "protocol": 1,
    "machine": "laptop",
    "skillsets": {
        "geno-dev": {
            "stable": {"version": "0.9.0"},
            "active": {
                "project_version": "1.0.0",
                "fingerprint": "a" * 64,
                "transfer_size": 100,
            },
        },
        "geno-stable": {
            "stable": {"version": "2.0.0"},
            "active": None,
        },
        "geno-tt": {
            "stable": {"version": "0.8.1"},
            "active": {
                "project_version": "0.9.0",
                "fingerprint": "b" * 64,
                "transfer_size": 200,
            },
        },
    },
}


def test_choose_asks_separately_for_each_eligible_skillset():
    calls = []

    def chooser(candidate, remaining):
        calls.append((candidate["name"], [item["name"] for item in remaining]))
        return {"geno-dev": "active", "geno-tt": "stable"}[candidate["name"]]

    chosen = selection.choose(INVENTORY, "ask", chooser, interactive=True)

    assert chosen == {
        "geno-dev": "active",
        "geno-stable": "stable",
        "geno-tt": "stable",
    }
    assert calls == [
        ("geno-dev", ["geno-dev", "geno-tt"]),
        ("geno-tt", ["geno-tt"]),
    ]


@pytest.mark.parametrize(
    "answer, expected",
    [
        (
            "active-all",
            {
                "geno-dev": "active",
                "geno-stable": "stable",
                "geno-tt": "active",
            },
        ),
        (
            "stable-all",
            {
                "geno-dev": "stable",
                "geno-stable": "stable",
                "geno-tt": "stable",
            },
        ),
    ],
)
def test_choose_all_shortcuts_apply_to_every_remaining_skillset(answer, expected):
    calls = []

    def chooser(candidate, remaining):
        calls.append(candidate["name"])
        return answer

    assert selection.choose(INVENTORY, "ask", chooser, interactive=True) == expected
    assert calls == ["geno-dev"]


def test_choose_cancel_stops_without_a_partial_selection():
    with pytest.raises(selection.SelectionError, match="cancelled"):
        selection.choose(
            INVENTORY,
            "ask",
            lambda _candidate, _remaining: "cancel",
            interactive=True,
        )


@pytest.mark.parametrize(
    "policy, expected",
    [
        (
            "active",
            {
                "geno-dev": "active",
                "geno-stable": "stable",
                "geno-tt": "active",
            },
        ),
        (
            "stable",
            {
                "geno-dev": "stable",
                "geno-stable": "stable",
                "geno-tt": "stable",
            },
        ),
    ],
)
def test_choose_noninteractive_policies_cover_mixed_eligibility(policy, expected):
    assert selection.choose(
        INVENTORY,
        policy,
        lambda *_args: pytest.fail("policy must not prompt"),
        interactive=False,
    ) == expected


def test_choose_ask_refuses_to_guess_without_a_tty():
    with pytest.raises(selection.SelectionError, match="--dev-source stable|active"):
        selection.choose(
            INVENTORY,
            "ask",
            lambda *_args: pytest.fail("non-TTY ask must not prompt"),
            interactive=False,
        )


def test_inventory_includes_stable_fallback_and_active_snapshot_size(monkeypatch):
    lock = {
        "version": 1,
        "machine": "laptop",
        "generated": "now",
        "skillsets": {
            "geno-dev": {
                "url": "https://example.test/geno-dev.git",
                "branch": "main",
                "sha": "1" * 40,
                "version": "0.9.0",
            }
        },
        "config": {},
    }
    payload = {
        "version": 1,
        "machine": "laptop",
        "captured": "now",
        "source": "/tmp/geno-dev",
        "project_version": "1.0.0",
        "branch": "feature",
        "commit": "2" * 40,
        "origin": None,
        "dirty": {"cached": True, "worktree": False, "untracked": 1},
        "fingerprint": "a" * 64,
        "artifacts": {
            "bundle": "AAAA",
            "cached_diff": "BBBB",
            "worktree_diff": "CCCC",
            "untracked_tar": "DDDD",
        },
    }
    monkeypatch.setattr(selection.lockfile, "build_lockfile", lambda: lock)
    monkeypatch.setattr(
        selection.dev,
        "selection_details",
        lambda _name: {
            "active": {"mode": "dev", "source": "/tmp/geno-dev"},
            "stable": {"mode": "stable"},
            "rollback": False,
        },
    )
    monkeypatch.setattr(selection.snapshot, "capture", lambda *_args, **_kw: payload)

    value = selection.inventory()

    candidate = value["skillsets"]["geno-dev"]
    assert value["lockfile"] == lock
    assert candidate["stable"] == lock["skillsets"]["geno-dev"]
    assert candidate["active"]["fingerprint"] == "a" * 64
    assert candidate["active"]["transfer_size"] == 16
    assert "artifacts" not in candidate["active"]


def test_parse_inventory_round_trips_json_and_rejects_old_remote_protocol():
    value = {
        **INVENTORY,
        "lockfile": {
            "version": 1,
            "machine": "laptop",
            "generated": "now",
            "skillsets": {
                name: {
                    "url": f"https://example.test/{name}.git",
                    "branch": "main",
                    "sha": name,
                    "version": item["stable"]["version"],
                }
                for name, item in INVENTORY["skillsets"].items()
            },
            "config": {},
        },
    }
    assert selection.parse(value) == value
    with pytest.raises(selection.SelectionError, match="protocol"):
        selection.parse(
            {
                "version": 1,
                "machine": "old-remote",
                "generated": "now",
                "skillsets": {},
                "config": {},
            }
        )
