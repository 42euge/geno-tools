"""Emit the local installation lockfile as machine-readable JSON."""

from __future__ import annotations

import argparse
import json
import sys

from geno_tools.sync import package as sync_package
from geno_tools.sync.lockfile import build_lockfile
from geno_tools.sync.package import PackageError

from .transfer import TransferError, decode_selections


def run(args: argparse.Namespace) -> int:
    try:
        value = (
            sync_package.build(decode_selections(args.selection_json))
            if args.selection_json
            else build_lockfile()
        )
    except (PackageError, TransferError) as error:
        print(f"sync export: {error}", file=sys.stderr)
        return 1
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0
