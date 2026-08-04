"""Profile store + resolver.

A *profile* is a named bundle that scopes one launched CLI session: which
skills (at which variant), which MCP catalog names, and which agents it may
target. Profiles are standalone YAML files under ~/.geno/profiles/*.yaml.

The four built-in bundles ported from geno-iso (bare/base/standard/full) are
available as profiles without a file on disk; a same-named file overrides the
built-in.

`resolve(name)` lowers a profile to a concrete plan:
    {
      "name": "eng",
      "agents": ["claude-code", "codex"],
      "skills": [{"name": "geno-notes", "variant": "wiki-v2",
                  "worktree": Path(...)}],
      "mcp": ["core", "gitlab"],          # catalog names; specs resolved by mcp.py
      "autonomy": 1 | None,
      "missing": ["geno-foo"],            # referenced but not installed
    }

The MCP *names* are resolved here; turning them into concrete server specs is
mcp.resolve_mcp()'s job (kept separate so the store has no catalog coupling).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from geno_tools import paths
from geno_tools.iso import profiles as builtin

# Agents npx skills can target (used to validate a profile's `agents` list and
# `launch --agent`). Kept here so the profile layer owns agent identity.
KNOWN_AGENTS: dict[str, str] = {
    "claude-code": "~/.claude/skills",
    "codex": "~/.codex/skills",
    "cursor": "~/.cursor/skills",
    "antigravity": "~/.gemini/antigravity/skills",
    "gemini-cli": "~/.gemini/skills",
    "github-copilot": "~/.copilot/skills",
    "opencode": "~/.config/opencode/skills",
}


class ProfileError(Exception):
    """Raised when a profile is unknown or malformed."""


def profile_path(name: str) -> Path:
    return paths.PROFILES_DIR / f"{name}.yaml"


def list_profiles() -> list[str]:
    """All available profile names: built-ins plus any on-disk YAML files."""
    names = set(builtin.NAMES)
    if paths.PROFILES_DIR.exists():
        for p in paths.PROFILES_DIR.glob("*.yaml"):
            names.add(p.stem)
    return sorted(names)


def load(name: str) -> dict:
    """Load a raw profile dict. On-disk file wins over a built-in bundle.

    Built-ins are lowered to the profile schema: their skillset list becomes
    `skills` entries (variant defaults to main), agents default to all known.
    """
    path = profile_path(name)
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError as e:
            raise ProfileError(f"malformed profile {name}: {e}") from e
        if not isinstance(data, dict):
            raise ProfileError(f"profile {name} is not a mapping")
        return _normalize(name, data)

    if name in builtin.BUILTIN:
        b = builtin.BUILTIN[name]
        return _normalize(name, {
            "agents": list(KNOWN_AGENTS),
            "skills": [{"name": s} for s in b.skillsets],
            "mcp": [],
        })

    raise ProfileError(
        f"unknown profile: {name}\n  available: {', '.join(list_profiles())}"
    )


def _normalize(name: str, data: dict) -> dict:
    """Coerce a raw profile mapping into the canonical shape."""
    agents = data.get("agents") or list(KNOWN_AGENTS)
    if isinstance(agents, str):
        agents = [agents]

    skills: list[dict] = []
    for entry in data.get("skills") or []:
        if isinstance(entry, str):
            skills.append({"name": entry, "variant": "main", "version": None})
        elif isinstance(entry, dict) and entry.get("name"):
            skills.append({
                "name": entry["name"],
                "variant": entry.get("variant", "main"),
                "version": entry.get("version"),
            })
        else:
            raise ProfileError(
                f"profile {name}: skill entry must be a name or "
                f"{{name, variant?, version?}}, got {entry!r}"
            )

    mcp = data.get("mcp") or []
    if isinstance(mcp, str):
        mcp = [mcp]

    return {
        "name": name,
        "agents": list(agents),
        "skills": skills,
        "mcp": list(mcp),
        "autonomy": data.get("autonomy"),
    }


def resolve(name: str) -> dict:
    """Lower a profile to a concrete plan (see module docstring).

    Each skill is mapped to the worktree path for its pinned variant. Skills
    whose skillset isn't installed are collected under `missing` rather than
    raising — the caller (launch) decides whether to auto-install or error.
    """
    prof = load(name)

    # Validate agent names early.
    unknown = [a for a in prof["agents"] if a not in KNOWN_AGENTS]
    if unknown:
        raise ProfileError(
            f"profile {name}: unknown agent(s) {unknown}; "
            f"known: {', '.join(KNOWN_AGENTS)}"
        )

    resolved_skills: list[dict] = []
    missing: list[str] = []
    for s in prof["skills"]:
        full = paths.normalize(s["name"])
        if not paths.skillset_root(full).exists():
            missing.append(full)
            continue
        wt = paths.skillset_worktree(full, s["variant"])
        resolved_skills.append({
            "name": full,
            "variant": s["variant"],
            "version": s["version"],
            "worktree": wt,
            "worktree_exists": wt.exists(),
        })

    return {
        "name": name,
        "agents": prof["agents"],
        "skills": resolved_skills,
        "mcp": prof["mcp"],
        "autonomy": prof["autonomy"],
        "missing": missing,
    }
