"""Compare Stable installations and active selections with remote hosts."""

from __future__ import annotations

import argparse

from geno_tools.sync import selection
from geno_tools.sync.diff import compare
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


def _active(value: dict | None) -> tuple[str, str | None]:
    active = value.get("active") if isinstance(value, dict) else None
    if not isinstance(active, dict):
        return "stable", None
    return "dev", active.get("fingerprint")


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

    local = selection.inventory()
    successes = 0
    for host in hosts:
        print(f"{host.alias}:")
        try:
            completed = run_remote(host, ["geno-tools", "sync", "inventory"])
        except TransportError as error:
            print(f"  offline: {error}")
            continue
        if completed.returncode:
            print(f"  {_failure(completed.returncode, completed.stderr)}")
            continue
        try:
            remote = selection.parse(completed.stdout)
        except selection.SelectionError as error:
            print(f"  invalid inventory: {error}")
            continue
        successes += 1
        delta = compare(local["lockfile"], remote["lockfile"])
        differences = [item for item in delta.skillsets if item.state != "in-sync"]
        for item in differences:
            print(f"  {item.name}: {item.state}")
        active_differences = 0
        names = sorted(local["skillsets"].keys() | remote["skillsets"].keys())
        for name in names:
            here = _active(local["skillsets"].get(name))
            there = _active(remote["skillsets"].get(name))
            if here == there:
                continue
            active_differences += 1
            if here[0] == there[0] == "dev":
                print(
                    f"  {name} active fingerprint: "
                    f"{str(here[1])[:12]} -> {str(there[1])[:12]}"
                )
            else:
                print(f"  {name} active selection: {here[0]} -> {there[0]}")
        for item in delta.config:
            print(f"  config {item.key}: {item.here!r} -> {item.source!r}")
        if not differences and not active_differences and not delta.config:
            print("  in sync")
    return 0 if successes else 1
