"""Tests for the root agent instruction files.

GENO.md is the single source of agent instructions. CLAUDE.md, AGENTS.md, and
GEMINI.md are thin pointers to it — they must contain only the import directive
for their respective agent convention, nothing else.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

POINTER_FILES = {
    "CLAUDE.md": "@./GENO.md",
    "GEMINI.md": "@./GENO.md",
    "AGENTS.md": "@import GENO.md",
}


def test_geno_md_exists_and_nonempty():
    path = REPO_ROOT / "GENO.md"
    assert path.is_file(), "GENO.md is missing from the repo root"
    assert path.read_bytes().strip(), "GENO.md is empty"


def test_geno_md_has_conventions_section():
    text = (REPO_ROOT / "GENO.md").read_text()
    assert any(
        line.lower().startswith("## conventions") or "# conventions" in line.lower()
        for line in text.splitlines()
    ), "GENO.md must contain a '## Conventions' section"


@pytest.mark.parametrize("filename,expected", POINTER_FILES.items())
def test_pointer_file_is_thin(filename, expected):
    path = REPO_ROOT / filename
    assert path.is_file(), f"{filename} is missing from the repo root"
    content = path.read_text().strip()
    assert content == expected, (
        f"{filename} must contain only '{expected}' — no other content. "
        f"Got: {content!r}"
    )
