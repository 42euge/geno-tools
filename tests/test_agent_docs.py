"""Tests for the root agent instruction files.

The repo keeps GENO.md as the single source of agent instructions. Per-agent
pointer files resolve to it at load time:
  - CLAUDE.md  → "@./GENO.md"      (Claude Code pointer syntax)
  - AGENTS.md  → "@import GENO.md" (Codex / OpenCode pointer syntax)

Adding GEMINI.md with "@./GENO.md" is recommended but not yet required.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_geno_md_exists_and_nonempty():
    path = REPO_ROOT / "GENO.md"
    assert path.is_file(), "GENO.md is missing from the repo root"
    assert path.read_bytes().strip(), "GENO.md is empty"


@pytest.mark.parametrize("name,expected", [
    ("CLAUDE.md", "@./GENO.md"),
    ("AGENTS.md", "@import GENO.md"),
])
def test_agent_pointer_files(name, expected):
    path = REPO_ROOT / name
    assert path.is_file(), f"{name} is missing from the repo root"
    content = path.read_text().strip()
    assert content == expected, (
        f"{name} must contain only '{expected}' (a pointer to GENO.md). "
        f"Got: {content!r}"
    )
