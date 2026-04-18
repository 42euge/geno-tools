from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class LinkSpec:
    src: str
    dst: str
    recursive: bool = False


@dataclass
class VenvSpec:
    python: str = ">=3.10"
    deps: list[str] = field(default_factory=list)
    name: str = "default"


@dataclass
class Manifest:
    name: str
    version: str
    description: str
    venv: VenvSpec | None = None
    runtime: list[LinkSpec] = field(default_factory=list)
    config: list[LinkSpec] = field(default_factory=list)
    commands_src: str = "commands/"

    @property
    def full_name(self) -> str:
        return f"geno-{self.name}"


def load(repo_dir: Path) -> Manifest:
    path = repo_dir / "genotools.yaml"
    if not path.exists():
        raise FileNotFoundError(f"missing {path}")
    data = yaml.safe_load(path.read_text()) or {}
    return _from_dict(data)


def _from_dict(data: dict) -> Manifest:
    for required in ("name", "version", "description"):
        if required not in data:
            raise ValueError(f"genotools.yaml missing required field: {required}")

    venv = None
    if "venv" in data:
        v = data["venv"]
        venv = VenvSpec(
            python=v.get("python", ">=3.10"),
            deps=list(v.get("deps", [])),
            name=v.get("name", "default"),
        )

    runtime = [_link(x) for x in data.get("runtime", [])]
    config = [_link(x) for x in data.get("config", [])]
    commands_src = (data.get("commands") or {}).get("source", "commands/")

    return Manifest(
        name=data["name"].removeprefix("geno-"),
        version=str(data["version"]),
        description=data["description"],
        venv=venv,
        runtime=runtime,
        config=config,
        commands_src=commands_src,
    )


def _link(raw: dict) -> LinkSpec:
    return LinkSpec(
        src=raw["src"],
        dst=raw["dst"],
        recursive=bool(raw.get("recursive", False)),
    )
