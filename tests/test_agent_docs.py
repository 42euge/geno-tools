"""Tests for the root agent instruction file.

The repo keeps a single instruction file: AGENTS.md. Every agent we target
reads it — Claude Code, Codex, Gemini CLI, Antigravity — so the older
per-agent pointer files (GENO.md, CLAUDE.md, GEMINI.md) are retired.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_agents_md_exists_and_nonempty():
    path = REPO_ROOT / "AGENTS.md"
    assert path.is_file(), "AGENTS.md is missing from the repo root"
    content = path.read_text()
    assert content.strip(), "AGENTS.md is empty"
    assert any(
        h.lower() in content.lower()
        for h in ["conventions", "convention"]
    ), "AGENTS.md must contain a Conventions section"


def test_agents_md_is_not_a_pointer():
    """AGENTS.md must hold the real content, not import it from elsewhere."""
    body = (REPO_ROOT / "AGENTS.md").read_text().strip()
    assert not body.startswith("@"), (
        "AGENTS.md must contain the instructions themselves, not an @import "
        f"pointer. Got: {body.splitlines()[0]!r}"
    )
    assert len(body.splitlines()) > 20, (
        "AGENTS.md looks too short to be the single source of truth"
    )


@pytest.mark.parametrize("name", ["GENO.md", "CLAUDE.md", "GEMINI.md"])
def test_retired_pointer_files_absent(name):
    path = REPO_ROOT / name
    assert not path.exists(), (
        f"{name} is retired — all agent instructions live in AGENTS.md. "
        "Delete it rather than reintroducing a second source of truth."
    )
