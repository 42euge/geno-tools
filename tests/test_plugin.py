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
        path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
        assert path.exists(), ".claude-plugin/marketplace.json missing"
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
        path = REPO_ROOT / ".claude-plugin" / "plugin.json"
        assert path.exists(), ".claude-plugin/plugin.json missing"
        return json.loads(path.read_text())

    def test_has_name(self, manifest):
        assert manifest.get("name") == "geno-tools"

    def test_has_skills_path(self, manifest):
        skills_path = manifest.get("skills")
        assert skills_path, "plugin.json must declare a skills path"

    def test_skills_dir_exists(self, manifest):
        skills_path = manifest.get("skills", "./skills")
        skills_dir = REPO_ROOT / skills_path
        assert skills_dir.is_dir(), f"skills dir {skills_dir} does not exist"

    def test_version_matches_marketplace(self, manifest):
        mp = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
        mp_version = mp["plugins"][0]["version"]
        assert manifest.get("version") == mp_version, "version mismatch between plugin.json and marketplace.json"


class TestSkills:
    @pytest.fixture()
    def skill_dirs(self):
        skills_dir = REPO_ROOT / "skills"
        return [d for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]

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

    def test_frontmatter_name_starts_with_geno_prefix(self, skill_dirs):
        """Frontmatter `name:` is the source of truth and always carries
        the fully qualified `geno-{...}` form regardless of whether the
        directory tree is flat or nested. See
        docs/skillsets/upstream-conventions.md § Nested skill trees.
        """
        for skill_dir in skill_dirs:
            text = (skill_dir / "SKILL.md").read_text()
            end = text.index("---", 3)
            fm = yaml.safe_load(text[3:end])
            assert fm["name"].startswith("geno-"), (
                f"{skill_dir.name}: frontmatter name '{fm['name']}' "
                f"must start with 'geno-' prefix"
            )

    def test_umbrella_mirror_has_full_prefixed_name(self):
        """The skillset-root umbrella mirror at skills/geno-tools/SKILL.md
        is the one place where the directory name keeps the full prefixed
        form (matches the repo name).
        """
        umbrella = REPO_ROOT / "skills" / "geno-tools" / "SKILL.md"
        assert umbrella.exists(), "skills/geno-tools/SKILL.md (umbrella mirror) missing"
        text = umbrella.read_text()
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm["name"] == "geno-tools", (
            f"umbrella mirror frontmatter name must be 'geno-tools', got '{fm['name']}'"
        )

    def test_non_umbrella_dirs_use_bare_nouns(self, skill_dirs):
        """Per the nested-skill-tree convention, non-umbrella directories
        under skills/ use bare nouns (no `geno-` prefix). Only the
        skillset-root umbrella mirror (`skills/geno-tools/`) keeps the
        full prefixed name.
        """
        for skill_dir in skill_dirs:
            if skill_dir.name == "geno-tools":
                continue  # the umbrella mirror exception
            assert not skill_dir.name.startswith("geno-"), (
                f"non-umbrella dir '{skill_dir.name}' must use a bare "
                f"noun, not a 'geno-' prefix"
            )

    def test_umbrella_skill_exists(self, skill_dirs):
        names = {d.name for d in skill_dirs}
        assert "geno-tools" in names, "umbrella skill 'geno-tools' missing"


class TestHooks:
    def test_hooks_json_exists(self):
        path = REPO_ROOT / "hooks" / "hooks.json"
        assert path.exists(), "hooks/hooks.json missing"

    def test_hooks_json_valid(self):
        path = REPO_ROOT / "hooks" / "hooks.json"
        data = json.loads(path.read_text())
        assert "hooks" in data

    def test_session_start_hook_script_exists(self):
        path = REPO_ROOT / "hooks" / "hooks.json"
        data = json.loads(path.read_text())
        for hook in data["hooks"].get("SessionStart", []):
            for h in hook.get("hooks", []):
                cmd = h.get("command", "")
                script = cmd.replace("${CLAUDE_PLUGIN_ROOT}/", "")
                script_path = REPO_ROOT / script
                assert script_path.exists(), f"hook script not found: {script_path}"


class TestConfigDefaults:
    def test_defaults_yaml_exists(self):
        path = REPO_ROOT / "config" / "defaults.yaml"
        assert path.exists()

    def test_defaults_yaml_valid(self):
        path = REPO_ROOT / "config" / "defaults.yaml"
        data = yaml.safe_load(path.read_text())
        assert "aliases" in data
        assert "discovery" in data

    def test_init_script_seeds_config(self):
        script = REPO_ROOT / "scripts" / "init-geno-dir.sh"
        assert script.exists()
        text = script.read_text()
        assert "config.yaml" in text
        assert "defaults.yaml" in text
