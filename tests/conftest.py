"""Shared fixtures for geno-tools tests."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture()
def tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect all geno-tools state to a temp directory."""
    root = tmp_path / ".geno-tools"
    root.mkdir()
    monkeypatch.setattr("geno_tools.paths.ROOT", root)
    monkeypatch.setattr("geno_tools.paths.STATE_HASH", root / ".state-hash")
    monkeypatch.setattr("geno_tools.paths.BOOTSTRAP", root / "geno-bootstrap")
    return root


@pytest.fixture()
def tmp_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect config dir to a temp directory."""
    cfg_dir = tmp_path / ".geno"
    cfg_dir.mkdir()
    monkeypatch.setattr("geno_tools.config.CONFIG_DIR", cfg_dir)
    monkeypatch.setattr("geno_tools.config.CONFIG_FILE", cfg_dir / "config.yaml")
    return cfg_dir


@pytest.fixture()
def fake_skillset(tmp_root: Path):
    """Create a minimal fake skillset on disk with umbrella + sub-skills."""

    def _make(
        name: str = "geno-fake",
        sub_skills: list[str] | None = None,
        has_pyproject: bool = False,
        has_manifest: bool = False,
        requires: list[str] | None = None,
    ) -> Path:
        root = tmp_root / name
        root.mkdir(parents=True, exist_ok=True)

        main = root / "main"
        main.mkdir()

        # umbrella SKILL.md
        (main / "SKILL.md").write_text(textwrap.dedent(f"""\
            ---
            name: {name}
            description: fake umbrella skill
            ---
            # {name}
        """))

        # sub-skills
        if sub_skills:
            skills_dir = main / "skills"
            skills_dir.mkdir()
            for sub in sub_skills:
                sd = skills_dir / sub
                sd.mkdir()
                (sd / "SKILL.md").write_text(textwrap.dedent(f"""\
                    ---
                    name: {sub}
                    description: fake sub-skill {sub}
                    ---
                    # {sub}
                """))

        if has_pyproject:
            (main / "pyproject.toml").write_text(textwrap.dedent(f"""\
                [project]
                name = "{name}"
                version = "0.1.0"
                dependencies = []

                [project.scripts]
                {name} = "{name.replace('-', '_')}.cli:main"
            """))

        if has_manifest and requires:
            import yaml
            (main / "genotools.yaml").write_text(
                yaml.safe_dump({"requires": requires})
            )

        # active -> main
        (root / "active").symlink_to("main")

        # fake .git dir
        (root / ".git").mkdir()

        return root

    return _make


@pytest.fixture()
def no_subprocess(monkeypatch: pytest.MonkeyPatch):
    """Block real subprocess calls — tests must mock explicitly."""
    def _blocked(*a, **kw):
        raise RuntimeError(f"subprocess blocked in test: {a}")
    monkeypatch.setattr("subprocess.check_call", _blocked)
    monkeypatch.setattr("subprocess.check_output", _blocked)
    monkeypatch.setattr("subprocess.run", _blocked)


@pytest.fixture()
def no_registry_network(monkeypatch: pytest.MonkeyPatch):
    """Prevent registry from hitting the network; use fallback."""
    monkeypatch.setattr("geno_tools.registry._cache", None)
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **kw: type("R", (), {"returncode": 1, "stdout": "", "stderr": ""})())
