"""Tests for the ecosystem compliance auditor (geno_tools.audit)."""

import textwrap
from pathlib import Path

from geno_tools import audit


def _mk(root: Path, manifest_ver="0.1.0", skill_ver="0.1.0", pyproject_ver=None):
    (root / "genotools.yaml").write_text(f"name: geno-demo\nversion: \"{manifest_ver}\"\n")
    (root / "SKILL.md").write_text(textwrap.dedent(f"""\
        ---
        name: geno-demo
        metadata:
          version: "{skill_ver}"
        ---
        # geno-demo
        """))
    if pyproject_ver:
        (root / "pyproject.toml").write_text(textwrap.dedent(f"""\
            [project]
            name = "geno-demo"
            version = "{pyproject_ver}"
            """))


def _levels(results, check_substr):
    return [lvl for lvl, chk, _ in results if check_substr in chk]


def test_compliant_repo_has_no_fail(tmp_path):
    _mk(tmp_path)
    results = audit.audit(str(tmp_path))
    assert "FAIL" not in [lvl for lvl, _, _ in results]


def test_version_mismatch_fails(tmp_path):
    _mk(tmp_path, manifest_ver="0.2.0", skill_ver="0.1.0")
    results = audit.audit(str(tmp_path))
    assert "FAIL" in _levels(results, "SKILL.md version == manifest")


def test_missing_manifest_fails(tmp_path):
    (tmp_path / "SKILL.md").write_text("---\nname: x\n---\n")
    results = audit.audit(str(tmp_path))
    assert "FAIL" in _levels(results, "genotools.yaml present")


def test_library_capable_info(tmp_path):
    _mk(tmp_path, pyproject_ver="0.1.0")
    results = audit.audit(str(tmp_path))
    assert any(lvl == "INFO" and "library-capable" in chk and "yes" in detail
               for lvl, chk, detail in results)
