"""List skillsets available from the discovery registry."""

from __future__ import annotations

import argparse

from geno_tools.core.terminal import bold, cyan, dim, green, rule

from .. import registry
from .status import _installed_skillsets

_CATEGORY_ORDER = [
    "Core Framework",
    "Developer Tools",
    "Workspaces & Data",
    "Modalities & Capabilities",
    "Applied Research",
    "Interfaces & Comms",
]


def run(args: argparse.Namespace) -> int:
    refresh = getattr(args, "refresh", False)
    if refresh or registry.is_stale():
        age = registry.cache_age_seconds()
        reason = "forced" if refresh else ("missing" if age is None else "stale")
        print(dim(f"  refreshing discovery cache ({reason})…"))
        try:
            registry.discover_now()
        except Exception as error:
            print(dim(f"  refresh failed ({error}); showing cached results"))

    entries = registry.read_full()
    print(bold("geno-tools"))
    if not entries:
        print(rule("discover"))
        print(dim("  no skillsets found (no network, empty cache)."))
        print(dim("  retry:  geno-tools discover --refresh"))
        print(dim("  or install directly:  geno-tools install <git-url>"))
        return 0

    installed = set(_installed_skillsets())
    by_category: dict[str, list[str]] = {}
    for name, entry in entries.items():
        by_category.setdefault(entry.get("category", "Uncategorized"), []).append(name)
    order = (
        [category for category in _CATEGORY_ORDER if category in by_category]
        + sorted(
            category
            for category in by_category
            if category not in _CATEGORY_ORDER and category != "Uncategorized"
        )
        + (["Uncategorized"] if "Uncategorized" in by_category else [])
    )

    print(rule(f"discover · {len(entries)}"))
    name_width = max(len(name) for name in entries)
    for category in order:
        print(cyan(f"  {category}"))
        for name in sorted(by_category[category]):
            marker = green("✓ installed") if name in installed else dim(entries[name]["url"])
            print(f"    {bold(name.ljust(name_width))}  {marker}")
    return 0
