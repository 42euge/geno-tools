"""Discovery — find candidate skillset repos in configured sources.

A *source* declares where to look (GitHub org, GitLab group, etc.) and a
*candidate* is any repo under that source whose name matches the configured
prefix and exposes a top-level ``SKILL.md``.

Discovery never installs anything. It only proposes repos that the operator
(or platform team) can then audit and install through ``geno-tools install``.

The provider layer is pluggable. A provider implements::

    def list_repos(source: dict) -> list[Candidate]: ...

This module currently ships a thin GitHub provider that shells out to the
``gh`` CLI so we don't pull in extra HTTP deps. GitLab, Gitea, and Bitbucket
follow the same shape — see ``_register_provider``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Iterable

from genotools import config


@dataclass(frozen=True)
class Candidate:
    name: str       # full repo name as it appears in the host
    url: str        # clone URL (https or ssh)
    source: str     # human-readable source label, e.g. "github:acme-corp"
    has_skill_md: bool


Provider = Callable[[dict], list[Candidate]]
_PROVIDERS: dict[str, Provider] = {}


def _register_provider(kind: str):
    def decorate(fn: Provider) -> Provider:
        _PROVIDERS[kind] = fn
        return fn
    return decorate


# ── public api ──────────────────────────────────────────────────────────────


def sources() -> list[dict]:
    """Return the configured list of discovery sources."""
    return list(config.load().get("discovery", {}).get("sources", []))


def candidates() -> list[Candidate]:
    """Walk every configured source and return matching candidate repos."""
    out: list[Candidate] = []
    for src in sources():
        kind = src.get("kind")
        provider = _PROVIDERS.get(kind)
        if provider is None:
            continue
        try:
            out.extend(provider(src))
        except Exception as e:
            print(f"  warn: discovery source {kind} failed: {e}", file=sys.stderr)
    return out


def candidates_by_name() -> dict[str, str]:
    """Return ``{repo_name: clone_url}`` for installable candidates."""
    return {c.name: c.url for c in candidates() if c.has_skill_md}


# ── github provider ─────────────────────────────────────────────────────────


@_register_provider("github")
def _github(source: dict) -> list[Candidate]:
    """List repos in a GitHub org via the ``gh`` CLI.

    Recognized fields: ``org`` (required), ``base_url`` (optional, for
    GitHub Enterprise), ``prefix`` (default: ``geno-``), ``auth_env``
    (optional environment variable name carrying a token).
    """
    org = source.get("org")
    if not org:
        return []
    prefix = source.get("prefix", "geno-")
    label = f"github:{org}"

    env = dict(os.environ)
    if (auth_env := source.get("auth_env")) and (tok := os.environ.get(auth_env)):
        env["GH_TOKEN"] = tok
    if base := source.get("base_url"):
        env["GH_HOST"] = base.rstrip("/").removeprefix("https://").removeprefix("http://")

    args = [
        "gh", "repo", "list", org,
        "--json", "name,url,sshUrl",
        "--limit", "200",
        "--no-archived",
    ]

    out = subprocess.run(args, capture_output=True, text=True, env=env, timeout=30)
    if out.returncode != 0:
        return []
    try:
        repos = json.loads(out.stdout)
    except json.JSONDecodeError:
        return []

    results: list[Candidate] = []
    for repo in repos:
        name = repo.get("name") or ""
        if not name.startswith(prefix):
            continue
        results.append(Candidate(
            name=name,
            url=(repo.get("url") or "") + ".git",
            source=label,
            has_skill_md=_github_has_skill_md(org, name, source, env),
        ))
    return results


def _github_has_skill_md(org: str, name: str, source: dict, env: dict) -> bool:
    """Probe for a top-level SKILL.md via the GitHub API."""
    api = source.get("base_url", "https://api.github.com").rstrip("/")
    path = f"/repos/{org}/{name}/contents/SKILL.md"
    out = subprocess.run(
        ["gh", "api", "--silent", path],
        capture_output=True, text=True, env=env, timeout=15,
    )
    return out.returncode == 0


# ── gitlab provider (scaffold) ──────────────────────────────────────────────


@_register_provider("gitlab")
def _gitlab(source: dict) -> list[Candidate]:
    """GitLab provider scaffold.

    Implementation plan:
    1. ``GET <base_url>/api/v4/groups/<group>/projects?per_page=100``
       with ``PRIVATE-TOKEN: $auth_env``.
    2. Filter ``path`` by ``prefix``.
    3. Probe ``GET /projects/<id>/repository/files/SKILL.md?ref=HEAD`` for
       the candidate check.
    Not implemented yet — returns an empty list so the rest of discovery
    keeps working.
    """
    return []


# ── bitbucket / gitea (placeholders) ────────────────────────────────────────


@_register_provider("bitbucket")
def _bitbucket(source: dict) -> list[Candidate]:
    return []


@_register_provider("gitea")
def _gitea(source: dict) -> list[Candidate]:
    return []


# ── helpers ─────────────────────────────────────────────────────────────────


def iter_kinds() -> Iterable[str]:
    return tuple(_PROVIDERS.keys())
