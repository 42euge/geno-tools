"""Compliance engine and audit CLI tests."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from geno_tools.cli import main
from geno_tools.skills_manager.compliance import RULE_IDS, audit_skillset


def compliant_repo(tmp_path: Path) -> Path:
    root = tmp_path / "geno-demo"
    skill = root / "skills" / "geno-demo" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        """---
name: geno-demo
description: Use when a demonstration skill is needed
allowed-tools: Read
metadata:
  version: "0.1.0"
---
# geno-demo
"""
    )
    (root / "SKILL.md").symlink_to("skills/geno-demo/SKILL.md")
    (root / "genotools.yaml").write_text(
        """name: geno-demo
version: "0.1.0"
description: Demonstration skillset
skills:
  source: skills/
"""
    )
    (root / "AGENTS.md").write_text("# geno-demo\n\nRepository-specific guidance.\n")
    (root / "README.md").write_text(
        "# geno-demo\n\nInstall with `geno-tools install geno-demo`.\n"
    )
    (root / "LICENSE").write_text("MIT\n")
    (root / "docs").mkdir()
    (root / "docs" / "index.md").write_text("# geno-demo\n")
    (root / "docs" / "getting-started.md").write_text("# Getting started\n")
    (root / "mkdocs.yml").write_text("site_name: geno-demo\n")
    subprocess.check_call(["git", "init", "--quiet", str(root)])
    subprocess.check_call(["git", "-C", str(root), "add", "."])
    return root


def result(report, rule_id):
    return next(item for item in report.results if item.rule_id == rule_id)


def test_compliant_repo_passes_every_rule(tmp_path):
    report = audit_skillset(compliant_repo(tmp_path))

    assert report.verdict == "PASS"
    assert [item.rule_id for item in report.results] == list(RULE_IDS)
    assert all(item.status == "PASS" for item in report.results)


def test_version_disagreement_fails(tmp_path):
    root = compliant_repo(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "geno-demo"\nversion = "0.2.0"\n'
    )

    report = audit_skillset(root)

    assert result(report, "GENO-007").status == "FAIL"
    assert "pyproject=0.2.0" in result(report, "GENO-007").message


def test_retired_instruction_files_fail(tmp_path):
    root = compliant_repo(tmp_path)
    (root / "CLAUDE.md").write_text("@./AGENTS.md\n")

    report = audit_skillset(root)

    assert result(report, "GENO-020").status == "FAIL"
    assert "CLAUDE.md" in result(report, "GENO-020").message


def test_aliased_command_fails(tmp_path):
    root = compliant_repo(tmp_path)
    (root / "README.md").write_text("Run `/gt-demo`.\n")

    report = audit_skillset(root)

    assert result(report, "GENO-021").status == "FAIL"
    assert "README.md" in result(report, "GENO-021").message


def test_cli_emits_json_report(tmp_path, capsys):
    root = compliant_repo(tmp_path)

    assert main(["audit", "check", str(root), "--json"]) == 0

    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "PASS"
    assert len(report["results"]) == len(RULE_IDS)


def test_audit_without_action_prints_help(capsys):
    assert main(["audit"]) == 0
    assert "audit check" not in capsys.readouterr().err


def test_documented_rules_match_engine():
    spec = Path(__file__).parents[2] / "docs" / "skillset-compliance.md"
    documented = re.findall(r"\*\*(GENO-\d{3})\b", spec.read_text())

    assert documented == list(RULE_IDS)
