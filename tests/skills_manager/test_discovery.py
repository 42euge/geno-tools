"""Tests for skills-manager discovery providers."""

import json
from unittest.mock import MagicMock

import pytest

from geno_tools.skills_manager import discovery


class TestProviders:
    def test_github_registered(self):
        assert "github" in discovery.iter_kinds()

    def test_gitlab_registered(self):
        assert "gitlab" in discovery.iter_kinds()

    def test_bitbucket_registered(self):
        assert "bitbucket" in discovery.iter_kinds()

    def test_gitea_registered(self):
        assert "gitea" in discovery.iter_kinds()


class TestSources:
    def test_loads_from_config(self, tmp_config):
        import yaml
        (tmp_config / "config.yaml").write_text(yaml.safe_dump({
            "discovery": {
                "sources": [{"kind": "github", "org": "test-org"}],
            },
        }))
        srcs = discovery.sources()
        assert len(srcs) == 1
        assert srcs[0]["org"] == "test-org"

    def test_empty_when_config_has_no_sources(self, tmp_config):
        import yaml
        (tmp_config / "config.yaml").write_text(yaml.safe_dump({"discovery": {"sources": []}}))
        srcs = discovery.sources()
        assert srcs == []


class TestGitHubProvider:
    def test_parses_repos(self, monkeypatch):
        fake = [
            {"name": "geno-dev", "url": "https://github.com/test/geno-dev", "sshUrl": ""},
            {"name": "geno-iso", "url": "https://github.com/test/geno-iso", "sshUrl": ""},
            {"name": "not-geno", "url": "https://github.com/test/not-geno", "sshUrl": ""},
        ]

        def fake_run(cmd, **kw):
            if "api" in cmd:
                return MagicMock(returncode=0)
            return MagicMock(returncode=0, stdout=json.dumps(fake))

        monkeypatch.setattr("subprocess.run", fake_run)

        results = discovery._github({"org": "test", "prefix": "geno-"})
        names = {c.name for c in results}
        assert "geno-dev" in names
        assert "geno-iso" in names
        assert "not-geno" not in names

    def test_gh_failure_returns_empty(self, monkeypatch):
        monkeypatch.setattr("subprocess.run",
                            lambda *a, **kw: MagicMock(returncode=1, stdout="", stderr=""))
        results = discovery._github({"org": "test"})
        assert results == []

    def test_no_org_returns_empty(self, monkeypatch):
        results = discovery._github({})
        assert results == []

    def test_candidates_by_name_filters(self, monkeypatch):
        c1 = discovery.Candidate("geno-a", "url-a", "github:test", has_skill_md=True)
        c2 = discovery.Candidate("geno-b", "url-b", "github:test", has_skill_md=False)
        monkeypatch.setattr("geno_tools.skills_manager.discovery.candidates", lambda: [c1, c2])
        by_name = discovery.candidates_by_name()
        assert "geno-a" in by_name
        assert "geno-b" not in by_name
