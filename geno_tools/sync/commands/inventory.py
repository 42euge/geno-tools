"""Emit source-selection inventory as machine-readable JSON."""

from __future__ import annotations

import argparse
import json

from geno_tools.sync.selection import inventory as build_inventory


def run(_: argparse.Namespace) -> int:
    print(json.dumps(build_inventory(), indent=2, sort_keys=True))
    return 0
