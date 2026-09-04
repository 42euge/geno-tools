"""Pipe local installation intent to a destination host."""

from __future__ import annotations

import argparse
import json
import sys

from geno_tools.sync.lockfile import build_lockfile
from geno_tools.sync.transport import (
    TransportError,
    load_host_registry,
    resolve_host,
    run as run_remote,
)


def run(args: argparse.Namespace) -> int:
    try:
        registry = load_host_registry()
        host = resolve_host(args.host, registry)
        command = ["geno-tools", "sync", "apply", "-"]
        if args.dry_run:
            command.append("--dry-run")
        if args.yes:
            command.append("--yes")
        if args.no_rebuild:
            command.append("--no-rebuild")
        completed = run_remote(
            host,
            command,
            input_text=json.dumps(build_lockfile(), sort_keys=True),
        )
    except TransportError as error:
        print(f"sync push {args.host}: {error}", file=sys.stderr)
        return 1
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.returncode:
        detail = completed.stderr.strip() or f"exit {completed.returncode}"
        print(f"sync push {args.host}: {detail}", file=sys.stderr)
        return 1
    return 0
