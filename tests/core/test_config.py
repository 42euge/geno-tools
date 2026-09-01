"""Tests for core config loading and defaults."""

import yaml

from geno_tools.core import config


class TestEnsureDir:
    def test_creates_geno_dir(self, tmp_config):
        import shutil
        shutil.rmtree(tmp_config)
        assert not tmp_config.exists()
        config.ensure_dir()
        assert tmp_config.exists()

    def test_seeds_config_yaml(self, tmp_config):
        cfg = tmp_config / "config.yaml"
        if cfg.exists():
            cfg.unlink()
        config.ensure_dir()
        assert cfg.exists()
        data = yaml.safe_load(cfg.read_text())
        assert "aliases" in data
        assert "discovery" in data


class TestLoad:
    def test_defaults_when_no_file(self, tmp_config):
        data = config.load()
        assert data["aliases"]["command_prefix"] == "gt"
        assert isinstance(data["discovery"]["sources"], list)

    def test_user_override_merged(self, tmp_config):
        cfg = tmp_config / "config.yaml"
        cfg.write_text(yaml.safe_dump({
            "aliases": {"command_prefix": "myprefix"},
        }))
        data = config.load()
        assert data["aliases"]["command_prefix"] == "myprefix"
        assert "discovery" in data


class TestCommandPrefix:
    def test_default(self, tmp_config):
        assert config.command_prefix() == "gt"

    def test_custom(self, tmp_config):
        cfg = tmp_config / "config.yaml"
        cfg.write_text(yaml.safe_dump({"aliases": {"command_prefix": "g"}}))
        assert config.command_prefix() == "g"
