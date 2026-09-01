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

from geno_tools.core import config


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
    """List repos in a GitLab group via the REST API."""
    group = source.get("group")
    if not group:
        return []
    base_url = source.get("base_url", "https://gitlab.com").rstrip("/")
    prefix = source.get("prefix", "geno-")
    label = f"gitlab:{group}"

    headers = {}
    if (auth_env := source.get("auth_env")) and (tok := os.environ.get(auth_env)):
        headers["PRIVATE-TOKEN"] = tok

    try:
        import urllib.request
        url = f"{base_url}/api/v4/groups/{group.replace('/', '%2F')}/projects?per_page=100&include_subgroups=true"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            repos = json.loads(resp.read())
    except Exception:
        return []

    results: list[Candidate] = []
    for repo in repos:
        path = repo.get("path", "")
        if not path.startswith(prefix):
            continue
        clone_url = repo.get("http_url_to_repo", "")
        project_id = repo.get("id")
        has_skill = False
        if project_id:
            has_skill = _gitlab_has_skill_md(base_url, project_id, headers)
        results.append(Candidate(name=path, url=clone_url, source=label, has_skill_md=has_skill))
    return results


def _gitlab_has_skill_md(base_url: str, project_id: int, headers: dict) -> bool:
    """Check for SKILL.md in a GitLab repo."""
    try:
        import urllib.request
        url = f"{base_url}/api/v4/projects/{project_id}/repository/files/SKILL.md?ref=HEAD"
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


# ── bitbucket / gitea (placeholders) ────────────────────────────────────────


@_register_provider("bitbucket")
def _bitbucket(source: dict) -> list[Candidate]:
    """List repos in a Bitbucket workspace via the REST API."""
    workspace = source.get("workspace")
    if not workspace:
        return []
    prefix = source.get("prefix", "geno-")
    label = f"bitbucket:{workspace}"

    headers = {}
    if (auth_env := source.get("auth_env")) and (tok := os.environ.get(auth_env)):
        headers["Authorization"] = f"Bearer {tok}"

    try:
        import urllib.request
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}?pagelen=100"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception:
        return []

    results: list[Candidate] = []
    for repo in data.get("values", []):
        slug = repo.get("slug", "")
        if not slug.startswith(prefix):
            continue
        clone_url = ""
        for link in repo.get("links", {}).get("clone", []):
            if link.get("name") == "https":
                clone_url = link.get("href", "")
                break
        has_skill = _bitbucket_has_skill_md(workspace, slug, headers)
        results.append(Candidate(name=slug, url=clone_url, source=label, has_skill_md=has_skill))
    return results


def _bitbucket_has_skill_md(workspace: str, slug: str, headers: dict) -> bool:
    """Check for SKILL.md in a Bitbucket repo."""
    try:
        import urllib.request
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{slug}/src/HEAD/SKILL.md"
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


@_register_provider("gitea")
def _gitea(source: dict) -> list[Candidate]:
    """List repos in a Gitea org via the REST API."""
    org = source.get("org")
    if not org:
        return []
    base_url = source.get("base_url", "https://gitea.com").rstrip("/")
    prefix = source.get("prefix", "geno-")
    label = f"gitea:{org}"

    headers = {}
    if (auth_env := source.get("auth_env")) and (tok := os.environ.get(auth_env)):
        headers["Authorization"] = f"token {tok}"

    try:
        import urllib.request
        url = f"{base_url}/api/v1/orgs/{org}/repos?limit=100"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            repos = json.loads(resp.read())
    except Exception:
        return []

    results: list[Candidate] = []
    for repo in repos:
        name = repo.get("name", "")
        if not name.startswith(prefix):
            continue
        clone_url = repo.get("clone_url", "")
        has_skill = _gitea_has_skill_md(base_url, org, name, headers)
        results.append(Candidate(name=name, url=clone_url, source=label, has_skill_md=has_skill))
    return results


def _gitea_has_skill_md(base_url: str, org: str, name: str, headers: dict) -> bool:
    """Check for SKILL.md in a Gitea repo."""
    try:
        import urllib.request
        url = f"{base_url}/api/v1/repos/{org}/{name}/contents/SKILL.md"
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


# ── community provider (GitHub search) ────────────────────────────────────


