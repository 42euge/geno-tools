"""Registry of geno-* skillsets — a discovery cache, not a hardcoded list.

A meta-ecosystem discovers its skillsets rather than shipping a static list.
The `meta/ecosystem/discover` skill drives an agent (web search + unauthenticated
curl against the public GitHub API) to find geno-* repos that expose a top-level
`SKILL.md`, and writes them to the cache below. This module only READS that
cache — no `gh`, no token, no network of its own.

Cache shape (`~/.geno/registry.json`):

    {
      "geno-loops": {"url": "https://github.com/42euge/geno-loops.git",
                     "source": "github:42euge", "discovered": "2026-06-26T..."},
      ...
    }

Registry keys are the full repo name (e.g. ``geno-<name>``). For backwards
compatibility the resolver also accepts the bare slug (``<name>``).
"""

import json
from pathlib import Path

PREFIX = "geno-"
CACHE_FILE = Path.home() / ".geno" / "registry.json"

_cache: dict[str, str] | None = None


def read_cache() -> dict[str, str]:
    """Return ``{name: url}`` from the discovery cache, or ``{}`` if absent.

    Tolerates both the rich shape ({name: {url, ...}}) the discover skill writes
    and a plain {name: url} map.
    """
    if not CACHE_FILE.exists():
        return {}
    try:
        data = json.loads(CACHE_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[str, str] = {}
    for name, val in data.items():
        if isinstance(val, dict):
            url = val.get("url")
            if url:
                out[name] = url
        elif isinstance(val, str):
            out[name] = val
    return out


def write_cache(entries: dict) -> Path:
    """Write the discovery cache (used by the discover skill / tests).

    `entries` may map name -> url or name -> {url, source, discovered}.
    Invalidates the in-process cache so the next ``available()`` re-reads.
    """
    global _cache
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(entries, indent=2) + "\n")
    _cache = None
    return CACHE_FILE


def available() -> dict[str, str]:
    """Return ``{name: url}`` of discoverable skillsets (from the cache).

    Empty when discovery has never run — that's intentional: no fake/hardcoded
    data. Callers should prompt the user to run the discover skill.
    """
    global _cache
    if _cache is None:
        _cache = read_cache()
    return _cache


def resolve(name: str) -> str | None:
    """Return the git URL for a discovered skillset name, or None.

    Accepts the canonical full repo name (e.g. ``geno-<name>``) and, for
    backwards compatibility, the bare slug (e.g. ``<name>``).
    """
    repos = available()
    if name in repos:
        return repos[name]
    if not name.startswith(PREFIX):
        return repos.get(f"{PREFIX}{name}")
    return None
