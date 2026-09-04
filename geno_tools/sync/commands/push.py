"""Transfer a selected local installation package to a destination host."""

from __future__ import annotations

import argparse
import json
import sys

from geno_tools.sync import package as sync_package
from geno_tools.sync import selection, terminal
from geno_tools.sync.package import PackageError
from geno_tools.sync.transport import (
    TransportError,
    load_host_registry,
    resolve_host,
    run as run_remote,
)

from . import render_result
from . import transfer


def _remote_error(args: argparse.Namespace, completed) -> int:
    detail = completed.stderr.strip() or f"exit {completed.returncode}"
    print(f"sync push {args.host}: {detail}", file=sys.stderr)
    return 1


def run(args: argparse.Namespace) -> int:
    try:
        registry = load_host_registry()
        host = resolve_host(args.host, registry)
        local = selection.inventory()
        choices = transfer.choose_sources(local, args.dev_source)

        if args.dry_run:
            completed = run_remote(host, ["geno-tools", "sync", "inventory"])
            if completed.returncode:
                return _remote_error(args, completed)
            remote = selection.parse(completed.stdout)
            result = transfer.preview(local, remote, choices)
            return render_result(result, dry_run=True)

        package = sync_package.build(choices)
        size = sync_package.artifact_size(package)
        approved, approved_large = transfer.approve_large(size, yes=args.yes)
        if not approved:
            raise transfer.TransferError("transfer cancelled; no data sent")
        command = ["geno-tools", "sync", "apply", "-"]
        if args.yes:
            command.append("--yes")
        elif approved_large:
            command.append("--allow-large")
        if args.no_rebuild:
            command.append("--no-rebuild")
        completed = run_remote(
            host,
            command,
            input_text=json.dumps(package, sort_keys=True),
        )
    except (
        PackageError,
        selection.SelectionError,
        transfer.TransferError,
        TransportError,
    ) as error:
        print(f"sync push {args.host}: {error}", file=sys.stderr)
        return 1
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.returncode:
        return _remote_error(args, completed)
    return 0