@_register_provider("community")
def _community(source: dict) -> list[Candidate]:
    """Search GitHub for public repos containing SKILL.md or agent skill topics."""
    query = source.get("query", "SKILL.md in:path filename:SKILL.md")
    limit = source.get("limit", 50)
    label = "community:github-search"

    args = [
        "gh", "search", "repos", query,
        "--json", "name,url,fullName",
        "--limit", str(limit),
    ]

    out = subprocess.run(args, capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        return []
    try:
        repos = json.loads(out.stdout)
    except json.JSONDecodeError:
        return []

    results: list[Candidate] = []
    for repo in repos:
        name = repo.get("name", "")
        full_name = repo.get("fullName", "")
        url = repo.get("url", "")
        results.append(Candidate(
            name=name,
            url=f"{url}.git" if url else "",
            source=f"{label}:{full_name}",
            has_skill_md=True,
        ))
    return results


# ── confluence knowledge scanner ──────────────────────────────────────────


@dataclass(frozen=True)
class KnowledgeEntry:
    title: str
    url: str
    source: str
    category: str  # "patterns", "decisions", or "errata"


KnowledgeProvider = Callable[[dict], list[KnowledgeEntry]]
_KNOWLEDGE_PROVIDERS: dict[str, KnowledgeProvider] = {}


def _register_knowledge_provider(kind: str):
    def decorate(fn: KnowledgeProvider) -> KnowledgeProvider:
        _KNOWLEDGE_PROVIDERS[kind] = fn
        return fn
    return decorate


@_register_knowledge_provider("confluence")
def _confluence(source: dict) -> list[KnowledgeEntry]:
    """Scan a Confluence space for automation-related pages."""
    base_url = source.get("base_url", "").rstrip("/")
    space = source.get("space", "")
    if not base_url or not space:
        return []
    label = f"confluence:{space}"

    headers = {"Accept": "application/json"}
    if (auth_env := source.get("auth_env")) and (tok := os.environ.get(auth_env)):
        headers["Authorization"] = f"Bearer {tok}"

    keywords = ("skill", "automation", "integration", "runbook", "playbook", "workflow")
    results: list[KnowledgeEntry] = []

    try:
        import urllib.request
        url = f"{base_url}/wiki/rest/api/content?spaceKey={space}&limit=100&expand=metadata.labels"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception:
        return []

    for page in data.get("results", []):
        title = page.get("title", "").lower()
        if any(kw in title for kw in keywords):
            page_url = f"{base_url}/wiki{page.get('_links', {}).get('webui', '')}"
            category = "patterns" if any(k in title for k in ("runbook", "playbook", "workflow")) else "errata"
            results.append(KnowledgeEntry(
                title=page.get("title", ""),
                url=page_url,
                source=label,
                category=category,
            ))
    return results


@_register_knowledge_provider("gitlab-wiki")
def _gitlab_wiki(source: dict) -> list[KnowledgeEntry]:
    """Scan GitLab project wikis for automation-related pages."""
    base_url = source.get("base_url", "https://gitlab.com").rstrip("/")
    group = source.get("group", "")
    if not group:
        return []
    label = f"gitlab-wiki:{group}"

    headers = {}
    if (auth_env := source.get("auth_env")) and (tok := os.environ.get(auth_env)):
        headers["PRIVATE-TOKEN"] = tok

    keywords = ("skill", "automation", "integration", "runbook", "playbook", "workflow")
    results: list[KnowledgeEntry] = []

    try:
        import urllib.request
        projects_url = f"{base_url}/api/v4/groups/{group.replace('/', '%2F')}/projects?per_page=50"
        req = urllib.request.Request(projects_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            projects = json.loads(resp.read())
    except Exception:
        return []

    for project in projects[:20]:
        pid = project.get("id")
        if not pid:
            continue
        try:
            wiki_url = f"{base_url}/api/v4/projects/{pid}/wikis"
            req = urllib.request.Request(wiki_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                pages = json.loads(resp.read())
        except Exception:
            continue
        for page in pages:
            title = page.get("title", "").lower()
            if any(kw in title for kw in keywords):
                slug = page.get("slug", "")
                page_url = f"{base_url}/{project.get('path_with_namespace', '')}/-/wikis/{slug}"
                category = "patterns" if any(k in title for k in ("runbook", "playbook")) else "errata"
                results.append(KnowledgeEntry(
                    title=page.get("title", ""),
                    url=page_url,
                    source=label,
                    category=category,
                ))
    return results


def scan_knowledge(*, namespace: str | None = None) -> list[KnowledgeEntry]:
    """Scan configured knowledge sources (Confluence, wiki) for relevant pages."""
    out: list[KnowledgeEntry] = []
    for src in sources():
        kind = src.get("kind")
        provider = _KNOWLEDGE_PROVIDERS.get(kind)
        if provider is None:
            continue
        try:
            out.extend(provider(src))
        except Exception as e:
            print(f"  warn: knowledge source {kind} failed: {e}", file=sys.stderr)
    return out


# ── helpers ─────────────────────────────────────────────────────────────────


def iter_kinds() -> Iterable[str]:
    return tuple(_PROVIDERS.keys())


# ── scan (continuous discovery) ────────────────────────────────────────────


DISCOVERY_DIR = os.path.expanduser("~/.geno/discovery")
CANDIDATES_FILE = os.path.join(DISCOVERY_DIR, "candidates.jsonl")


def scan(*, namespace: str | None = None, dry_run: bool = False) -> list[Candidate]:
    """Scan all sources, find uninstalled candidates, and write to queue.

    Returns the list of new candidates found.
    """
    from datetime import datetime, timezone

    all_candidates = candidates()
    if namespace:
        prefix = f"{namespace}-" if not namespace.endswith("-") else namespace
        all_candidates = [c for c in all_candidates if c.name.startswith(prefix)]

    installed = _get_installed_names()
    new = [c for c in all_candidates if c.has_skill_md and c.name not in installed]

    if not dry_run and new:
        os.makedirs(DISCOVERY_DIR, exist_ok=True)
        existing_names = _get_queued_names()
        with open(CANDIDATES_FILE, "a") as f:
            for c in new:
                if c.name in existing_names:
                    continue
                entry = json.dumps({
                    "name": c.name,
                    "url": c.url,
                    "source": c.source,
                    "discovered": datetime.now(timezone.utc).isoformat(),
                    "has_skill_md": c.has_skill_md,
                }, separators=(",", ":"))
                f.write(entry + "\n")

        with open(os.path.join(DISCOVERY_DIR, "last_scan"), "w") as f:
            f.write(datetime.now(timezone.utc).isoformat())

    return new


def _get_installed_names() -> set[str]:
    """Get names of currently installed skillsets."""
    from . import paths
    installed = set()
    if paths.ROOT.exists():
        for p in paths.ROOT.iterdir():
            if p.is_dir() and p.name.startswith("geno-"):
                installed.add(p.name)
    return installed


def _get_queued_names() -> set[str]:
    """Get names already in the candidate queue."""
    names = set()
    if os.path.exists(CANDIDATES_FILE):
        with open(CANDIDATES_FILE) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    names.add(entry.get("name", ""))
                except json.JSONDecodeError:
                    continue
    return names
