"""Tests for the root agent instruction files.

The repo keeps exactly two agent-instruction files at the root — AGENTS.md
(read by Codex, Cursor, OpenCode, …) and CLAUDE.md (read by Claude Code).
They MUST be byte-for-byte identical so every agent sees the same guidance.
Edit one, copy it to the other.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_DOCS = ("AGENTS.md", "CLAUDE.md")


@pytest.mark.parametrize("name", AGENT_DOCS)
def test_agent_doc_exists_and_nonempty(name):
    path = REPO_ROOT / name
    assert path.is_file(), f"{name} is missing from the repo root"
    assert path.read_bytes().strip(), f"{name} is empty"


def test_agent_docs_are_identical():
    contents = {name: (REPO_ROOT / name).read_bytes() for name in AGENT_DOCS}
    a, c = contents["AGENTS.md"], contents["CLAUDE.md"]
    assert a == c, (
        "AGENTS.md and CLAUDE.md must be byte-for-byte identical. "
        "Edit one and copy it to the other.\n"
        f"AGENTS.md: {len(a)} bytes, CLAUDE.md: {len(c)} bytes."
    )
