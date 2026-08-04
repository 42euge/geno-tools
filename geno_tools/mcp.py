"""MCP catalog adapter.

Profiles reference MCP servers by *catalog name* (e.g. ``core``, ``gitlab``).
This module resolves those names to concrete server specs and writes an
agent-consumable MCP config (``.mcp.json``: ``{"mcpServers": {...}}``).

Provider layer (mirrors ``discovery._PROVIDERS``). A provider implements::

    def catalog(source: dict) -> dict[str, ServerSpec]: ...

returning ``{catalog_name: spec}``. Configured sources live under
``config.mcp_catalogs.sources`` (same shape as ``discovery.sources``).

PROPRIETARY ISOLATION. The public repo ships only generic providers
(``file``, ``env``). A private catalog (e.g. Blue Origin's) must NOT appear
here — instead it self-registers: on first use we scan every installed
skillset's ``active/`` dir for an ``mcp_provider.py`` and import it; that
module calls ``register_catalog(kind)`` to add itself. So no proprietary
name/URL/token ever lands in ``geno_tools/**`` (a CI grep enforces this).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Callable

import yaml

from geno_tools import config, paths

# A server spec is the value side of Claude Code's mcpServers map. We stay
# schema-agnostic: providers return whatever the agent needs (command/args/env
# for stdio, or url/transport/headers for http). We only require a name key.
ServerSpec = dict

CatalogProvider = Callable[[dict], "dict[str, ServerSpec]"]
_CATALOG_PROVIDERS: dict[str, CatalogProvider] = {}
_discovered = False


def register_catalog(kind: str):
    """Register a catalog provider for ``kind``. Usable as a decorator.

    Private skillsets call this from their ``mcp_provider.py`` to plug a
    proprietary catalog in without the public repo referencing them.
    """
    def decorate(fn: CatalogProvider) -> CatalogProvider:
        _CATALOG_PROVIDERS[kind] = fn
        return fn
    return decorate


# ── generic built-in providers ───────────────────────────────────────────────

@register_catalog("file")
def _file_catalog(source: dict) -> dict[str, ServerSpec]:
    """Read a local YAML catalog: ``{name: {<<spec>>}}`` (optionally nested
    under a top-level ``servers:`` key)."""
    path = source.get("path")
    if not path:
        return {}
    p = Path(path).expanduser()
    if not p.exists():
        return {}
    data = yaml.safe_load(p.read_text()) or {}
    if isinstance(data, dict) and "servers" in data:
        data = data["servers"]
    return data if isinstance(data, dict) else {}


@register_catalog("env")
def _env_catalog(source: dict) -> dict[str, ServerSpec]:
    """Read a JSON catalog from an env var named by ``var``."""
    import os
    raw = os.environ.get(source.get("var", ""), "")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


# ── discovery of private provider modules ─────────────────────────────────────

def _discover_provider_modules() -> None:
    """Import ``mcp_provider.py`` from every installed skillset's active dir.

    Each such module self-registers via ``register_catalog``. Import errors
    are swallowed (a broken private provider must not break the public tool).
    """
    global _discovered
    if _discovered:
        return
    _discovered = True
    if not paths.ROOT.exists():
        return
    for skillset in sorted(paths.ROOT.glob("geno-*")):
        provider = skillset / "active" / "mcp_provider.py"
        if not provider.exists():
            continue
        mod_name = f"_geno_mcp_provider_{skillset.name.replace('-', '_')}"
        try:
            spec = importlib.util.spec_from_file_location(mod_name, provider)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = module
                spec.loader.exec_module(module)
        except Exception as e:  # noqa: BLE001
            print(f"  warn: MCP provider {provider} failed to load: {e}",
                  file=sys.stderr)


# ── public api ────────────────────────────────────────────────────────────────

def sources() -> list[dict]:
    """Configured MCP catalog sources (config.mcp_catalogs.sources)."""
    return list(config.load().get("mcp_catalogs", {}).get("sources", []))


def full_catalog() -> dict[str, ServerSpec]:
    """Union of every configured source's catalog. Later sources win on
    name collision."""
    _discover_provider_modules()
    catalog: dict[str, ServerSpec] = {}
    for src in sources():
        kind = src.get("kind")
        provider = _CATALOG_PROVIDERS.get(kind)
        if provider is None:
            print(f"  warn: no MCP catalog provider for kind '{kind}'",
                  file=sys.stderr)
            continue
        try:
            catalog.update(provider(src))
        except Exception as e:  # noqa: BLE001
            print(f"  warn: MCP catalog source {kind} failed: {e}",
                  file=sys.stderr)
    return catalog


def resolve_mcp(names: list[str]) -> dict[str, ServerSpec]:
    """Resolve catalog names to concrete server specs.

    Raises KeyError listing any names not found in the union catalog, so the
    caller (launch) fails loudly rather than silently dropping a server.
    """
    if not names:
        return {}
    catalog = full_catalog()
    missing = [n for n in names if n not in catalog]
    if missing:
        available = ", ".join(sorted(catalog)) or "(none — configure mcp_catalogs.sources)"
        raise KeyError(
            f"MCP catalog name(s) not found: {', '.join(missing)}\n"
            f"  available: {available}"
        )
    return {n: catalog[n] for n in names}


def write_mcp_config(specs: dict[str, ServerSpec], out_path: Path) -> Path:
    """Write specs to an agent-consumable .mcp.json (mcpServers map)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"mcpServers": specs}, indent=2) + "\n")
    return out_path
