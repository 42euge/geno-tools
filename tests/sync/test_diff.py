import pytest

from geno_tools.sync import diff


ENTRY = {
    "url": "https://example.test/geno-dev.git",
    "branch": "main",
    "sha": "abc123",
    "version": "1.0.0",
}


def lock(*, skillsets=None, config=None):
    return {
        "version": 1,
        "machine": "fixture",
        "generated": "now",
        "skillsets": skillsets or {},
        "config": config or {},
    }


@pytest.mark.parametrize(
    ("here", "source", "state"),
    [
        ({}, {"geno-dev": ENTRY}, "missing-here"),
        ({"geno-dev": ENTRY}, {}, "extra-here"),
        (
            {"geno-dev": ENTRY},
            {"geno-dev": {**ENTRY, "sha": "other"}},
            "version-skew",
        ),
        ({"geno-dev": ENTRY}, {"geno-dev": ENTRY}, "in-sync"),
    ],
)
def test_compare_classifies_skillset_state(here, source, state):
    value = diff.compare(lock(skillsets=here), lock(skillsets=source))
    assert [(item.name, item.state) for item in value.skillsets] == [
        ("geno-dev", state)
    ]


@pytest.mark.parametrize(
    "field, value",
    [
        ("url", "https://mirror.test/geno-dev.git"),
        ("branch", "stable"),
        ("version", "2.0.0"),
    ],
)
def test_compare_reports_metadata_differences_as_version_skew(field, value):
    source = {**ENTRY, field: value}
    result = diff.compare(
        lock(skillsets={"geno-dev": ENTRY}),
        lock(skillsets={"geno-dev": source}),
    )
    assert result.skillsets[0].state == "version-skew"


def test_compare_orders_skillsets_by_name():
    result = diff.compare(
        lock(skillsets={"geno-z": ENTRY}),
        lock(skillsets={"geno-b": ENTRY, "geno-a": ENTRY}),
    )
    assert [item.name for item in result.skillsets] == ["geno-a", "geno-b", "geno-z"]


def test_compare_reports_nested_config_changes_by_dot_path():
    result = diff.compare(
        lock(config={"aliases": {"command_prefix": "old"}, "mode": "user"}),
        lock(
            config={
                "aliases": {"command_prefix": "gt"},
                "discovery": {"sources": []},
                "mode": "user",
            }
        ),
    )

    assert result.config == (
        diff.ConfigDelta("aliases.command_prefix", "old", "gt"),
        diff.ConfigDelta("discovery.sources", None, []),
    )


def test_compare_omits_equal_config():
    result = diff.compare(lock(config={"mode": "user"}), lock(config={"mode": "user"}))
    assert result.config == ()


def test_compare_distinguishes_null_config_from_absent_config():
    result = diff.compare(lock(config={"mode": None}), lock(config={}))
    assert result.config == (diff.ConfigDelta("mode", None, None),)
