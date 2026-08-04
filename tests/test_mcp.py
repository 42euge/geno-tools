"""Tests for the MCP catalog adapter + the proprietary-isolation guarantee."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from geno_tools import mcp


@pytest.fixture(autouse=True)
def reset_registry(monkeypatch):
    """Each test starts from only the built-in providers, no discovery."""
    monkeypatch.setattr(mcp, "_discovered", True)  # skip module discovery
    # keep file/env providers, drop any test-registered ones
    monkeypatch.setattr(mcp, "_CATALOG_PROVIDERS",
                        {"file": mcp._file_catalog, "env": mcp._env_catalog})


def _catalog_source(tmp_path: Path, servers: dict) -> dict:
    p = tmp_path / "catalog.yaml"
    p.write_text(yaml.safe_dump(servers))
    return {"kind": "file", "path": str(p)}


class TestFileProvider:
    def test_resolves_names(self, tmp_path, monkeypatch):
        src = _catalog_source(tmp_path, {
            "core": {"url": "http://x/core"},
            "gitlab": {"url": "http://x/gitlab"},
        })
        monkeypatch.setattr(mcp, "sources", lambda: [src])
        specs = mcp.resolve_mcp(["core"])
        assert specs == {"core": {"url": "http://x/core"}}

    def test_servers_nesting(self, tmp_path, monkeypatch):
        p = tmp_path / "c.yaml"
        p.write_text(yaml.safe_dump({"servers": {"core": {"url": "u"}}}))
        monkeypatch.setattr(mcp, "sources", lambda: [{"kind": "file", "path": str(p)}])
        assert "core" in mcp.full_catalog()

    def test_missing_name_raises(self, tmp_path, monkeypatch):
        src = _catalog_source(tmp_path, {"core": {"url": "u"}})
        monkeypatch.setattr(mcp, "sources", lambda: [src])
        with pytest.raises(KeyError):
            mcp.resolve_mcp(["core", "nope"])

    def test_empty_names(self, monkeypatch):
        monkeypatch.setattr(mcp, "sources", lambda: [])
        assert mcp.resolve_mcp([]) == {}

    def test_later_source_wins(self, tmp_path, monkeypatch):
        p1 = tmp_path / "1.yaml"; p1.write_text(yaml.safe_dump({"core": {"url": "A"}}))
        p2 = tmp_path / "2.yaml"; p2.write_text(yaml.safe_dump({"core": {"url": "B"}}))
        monkeypatch.setattr(mcp, "sources", lambda: [
            {"kind": "file", "path": str(p1)},
            {"kind": "file", "path": str(p2)},
        ])
        assert mcp.full_catalog()["core"]["url"] == "B"


class TestWriteConfig:
    def test_writes_mcpservers_map(self, tmp_path):
        out = mcp.write_mcp_config({"core": {"url": "u"}}, tmp_path / ".mcp.json")
        data = json.loads(out.read_text())
        assert data == {"mcpServers": {"core": {"url": "u"}}}


class TestProviderDiscovery:
    def test_private_provider_self_registers(self, tmp_root, monkeypatch):
        """A skillset dropping active/mcp_provider.py plugs a catalog in."""
        monkeypatch.setattr(mcp, "_discovered", False)
        skillset = tmp_root / "geno-secret"
        active = skillset / "active"
        active.mkdir(parents=True)
        (active / "mcp_provider.py").write_text(
            "from geno_tools import mcp\n"
            "@mcp.register_catalog('secretkind')\n"
            "def _c(source):\n"
            "    return {'vault': {'url': 'http://internal/vault'}}\n"
        )
        monkeypatch.setattr(mcp, "sources", lambda: [{"kind": "secretkind"}])
        specs = mcp.resolve_mcp(["vault"])
        assert specs["vault"]["url"] == "http://internal/vault"


class TestProprietaryIsolation:
    def test_no_blue_origin_strings_in_package(self):
        """CI guard: no Blue Origin specifics may leak into geno_tools/**.

        The private catalog must plug in via a discovered provider module, not
        by hardcoding proprietary names/URLs/tokens in the public package.
        """
        pkg = Path(__file__).resolve().parent.parent / "geno_tools"
        pattern = re.compile(r"\b(blueorigin|leap\.blueorigin|okta|bgpat|blue_?origin)\b",
                             re.IGNORECASE)
        offenders = []
        for py in pkg.rglob("*.py"):
            text = py.read_text(errors="ignore")
            for m in pattern.finditer(text):
                offenders.append(f"{py.relative_to(pkg.parent)}: {m.group(0)}")
        assert not offenders, "proprietary strings found:\n" + "\n".join(offenders)
