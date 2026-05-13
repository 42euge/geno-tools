"""Registry of geno-* skillsets — discovers repos from GitHub.

Registry keys are the full repo name (e.g. ``geno-<name>``). For backwards
compatibility the resolver also accepts the bare slug (``<name>``).
"""

import json
import subprocess

OWNER = "42euge"
PREFIX = "geno-"
EXCLUDE = {"geno-tools"}


def _discover() -> dict[str, str]:
    """Discover geno-* repos from the GitHub account via `gh` CLI."""
    try:
        r = subprocess.run(
            ["gh", "repo", "list", OWNER,
             "--json", "name,url",
             "--limit", "100",
             "--no-archived"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0:
            return {}
        repos = json.loads(r.stdout)
        return {
            repo["name"]: repo["url"] + ".git"
            for repo in repos
            if repo["name"].startswith(PREFIX) and repo["name"] not in EXCLUDE
        }
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return {}


_FALLBACK: dict[str, str] = {
    "geno-agents":   f"https://github.com/{OWNER}/geno-agents.git",
    "geno-dev":      f"https://github.com/{OWNER}/geno-dev.git",
    "geno-iso":      f"https://github.com/{OWNER}/geno-iso.git",
    "geno-kaggle":   f"https://github.com/{OWNER}/geno-kaggle.git",
    "geno-loops":    f"https://github.com/{OWNER}/geno-loops.git",
    "geno-media":    f"https://github.com/{OWNER}/geno-media.git",
    "geno-mine":     f"https://github.com/{OWNER}/geno-mine.git",
    "geno-notes":    f"https://github.com/{OWNER}/geno-notes.git",
    "geno-research": f"https://github.com/{OWNER}/geno-research.git",
    "geno-specs":    f"https://github.com/{OWNER}/geno-specs.git",
    "geno-taxes":    f"https://github.com/{OWNER}/geno-taxes.git",
    "geno-ws":       f"https://github.com/{OWNER}/geno-ws.git",
}

_cache: dict[str, str] | None = None


def available() -> dict[str, str]:
    global _cache
    if _cache is None:
        _cache = _discover()
        if not _cache:
            _cache = dict(_FALLBACK)
    return _cache


def resolve(name: str) -> str | None:
    """Return the git URL for a registered skillset name, or None.

    Accepts the canonical full repo name (e.g. ``geno-<name>``) and, for
    backwards compatibility, the bare slug (e.g. ``<name>``).
    """
    repos = available()
    if name in repos:
        return repos[name]
    if not name.startswith(PREFIX):
        return repos.get(f"{PREFIX}{name}")
    return None
