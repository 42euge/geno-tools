"""Fetch and apply a selected installation package from a source host."""

from __future__ import annotations

import argparse
import sys

from geno_tools.core import config
from geno_tools.sync import package as sync_package
from geno_tools.sync import selection, terminal
from geno_tools.sync.package import PackageError
from geno_tools.sync.reconcile import ReconcileError, reconcile_package
from geno_tools.sync.transport import (
    TransportError,
    load_host_registry,
    resolve_host,
    run as run_remote,
)

from . import options_from_args, render_result
from . import transfer


def _remote_failure(alias: str, completed, operation: str) -> TransportError:
    if completed.returncode == 127 or "command not found" in completed.stderr.lower():
        detail = "geno-tools is not installed"
    else:
        detail = f"remote {operation} exited {completed.returncode}"
    return TransportError(f"{alias}: {detail}")


def run(args: argparse.Namespace) -> int:
    alias = args.host
    try:
        registry = load_host_registry()
        alias = alias or config.load().get("sync", {}).get("primary")
        if not alias:
            raise TransportError(
                "no source host specified; set geno-tools config key sync.primary"
            )
        host = resolve_host(alias, registry)
        completed = run_remote(host, ["geno-tools", "sync", "inventory"])
        if completed.returncode:
            raise _remote_failure(alias, completed, "inventory")
        remote = selection.parse(completed.stdout)
        choices = transfer.choose_sources(remote, args.dev_source)

        if args.dry_run:
            local = selection.inventory()
            return render_result(
                transfer.preview(remote, local, choices), dry_run=True
            )

        estimate = transfer.estimated_size(remote, choices)
        approved, _approved_large = transfer.approve_large(estimate, yes=args.yes)
        if not approved:
            raise transfer.TransferError("transfer cancelled; no data fetched")
        encoded = transfer.encode_selections(choices)
        completed = run_remote(
            host,
            ["geno-tools", "sync", "export", "--selection-json", encoded],
        )
        if completed.returncode:
            raise _remote_failure(alias, completed, "export")
        package = sync_package.parse(completed.stdout)
        actual = sync_package.artifact_size(package)
        if actual > transfer.MAX_UNCONFIRMED_BYTES and estimate <= (
            transfer.MAX_UNCONFIRMED_BYTES
        ):
            approved, _approved_large = transfer.approve_large(actual, yes=args.yes)
            if not approved:
                raise transfer.TransferError("transfer cancelled; package not applied")
        options = options_from_args(args)
        result = reconcile_package(package, options)
    except (
        PackageError,
        ReconcileError,
        selection.SelectionError,
        transfer.TransferError,
        TransportError,
    ) as error:
        prefix = f"sync pull {alias}" if alias else "sync pull"
        print(f"{prefix}: {error}", file=sys.stderr)
        return 1
    return render_result(result, dry_run=options.dry_run)
