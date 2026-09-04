"""Apply a lockfile supplied on standard input."""

from __future__ import annotations

import argparse
import sys

from geno_tools.sync.lockfile import LockfileError, parse_lockfile
from geno_tools.sync.reconcile import (
    ReconcileError,
    reconcile as reconcile_installation,
)

from . import options_from_args, render_result


def run(args: argparse.Namespace) -> int:
    try:
        source = parse_lockfile(sys.stdin.read())
        options = options_from_args(args)
        result = reconcile_installation(source, options)
    except (LockfileError, ReconcileError) as error:
        print(f"sync apply: {error}", file=sys.stderr)
        return 1
    return render_result(result, dry_run=options.dry_run)
