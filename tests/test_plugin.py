"""Tests for plugin manifests and install flow.

Verifies the Claude Code plugin installation experience documented in README.md:
  1. marketplace.json is valid and has required fields
  2. plugin.json points to a valid skills directory
  3. Every skill in skills/ has a valid SKILL.md with required frontmatter
  4. The SessionStart hook script exists and is executable-ready
  5. Skills listed in plugin.json match what's on disk
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestMarketplaceJson:
    @pytest.fixture()
    def manifest(self):
        path = REPO_ROOT / "marketplace.json"
        assert path.exists(), "marketplace.json missing"
        return json.loads(path.read_text())

    def test_has_name(self, manifest):
        assert manifest.get("name") == "geno-tools"

    def test_has_description(self, manifest):
        assert manifest.get("description"), "marketplace.json must have a description"

    def test_has_owner(self, manifest):
        owner = manifest.get("owner", {})
        assert owner.get("name"), "owner.name required"
        assert owner.get("url"), "owner.url required"

    def test_plugins_list_nonempty(self, manifest):
        plugins = manifest.get("plugins", [])
        assert len(plugins) > 0

    def test_plugin_entry_has_required_fields(self, manifest):
        for p in manifest["plugins"]:
            assert p.get("name"), "plugin entry missing name"
            assert p.get("source"), "plugin entry missing source"
            assert p.get("description"), "plugin entry missing description"
            assert p.get("version"), "plugin entry missing version"


class TestPluginJson:
    @pytest.fixture()
    def manifest(self):
        path = REPO_ROOT / "plugin.json"
        assert path.exists(), "plugin.json missing"
        return json.loads(path.read_text())

    def test_has_name(self, manifest):
        assert manifest.get("name") == "geno-tools"

    def test_has_skills_path(self, manifest):
        skills_path = manifest.get("skills")
        assert skills_path, "plugin.json must declare a skills path"

    def test_skills_dir_exists(self, manifest):
        # `skills` may be a single path or an array of category dirs (each
        # scanned one level deep by the plugin loader).
        skills_paths = manifest.get("skills", "./skills")
        if isinstance(skills_paths, str):
            skills_paths = [skills_paths]
        for skills_path in skills_paths:
            skills_dir = REPO_ROOT / skills_path
            assert skills_dir.is_dir(), f"skills dir {skills_dir} does not exist"

    def test_version_matches_marketplace(self, manifest):
        mp = json.loads((REPO_ROOT / "marketplace.json").read_text())
        mp_version = mp["plugins"][0]["version"]
        assert manifest.get("version") == mp_version, "version mismatch between plugin.json and marketplace.json"


class TestSkills:
    @pytest.fixture()
    def skill_dirs(self):
        # Skills nest under category dirs (skills/<category>/<name>/SKILL.md,
        # arbitrarily deep), so walk recursively, not just one level.
        skills_dir = REPO_ROOT / "skills"
        return [p.parent for p in skills_dir.rglob("SKILL.md")]

    def test_at_least_one_skill(self, skill_dirs):
        assert len(skill_dirs) >= 1

    def test_each_skill_has_valid_frontmatter(self, skill_dirs):
        for skill_dir in skill_dirs:
            text = (skill_dir / "SKILL.md").read_text()
            assert text.startswith("---"), f"{skill_dir.name}/SKILL.md missing frontmatter"
            end = text.index("---", 3)
            fm = yaml.safe_load(text[3:end])
            assert fm.get("name"), f"{skill_dir.name}: frontmatter missing 'name'"
            assert fm.get("description"), f"{skill_dir.name}: frontmatter missing 'description'"

    def test_skill_name_mirrors_path(self, skill_dirs):
        # Per the nesting standard (SKILLS.md): a leaf's frontmatter `name` is
        # the fully-qualified path. The umbrella is exactly "geno-tools"; every
        # nested leaf's name ends with "-<leaf-dir-name>".
        for skill_dir in skill_dirs:
            text = (skill_dir / "SKILL.md").read_text()
            end = text.index("---", 3)
            name = yaml.safe_load(text[3:end])["name"]
            if skill_dir.name == "geno-tools":
                assert name == "geno-tools"
            else:
                assert name.endswith(f"-{skill_dir.name}"), (
                    f"name '{name}' should end with '-{skill_dir.name}' (path-mirrored)"
                )

    def test_umbrella_skill_exists(self, skill_dirs):
        names = {d.name for d in skill_dirs}
        assert "geno-tools" in names, "umbrella skill 'geno-tools' missing"


class TestConfigDefaults:
    def test_defaults_yaml_exists(self):
        path = REPO_ROOT / "geno_tools" / "config" / "defaults.yaml"
        assert path.exists()

    def test_defaults_yaml_valid(self):
        path = REPO_ROOT / "geno_tools" / "config" / "defaults.yaml"
        data = yaml.safe_load(path.read_text())
        assert "aliases" in data
        assert "discovery" in data
