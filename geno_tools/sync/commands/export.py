"""Emit the local installation lockfile as machine-readable JSON."""

from __future__ import annotations

import argparse
import json

from geno_tools.sync.lockfile import build_lockfile


def run(_: argparse.Namespace) -> int:
    print(json.dumps(build_lockfile(), indent=2, sort_keys=True))
    return 0
