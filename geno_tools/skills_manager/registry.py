"""Registry of geno-* skillsets — a discovery cache, not a hardcoded list.

A meta-ecosystem discovers its skillsets rather than shipping a static list.
Discovery (`discover_now`) uses **unauthenticated curl against the public GitHub
API** — no `gh`, no token, no MCP — to find geno-* repos that expose a top-level
`SKILL.md`, reads each repo's `layer.json` for its ecosystem category, and writes
them to the cache below. The CLI `discover` command refreshes when the cache is
stale (>30 min) and reads it the rest of the time.

Cache shape (`~/.geno/registry.json`):

    {
      "geno-loops": {"url": "...git", "source": "github:42euge",
                     "category": "Developer Tools", "discovered": "2026-..."},
      ...
    }

Registry keys are the full repo name (e.g. ``geno-<name>``). For backwards
compatibility the resolver also accepts the bare slug (``<name>``).
"""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

PREFIX = "geno-"
CACHE_FILE = Path.home() / ".geno" / "registry.json"
STALE_SECONDS = 30 * 60  # auto-refresh `discover` when the cache is older
_UNCATEGORIZED = "Uncategorized"

_cache: dict[str, str] | None = None


# ── cache read ────────────────────────────────────────────────────────────

def read_full() -> dict[str, dict]:
    """Return the rich cache: ``{name: {url, source, category, discovered}}``.

    Normalizes the plain ``{name: url}`` shape too. ``{}`` if absent/unreadable.
    """
    if not CACHE_FILE.exists():
        return {}
    try:
        data = json.loads(CACHE_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[str, dict] = {}
    for name, val in data.items():
        if isinstance(val, dict) and val.get("url"):
            entry = dict(val)
            entry.setdefault("category", _UNCATEGORIZED)
            out[name] = entry
        elif isinstance(val, str):
            out[name] = {"url": val, "category": _UNCATEGORIZED}
    return out


def read_cache() -> dict[str, str]:
    """Return ``{name: url}`` from the cache (back-compat flat view)."""
    return {name: e["url"] for name, e in read_full().items()}


def write_cache(entries: dict) -> Path:
    """Write the discovery cache. Invalidates the in-process cache."""
    global _cache
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(entries, indent=2) + "\n")
    _cache = None
    return CACHE_FILE


def available() -> dict[str, str]:
    """Return ``{name: url}`` of discoverable skillsets (from the cache)."""
    global _cache
    if _cache is None:
        _cache = read_cache()
    return _cache


def resolve(name: str) -> str | None:
    """git URL for a discovered skillset name (full or bare slug), or None."""
    repos = available()
    if name in repos:
        return repos[name]
    if not name.startswith(PREFIX):
        return repos.get(f"{PREFIX}{name}")
    return None


# ── staleness ─────────────────────────────────────────────────────────────

def cache_age_seconds() -> float | None:
    """Seconds since the cache was last written, or None if it doesn't exist."""
    if not CACHE_FILE.exists():
        return None
    return max(0.0, time.time() - CACHE_FILE.stat().st_mtime)


def is_stale(max_age: float = STALE_SECONDS) -> bool:
    """True if the cache is missing or older than max_age seconds."""
    age = cache_age_seconds()
    return age is None or age > max_age


# ── discovery (curl, unauthenticated) ───────────────────────────────────────

def _get(url: str, *, method: str = "GET", timeout: int = 20):
    req = urllib.request.Request(
        url, method=method, headers={"User-Agent": "geno-tools-discover"})
    return urllib.request.urlopen(req, timeout=timeout)


def _category(org: str, name: str) -> str:
    """Read a repo's ecosystem category from its public layer.json.

    `{"ecosystem": "geno-ecosystem / Developer Tools"}` → "Developer Tools".
    """
    try:
        raw = _get(f"https://raw.githubusercontent.com/{org}/{name}/HEAD/layer.json").read()
        eco = (json.loads(raw) or {}).get("ecosystem", "")
        # strip the "geno-ecosystem / " prefix if present
        return eco.split("/", 1)[-1].strip() if eco else _UNCATEGORIZED
    except Exception:
        return _UNCATEGORIZED


def _has_skill_md(org: str, name: str) -> bool:
    try:
        return _get(f"https://raw.githubusercontent.com/{org}/{name}/HEAD/SKILL.md",
                    method="HEAD", timeout=10).status == 200
    except Exception:
        return False


def discover_now(org: str = "42euge", prefix: str = PREFIX) -> dict[str, dict]:
    """Curl the public GitHub API for {prefix}* repos with a top-level SKILL.md,
    tag each with its layer.json category, write + return the cache.

    Unauthenticated → public repos only. Raises on a hard network failure so the
    caller can fall back to the existing cache.
    """
    repos = json.loads(
        _get(f"https://api.github.com/users/{org}/repos?per_page=100&type=public").read())
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    out: dict[str, dict] = {}
    for r in repos:
        name = r.get("name", "")
        if not name.startswith(prefix) or r.get("archived") or name == "geno-tools":
            continue
        if not _has_skill_md(org, name):
            continue
        out[name] = {
            "url": r["clone_url"],
            "source": f"github:{org}",
            "category": _category(org, name),
            "discovered": stamp,
        }
    write_cache(out)
    return out
