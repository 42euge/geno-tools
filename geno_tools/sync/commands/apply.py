"""Apply a lockfile supplied on standard input."""

from __future__ import annotations

import argparse
import json
import sys

from geno_tools.sync import package as sync_package
from geno_tools.sync.lockfile import LockfileError, parse_lockfile
from geno_tools.sync.package import PackageError
from geno_tools.sync.reconcile import (
    ReconcileError,
    reconcile_package,
    reconcile as reconcile_installation,
)

from . import options_from_args, render_result


MAX_UNCONFIRMED_BYTES = 100 * 1024 * 1024


def run(args: argparse.Namespace) -> int:
    try:
        raw = sys.stdin.read()
        try:
            decoded = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise LockfileError("lockfile is not valid JSON") from error
        options = options_from_args(args)
        if isinstance(decoded, dict) and "protocol" in decoded:
            source = sync_package.parse(decoded)
            size = sync_package.artifact_size(source)
            if (
                size > MAX_UNCONFIRMED_BYTES
                and not options.yes
                and not args.allow_large
            ):
                raise ReconcileError(
                    "package artifacts exceed 100 MiB; rerun with --yes to apply"
                )
            result = reconcile_package(source, options)
        else:
            source = parse_lockfile(decoded)
            result = reconcile_installation(source, options)
    except (LockfileError, PackageError, ReconcileError) as error:
        print(f"sync apply: {error}", file=sys.stderr)
        return 1
    return render_result(result, dry_run=options.dry_run)
