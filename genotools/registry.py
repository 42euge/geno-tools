"""Registry of geno-* skillsets — discovers repos from GitHub."""

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
            repo["name"].removeprefix(PREFIX): repo["url"] + ".git"
            for repo in repos
            if repo["name"].startswith(PREFIX) and repo["name"] not in EXCLUDE
        }
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return {}


_FALLBACK: dict[str, str] = {
    "agents":   f"https://github.com/{OWNER}/geno-agents.git",
    "media":    f"https://github.com/{OWNER}/geno-media.git",
    "research": f"https://github.com/{OWNER}/geno-research.git",
    "taxes":    f"https://github.com/{OWNER}/geno-taxes.git",
    "kaggle":   f"https://github.com/{OWNER}/geno-kaggle.git",
    "dev":      f"https://github.com/{OWNER}/geno-dev.git",
    "specs":    f"https://github.com/{OWNER}/geno-specs.git",
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
    """Return the git URL for a registered skillset name, or None."""
    return available().get(name)
