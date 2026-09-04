"""Reconcile this machine toward a configured source host."""

from __future__ import annotations

import argparse
import sys

from geno_tools.core import config
from geno_tools.sync.lockfile import LockfileError, parse_lockfile
from geno_tools.sync.reconcile import (
    ReconcileError,
    reconcile as reconcile_installation,
)
from geno_tools.sync.transport import (
    TransportError,
    load_host_registry,
    resolve_host,
    run as run_remote,
)

from . import options_from_args, render_result


def run(args: argparse.Namespace) -> int:
    try:
        registry = load_host_registry()
        alias = args.host or config.load().get("sync", {}).get("primary")
        if not alias:
            raise TransportError(
                "no source host specified; set geno-tools config key sync.primary"
            )
        host = resolve_host(alias, registry)
        completed = run_remote(host, ["geno-tools", "sync", "export"])
    except TransportError as error:
        print(f"sync pull: {error}", file=sys.stderr)
        return 1
    if completed.returncode:
        if completed.returncode == 127 or "command not found" in completed.stderr.lower():
            detail = "geno-tools is not installed"
        else:
            detail = f"remote export exited {completed.returncode}"
        print(f"sync pull {alias}: {detail}", file=sys.stderr)
        return 1
    try:
        source = parse_lockfile(completed.stdout)
        options = options_from_args(args)
        result = reconcile_installation(source, options)
    except (LockfileError, ReconcileError) as error:
        print(f"sync pull {alias}: {error}", file=sys.stderr)
        return 1
    return render_result(result, dry_run=options.dry_run)
