"""Tests for the profile store + resolver."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from geno_tools import paths, profiles


@pytest.fixture()
def tmp_profiles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect PROFILES_DIR to a temp dir."""
    d = tmp_path / "profiles"
    d.mkdir()
    monkeypatch.setattr(paths, "PROFILES_DIR", d)
    return d


def _write_profile(d: Path, name: str, body: dict) -> None:
    (d / f"{name}.yaml").write_text(yaml.safe_dump(body))


class TestListProfiles:
    def test_builtins_present(self, tmp_profiles):
        names = profiles.list_profiles()
        for b in ("bare", "base", "standard", "full"):
            assert b in names

    def test_includes_on_disk(self, tmp_profiles):
        _write_profile(tmp_profiles, "eng", {"agents": ["claude-code"]})
        assert "eng" in profiles.list_profiles()


class TestLoad:
    def test_builtin_lowered_to_schema(self, tmp_profiles):
        p = profiles.load("base")
        skill_names = [s["name"] for s in p["skills"]]
        assert "geno-dev" in skill_names
        assert all(s["variant"] == "main" for s in p["skills"])
        assert set(p["agents"]) == set(profiles.KNOWN_AGENTS)

    def test_bare_has_no_skills(self, tmp_profiles):
        assert profiles.load("bare")["skills"] == []

    def test_file_overrides_builtin(self, tmp_profiles):
        _write_profile(tmp_profiles, "base", {
            "agents": ["codex"], "skills": ["geno-x"]})
        p = profiles.load("base")
        assert p["agents"] == ["codex"]
        assert [s["name"] for s in p["skills"]] == ["geno-x"]

    def test_string_skill_entry(self, tmp_profiles):
        _write_profile(tmp_profiles, "s", {"skills": ["geno-a"]})
        p = profiles.load("s")
        assert p["skills"][0] == {"name": "geno-a", "variant": "main", "version": None}

    def test_dict_skill_entry_with_variant(self, tmp_profiles):
        _write_profile(tmp_profiles, "s", {
            "skills": [{"name": "geno-a", "variant": "exp"}]})
        p = profiles.load("s")
        assert p["skills"][0]["variant"] == "exp"

    def test_string_agents_coerced(self, tmp_profiles):
        _write_profile(tmp_profiles, "s", {"agents": "claude-code"})
        assert profiles.load("s")["agents"] == ["claude-code"]

    def test_unknown_profile_raises(self, tmp_profiles):
        with pytest.raises(profiles.ProfileError):
            profiles.load("does-not-exist")

    def test_malformed_yaml_raises(self, tmp_profiles):
        (tmp_profiles / "bad.yaml").write_text("::: not yaml :::\n- [")
        with pytest.raises(profiles.ProfileError):
            profiles.load("bad")

    def test_bad_skill_entry_raises(self, tmp_profiles):
        _write_profile(tmp_profiles, "s", {"skills": [123]})
        with pytest.raises(profiles.ProfileError):
            profiles.load("s")


class TestResolve:
    def test_missing_skillset_collected(self, tmp_profiles, tmp_root):
        _write_profile(tmp_profiles, "s", {"skills": ["geno-absent"]})
        r = profiles.resolve("s")
        assert "geno-absent" in r["missing"]
        assert r["skills"] == []

    def test_installed_skill_maps_to_worktree(self, tmp_profiles, tmp_root):
        # fake an installed skillset root + variant worktree
        root = paths.skillset_root("geno-x")
        (root / ".worktrees" / "exp").mkdir(parents=True)
        (root / "main").mkdir()
        _write_profile(tmp_profiles, "s", {
            "skills": [{"name": "geno-x", "variant": "exp"}]})
        r = profiles.resolve("s")
        assert r["missing"] == []
        s = r["skills"][0]
        assert s["name"] == "geno-x"
        assert s["variant"] == "exp"
        assert s["worktree"] == paths.skillset_worktree("geno-x", "exp")
        assert s["worktree_exists"] is True

    def test_unknown_agent_raises(self, tmp_profiles):
        _write_profile(tmp_profiles, "s", {"agents": ["not-an-agent"]})
        with pytest.raises(profiles.ProfileError):
            profiles.resolve("s")

    def test_mcp_names_passthrough(self, tmp_profiles):
        _write_profile(tmp_profiles, "s", {"mcp": ["core", "gitlab"]})
        assert profiles.resolve("s")["mcp"] == ["core", "gitlab"]

    def test_autonomy_override(self, tmp_profiles):
        _write_profile(tmp_profiles, "s", {"autonomy": 0})
        assert profiles.resolve("s")["autonomy"] == 0
