"""Resolve geno-tt host aliases and execute local or SSH commands."""

from __future__ import annotations

import shlex
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path


TT_CONFIG_FILE = Path.home() / ".geno" / "tt" / "config.toml"


class TransportError(RuntimeError):
    """Host configuration or command execution could not be used."""


@dataclass(frozen=True)
class Host:
    alias: str
    destination: str
    local: bool


@dataclass(frozen=True)
class HostRegistry:
    default_host: str | None
    hosts: dict[str, Host]


def load_host_registry(path: Path | None = None) -> HostRegistry:
    """Read the public geno-tt host registry contract."""
    source = path or TT_CONFIG_FILE
    try:
        value = tomllib.loads(source.read_text())
    except FileNotFoundError as error:
        raise TransportError(
            f"geno-tt host config not found at {source}; add one with 'tt add-host'"
        ) from error
    except OSError as error:
        raise TransportError(f"cannot read geno-tt host config {source}: {error}") from error
    except tomllib.TOMLDecodeError as error:
        raise TransportError(f"invalid geno-tt host config {source}: {error}") from error

    raw_hosts = value.get("hosts")
    if not isinstance(raw_hosts, dict) or not raw_hosts:
        raise TransportError(
            f"geno-tt host config {source} has no hosts; add one with 'tt add-host'"
        )
    hosts: dict[str, Host] = {}
    for alias, destination in raw_hosts.items():
        if not isinstance(alias, str) or not isinstance(destination, str):
            raise TransportError("each geno-tt host alias needs a string destination")
        hosts[alias] = Host(alias, destination, destination == "localhost")

    default = value.get("default_host")
    if default is not None and not isinstance(default, str):
        raise TransportError("geno-tt default_host must be a host alias string")
    return HostRegistry(default, hosts)


def resolve_host(alias: str, registry: HostRegistry) -> Host:
    try:
        return registry.hosts[alias]
    except KeyError as error:
        available = ", ".join(sorted(registry.hosts))
        raise TransportError(
            f"unknown host alias {alias!r}; configured hosts: {available}"
        ) from error


def run(
    host: Host,
    command: list[str],
    *,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Execute a command locally or through one outbound SSH connection."""
    argv = command if host.local else ["ssh", host.destination, shlex.join(command)]
    try:
        return subprocess.run(
            argv,
            text=True,
            capture_output=True,
            input=input_text,
            check=False,
        )
    except OSError as error:
        raise TransportError(f"cannot run command for host {host.alias!r}: {error}") from error
