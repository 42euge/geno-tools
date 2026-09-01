"""CLI adapter for deterministic skillset compliance audits."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from rich.console import Console
from rich.table import Table

from .. import paths, registry
from ..compliance import AuditReport, audit_skillset


def run(args: argparse.Namespace) -> int:
    try:
        with resolve_target(args.target) as target:
            report = audit_skillset(
                target.path, repository_name=target.repository_name
            )
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"audit failed: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(report.to_json())
    else:
        print_report(report)

    if report.verdict == "FAIL":
        return 1
    if args.strict and report.verdict == "WARN":
        return 1
    return 0


@contextmanager
def resolve_target(reference: str) -> Iterator["ResolvedTarget"]:
    """Resolve a path, installed name, registry name, or git URL to a checkout."""
    candidate = Path(reference).expanduser()
    if candidate.is_dir():
        yield ResolvedTarget(candidate.resolve(), candidate.resolve().name)
        return

    installed_name = paths.normalize(reference)
    installed = paths.skillset_active(installed_name)
    if installed.is_dir():
        yield ResolvedTarget(installed.resolve(), installed_name)
        return

    source = registry.resolve(reference)
    if source is None and reference.startswith(("https://", "http://", "git@")):
        source = reference
    if source is None and reference.endswith(".git"):
        source = reference
    if source is None:
        raise ValueError(
            f"unknown audit target: {reference}; pass a local path, installed "
            "skillset, registry name, or git URL"
        )

    repository_name = Path(source.rstrip("/")).name.removesuffix(".git")
    with tempfile.TemporaryDirectory(prefix="geno-tools-audit-") as directory:
        checkout = Path(directory) / repository_name
        subprocess.check_call(
            ["git", "clone", "--depth", "1", "--quiet", source, str(checkout)]
        )
        yield ResolvedTarget(checkout, repository_name)


@dataclass(frozen=True)
class ResolvedTarget:
    path: Path
    repository_name: str


def print_report(report: AuditReport) -> None:
    console = Console(highlight=False)
    table = Table(title=f"Skillset compliance · {Path(report.target).name}")
    table.add_column("Status", no_wrap=True)
    table.add_column("Rule", style="bold magenta", no_wrap=True)
    table.add_column("Finding")
    table.add_column("Path", style="dim")
    colors = {"PASS": "green", "FAIL": "bold red", "WARN": "yellow", "INFO": "cyan"}
    for result in report.results:
        table.add_row(
            f"[{colors[result.status]}]{result.status}[/{colors[result.status]}]",
            result.rule_id,
            result.message,
            result.path or "",
        )
    console.print(table)
    counts = report.counts
    console.print(
        f"[{colors[report.verdict]}]{report.verdict}[/{colors[report.verdict]}]  "
        f"{counts['PASS']} passed · {counts['FAIL']} failed · {counts['WARN']} warnings"
    )


__all__ = ["print_report", "resolve_target", "run"]
