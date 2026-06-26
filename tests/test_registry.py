"""Tests for registry resolution — names, fallback, backwards compat."""

import json
from unittest.mock import MagicMock

import pytest

from geno_tools import registry


@pytest.fixture(autouse=True)
def _reset_cache():
    registry._cache = None
    yield
    registry._cache = None


class TestFallback:
    def test_fallback_used_when_gh_unavailable(self, monkeypatch):
        monkeypatch.setattr("subprocess.run",
                            lambda *a, **kw: MagicMock(returncode=1, stdout="", stderr=""))
        repos = registry.available()
        assert "geno-agents" in repos
        assert "geno-dev" in repos

    def test_fallback_keys_have_geno_prefix(self, monkeypatch):
        monkeypatch.setattr("subprocess.run",
                            lambda *a, **kw: MagicMock(returncode=1))
        for name in registry.available():
            assert name.startswith("geno-"), f"fallback key {name!r} missing geno- prefix"

    def test_fallback_values_are_git_urls(self, monkeypatch):
        monkeypatch.setattr("subprocess.run",
                            lambda *a, **kw: MagicMock(returncode=1))
        for url in registry.available().values():
            assert url.endswith(".git"), f"url {url!r} should end with .git"


class TestDiscover:
    def test_discover_parses_gh_output(self, monkeypatch):
        fake_repos = [
            {"name": "geno-dev", "url": "https://github.com/42euge/geno-dev"},
            {"name": "geno-iso", "url": "https://github.com/42euge/geno-iso"},
            {"name": "not-geno", "url": "https://github.com/42euge/not-geno"},
            {"name": "geno-tools", "url": "https://github.com/42euge/geno-tools"},
        ]
        result = MagicMock(returncode=0, stdout=json.dumps(fake_repos))
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: result)

        repos = registry.available()
        assert "geno-dev" in repos
        assert "geno-iso" in repos
        assert "not-geno" not in repos
        assert "geno-tools" not in repos  # EXCLUDE

    def test_discover_appends_dot_git(self, monkeypatch):
        fake = [{"name": "geno-dev", "url": "https://github.com/42euge/geno-dev"}]
        result = MagicMock(returncode=0, stdout=json.dumps(fake))
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: result)

        repos = registry.available()
        assert repos["geno-dev"].endswith(".git")


class TestResolve:
    def test_resolve_full_name(self, monkeypatch):
        monkeypatch.setattr("subprocess.run",
                            lambda *a, **kw: MagicMock(returncode=1))
        url = registry.resolve("geno-agents")
        assert url is not None
        assert "geno-agents" in url

    def test_resolve_bare_slug(self, monkeypatch):
        monkeypatch.setattr("subprocess.run",
                            lambda *a, **kw: MagicMock(returncode=1))
        url = registry.resolve("agents")
        assert url is not None
        assert "geno-agents" in url

    def test_resolve_unknown_returns_none(self, monkeypatch):
        monkeypatch.setattr("subprocess.run",
                            lambda *a, **kw: MagicMock(returncode=1))
        assert registry.resolve("geno-nonexistent") is None

    def test_resolve_bare_unknown_returns_none(self, monkeypatch):
        monkeypatch.setattr("subprocess.run",
                            lambda *a, **kw: MagicMock(returncode=1))
        assert registry.resolve("nonexistent") is None
