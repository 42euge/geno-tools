"""Tests for the root agent instruction files.

The repo uses a GENO.md single-source-of-truth pattern: all agent instructions
live in GENO.md; per-agent files are thin pointers that import it.

- CLAUDE.md  → @./GENO.md
- AGENTS.md  → @import GENO.md
- GEMINI.md  → @./GENO.md
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_geno_md_exists_and_nonempty():
    path = REPO_ROOT / "GENO.md"
    assert path.is_file(), "GENO.md is missing from the repo root"
    content = path.read_text()
    assert content.strip(), "GENO.md is empty"
    assert any(
        h.lower() in content.lower()
        for h in ["conventions", "convention"]
    ), "GENO.md must contain a Conventions section"


@pytest.mark.parametrize(
    "name,expected",
    [
        ("CLAUDE.md", "@./GENO.md"),
        ("AGENTS.md", "@import GENO.md"),
        ("GEMINI.md", "@./GENO.md"),
    ],
)
def test_agent_pointer_files(name, expected):
    path = REPO_ROOT / name
    assert path.is_file(), f"{name} is missing from the repo root"
    content = path.read_text().strip()
    assert content == expected, (
        f"{name} must contain only '{expected}' (GENO.md pointer). "
        f"Got: {content!r}"
    )
