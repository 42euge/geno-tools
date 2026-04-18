"""Install ledger at ~/.geno-tools/linkdb.json.

Tracks every path we created or modified per skillset so `remove` is a pure
replay-in-reverse — no filesystem guessing.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from genotools.paths import LINKDB, ROOT


@dataclass
class SkillsetEntry:
    name: str                      # e.g. "media" (no geno- prefix)
    source: str                    # git URL or local path
    mode: str                      # "git" | "dev"
    agents: list[str] = field(default_factory=list)
    # Paths we created — removed on uninstall. Order matters (reverse on remove).
    links: list[str] = field(default_factory=list)
    # Config files we copied. Removed only if --keep-data is NOT set.
    configs: list[str] = field(default_factory=list)


@dataclass
class LinkDB:
    entries: dict[str, SkillsetEntry] = field(default_factory=dict)

    def skillsets(self) -> list[SkillsetEntry]:
        return list(self.entries.values())

    def get(self, name: str) -> SkillsetEntry | None:
        return self.entries.get(name)

    def put(self, entry: SkillsetEntry) -> None:
        self.entries[entry.name] = entry

    def drop(self, name: str) -> SkillsetEntry | None:
        return self.entries.pop(name, None)


def load() -> LinkDB:
    if not LINKDB.exists():
        return LinkDB()
    raw = json.loads(LINKDB.read_text())
    entries = {
        name: SkillsetEntry(**data) for name, data in raw.get("entries", {}).items()
    }
    return LinkDB(entries=entries)


def save(db: LinkDB) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    payload = {"entries": {name: asdict(e) for name, e in db.entries.items()}}
    LINKDB.write_text(json.dumps(payload, indent=2))


def record_link(entry: SkillsetEntry, path: Path) -> None:
    entry.links.append(str(path))


def record_config(entry: SkillsetEntry, path: Path) -> None:
    entry.configs.append(str(path))
