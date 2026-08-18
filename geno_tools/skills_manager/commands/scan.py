"""Scan configured sources for unregistered skillsets."""

from __future__ import annotations

import argparse

from .. import discovery


def run(args: argparse.Namespace) -> int:
    if not discovery.sources():
        print("no discovery sources configured (~/.geno/config.yaml: discovery.sources)")
        return 0

    candidates = discovery.scan(namespace=args.namespace, dry_run=args.dry_run)
    if not candidates:
        print("no new candidates found")
        return 0

    action = "found" if args.dry_run else "queued"
    print(f"{action} {len(candidates)} new candidate(s):")
    for candidate in candidates:
        print(f"  [{candidate.source}] {candidate.name:<32} {candidate.url}")
    if not args.dry_run:
        print(f"\ncandidates written to {discovery.CANDIDATES_FILE}")
    return 0
