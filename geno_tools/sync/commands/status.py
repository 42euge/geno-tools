"""Compare local installation state with one or more hosts."""

from __future__ import annotations

import argparse

from geno_tools.sync.diff import compare
from geno_tools.sync.lockfile import LockfileError, build_lockfile, parse_lockfile
from geno_tools.sync.transport import (
    TransportError,
    load_host_registry,
    resolve_host,
    run as run_remote,
)


def _failure(returncode: int, stderr: str) -> str:
    if returncode == 127 or "command not found" in stderr.lower():
        return "geno-tools is not installed"
    return f"offline (exit {returncode})"


def run(args: argparse.Namespace) -> int:
    try:
        registry = load_host_registry()
        aliases = args.hosts or [
            alias for alias, host in registry.hosts.items() if not host.local
        ]
        hosts = [resolve_host(alias, registry) for alias in aliases]
    except TransportError as error:
        print(f"sync status: {error}")
        return 1
    if not hosts:
        print("no remote hosts configured")
        return 0

    local = build_lockfile()
    successes = 0
    for host in hosts:
        print(f"{host.alias}:")
        try:
            completed = run_remote(host, ["geno-tools", "sync", "export"])
        except TransportError as error:
            print(f"  offline: {error}")
            continue
        if completed.returncode:
            print(f"  {_failure(completed.returncode, completed.stderr)}")
            continue
        try:
            remote = parse_lockfile(completed.stdout)
        except LockfileError as error:
            print(f"  invalid lockfile: {error}")
            continue
        successes += 1
        delta = compare(local, remote)
        differences = [item for item in delta.skillsets if item.state != "in-sync"]
        if not differences and not delta.config:
            print("  in sync")
            continue
        for item in differences:
            print(f"  {item.name}: {item.state}")
        for item in delta.config:
            print(f"  config {item.key}: {item.here!r} -> {item.source!r}")
    return 0 if successes else 1
