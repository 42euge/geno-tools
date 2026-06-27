"""Tests for the registry — a discovery cache, no hardcoded list, no gh.

The registry reads ~/.geno/registry.json (written by the discover skill). It
ships no fallback data and never shells out. These tests point CACHE_FILE at a
temp file and exercise read/write/resolve.
"""

import json

import pytest

from geno_tools import registry


@pytest.fixture(autouse=True)
def _temp_cache(tmp_path, monkeypatch):
    """Point the registry cache at a temp file; reset the in-process cache."""
    cache = tmp_path / "registry.json"
    monkeypatch.setattr(registry, "CACHE_FILE", cache)
    registry._cache = None
    yield cache
    registry._cache = None


def _seed(cache, mapping):
    cache.write_text(json.dumps(mapping, indent=2))
    registry._cache = None


class TestEmptyRegistry:
    def test_no_cache_is_empty(self):
        # No discovery has run → empty, no hardcoded fallback.
        assert registry.available() == {}

    def test_resolve_returns_none_when_empty(self):
        assert registry.resolve("geno-loops") is None
        assert registry.resolve("loops") is None

    def test_no_fallback_attribute(self):
        # The hardcoded fallback dict is gone.
        assert not hasattr(registry, "_FALLBACK")


class TestCacheRoundTrip:
    def test_write_then_available(self):
        registry.write_cache({
            "geno-loops": {"url": "https://github.com/42euge/geno-loops.git",
                           "source": "github:42euge"},
        })
        repos = registry.available()
        assert repos == {"geno-loops": "https://github.com/42euge/geno-loops.git"}

    def test_accepts_plain_string_values(self, _temp_cache):
        _seed(_temp_cache, {"geno-dev": "https://github.com/42euge/geno-dev.git"})
        assert registry.available()["geno-dev"].endswith("geno-dev.git")

    def test_malformed_cache_is_empty(self, _temp_cache):
        _temp_cache.write_text("{ not json")
        registry._cache = None
        assert registry.available() == {}


class TestResolve:
    @pytest.fixture(autouse=True)
    def _seeded(self):
        registry.write_cache({
            "geno-agents": {"url": "https://github.com/42euge/geno-agents.git"},
            "geno-loops": {"url": "https://github.com/42euge/geno-loops.git"},
        })

    def test_resolve_full_name(self):
        assert registry.resolve("geno-loops") == "https://github.com/42euge/geno-loops.git"

    def test_resolve_bare_slug(self):
        # backwards-compat: bare slug resolves to geno-<slug>
        assert registry.resolve("agents") == "https://github.com/42euge/geno-agents.git"

    def test_resolve_unknown_full_returns_none(self):
        assert registry.resolve("geno-nonexistent") is None

    def test_resolve_unknown_bare_returns_none(self):
        assert registry.resolve("nonexistent") is None
