"""Portable, Git-aware snapshots of active development checkouts."""

from __future__ import annotations

import base64
import binascii
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tarfile
import tempfile
from typing import Any

from geno_tools.skills_manager import paths
from geno_tools.skills_manager.commands import install


SNAPSHOT_VERSION = 1
ARTIFACT_NAMES = ("bundle", "cached_diff", "worktree_diff", "untracked_tar")
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "venvs",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
}
SECRET_NAMES = {".env", ".secrets"}


class SnapshotError(RuntimeError):
    """Raised when a development snapshot cannot be captured or trusted."""


@dataclass(frozen=True)
class SnapshotDescriptor:
    """Human- and machine-readable metadata for one captured checkout."""

    version: int
    machine: str
    captured: str
    source: str
    project_version: str
    branch: str | None
    commit: str
    origin: str | None
    dirty: dict[str, int | bool]
    fingerprint: str


@dataclass(frozen=True)
class _UntrackedEntry:
    name: str
    kind: str
    mode: int
    digest: str


def _run_git(
    checkout: Path, *arguments: str, text: bool = False
) -> str | bytes:
    try:
        return subprocess.check_output(
            ["git", "-C", str(checkout), *arguments],
            text=text,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SnapshotError(f"Git command failed in {checkout}: {' '.join(arguments)}") from exc


def _git_text(checkout: Path, *arguments: str) -> str:
    return str(_run_git(checkout, *arguments, text=True)).strip()


def _git_bytes(checkout: Path, *arguments: str) -> bytes:
    value = _run_git(checkout, *arguments)
    if not isinstance(value, bytes):  # pragma: no cover - guarded by text=False
        raise SnapshotError("Git returned text where bytes were required")
    return value


def _excluded(name: str) -> bool:
    path = PurePosixPath(name)
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return True
    basename = path.name
    return basename in SECRET_NAMES or basename.startswith(".env.")


def _untracked_names(checkout: Path) -> list[str]:
    raw = _git_bytes(
        checkout, "ls-files", "--others", "--exclude-standard", "-z", "--"
    )
    names = [os.fsdecode(item) for item in raw.split(b"\0") if item]
    return sorted(name for name in names if not _excluded(name))


def _safe_link(name: str, target: str) -> bool:
    link = PurePosixPath(target)
    if link.is_absolute() or not target or "\\" in target:
        return False
    depth = len(PurePosixPath(name).parent.parts)
    for part in link.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            depth -= 1
            if depth < 0:
                return False
        else:
            depth += 1
    return True


def _untracked_entries(checkout: Path) -> list[_UntrackedEntry]:
    entries: list[_UntrackedEntry] = []
    for name in _untracked_names(checkout):
        source = checkout / name
        try:
            details = source.lstat()
        except OSError as exc:
            raise SnapshotError(f"could not inspect untracked file {source}: {exc}") from exc
        mode = stat.S_IMODE(details.st_mode)
        if stat.S_ISREG(details.st_mode):
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            kind = "file"
        elif stat.S_ISLNK(details.st_mode):
            target = os.readlink(source)
            if not _safe_link(name, target):
                raise SnapshotError(f"unsafe symlink target for {name}: {target}")
            digest = hashlib.sha256(os.fsencode(target)).hexdigest()
            kind = "symlink"
        else:
            raise SnapshotError(f"unsupported untracked file type: {source}")
        entries.append(_UntrackedEntry(name, kind, mode, digest))
    return entries


def _fingerprint_parts(
    commit: str,
    cached_diff: bytes,
    worktree_diff: bytes,
    entries: list[_UntrackedEntry],
) -> str:
    digest = hashlib.sha256()
    for value in (
        b"geno-tools-dev-snapshot-v1\0",
        commit.encode("ascii"),
        cached_diff,
        worktree_diff,
        json.dumps(
            [asdict(entry) for entry in entries],
            sort_keys=True,
            separators=(",", ":"),
        ).encode(),
    ):
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
    return digest.hexdigest()


def fingerprint(checkout: Path) -> str:
    """Return a path-independent digest of every portable Git state layer."""
    source = checkout.expanduser().resolve()
    commit = _git_text(source, "rev-parse", "HEAD")
    cached = _git_bytes(source, "diff", "--cached", "--binary", "HEAD", "--")
    worktree = _git_bytes(source, "diff", "--binary", "--")
    return _fingerprint_parts(commit, cached, worktree, _untracked_entries(source))


def _untracked_archive(checkout: Path, entries: list[_UntrackedEntry]) -> bytes:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        for entry in entries:
            source = checkout / entry.name
            member = tarfile.TarInfo(entry.name)
            member.mode = entry.mode
            member.mtime = 0
            member.uid = member.gid = 0
            member.uname = member.gname = ""
            if entry.kind == "symlink":
                member.type = tarfile.SYMTYPE
                member.linkname = os.readlink(source)
                archive.addfile(member)
            else:
                content = source.read_bytes()
                member.type = tarfile.REGTYPE
                member.size = len(content)
                archive.addfile(member, io.BytesIO(content))
    return stream.getvalue()


def _project_version(checkout: Path) -> str:
    project = install._read_project(checkout).get("project") or {}
    return str(
        install._read_manifest_at(checkout).get("version")
        or project.get("version")
        or "?"
    )


def _optional_git(checkout: Path, *arguments: str) -> str | None:
    try:
        value = subprocess.check_output(
            ["git", "-C", str(checkout), *arguments],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return value or None


def _bundle(checkout: Path) -> bytes:
    with tempfile.TemporaryDirectory(prefix="geno-snapshot-bundle-") as temporary:
        destination = Path(temporary) / "snapshot.bundle"
        try:
            subprocess.run(
                ["git", "-C", str(checkout), "bundle", "create", str(destination), "HEAD"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise SnapshotError(f"could not create Git bundle for {checkout}") from exc
        return destination.read_bytes()


def _encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def capture(checkout: Path, *, machine: str) -> dict[str, Any]:
    """Capture committed, staged, unstaged, and safe untracked checkout state."""
    source = checkout.expanduser().resolve()
    if not source.is_dir():
        raise SnapshotError(f"checkout does not exist: {source}")
    commit = _git_text(source, "rev-parse", "HEAD")
    branch = _optional_git(source, "branch", "--show-current")
    cached = _git_bytes(source, "diff", "--cached", "--binary", "HEAD", "--")
    worktree = _git_bytes(source, "diff", "--binary", "--")
    entries = _untracked_entries(source)
    descriptor = SnapshotDescriptor(
        version=SNAPSHOT_VERSION,
        machine=machine,
        captured=datetime.now(timezone.utc).isoformat(),
        source=str(source),
        project_version=_project_version(source),
        branch=branch,
        commit=commit,
        origin=_optional_git(source, "remote", "get-url", "origin"),
        dirty={
            "cached": bool(cached),
            "worktree": bool(worktree),
            "untracked": len(entries),
        },
        fingerprint=_fingerprint_parts(commit, cached, worktree, entries),
    )
    return {
        **asdict(descriptor),
        "artifacts": {
            "bundle": _encode(_bundle(source)),
            "cached_diff": _encode(cached),
            "worktree_diff": _encode(worktree),
            "untracked_tar": _encode(_untracked_archive(source, entries)),
        },
    }


def encoded_size(payload: dict[str, Any]) -> int:
    """Return the number of base64 bytes carried by a snapshot payload."""
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        raise SnapshotError("snapshot artifacts are missing")
    values = [artifacts.get(name) for name in ARTIFACT_NAMES]
    if not all(isinstance(value, str) for value in values):
        raise SnapshotError("snapshot artifacts have an unsupported schema")
    return sum(len(value.encode("ascii")) for value in values)


def _decode_artifacts(payload: dict[str, Any]) -> dict[str, bytes]:
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        raise SnapshotError("snapshot artifacts are missing")
    decoded: dict[str, bytes] = {}
    for name in ARTIFACT_NAMES:
        value = artifacts.get(name)
        if not isinstance(value, str):
            raise SnapshotError(f"snapshot artifact is missing: {name}")
        try:
            decoded[name] = base64.b64decode(value, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise SnapshotError(f"invalid base64 in snapshot artifact: {name}") from exc
    return decoded


def _archive_members(value: bytes) -> list[tarfile.TarInfo]:
    try:
        with tarfile.open(fileobj=io.BytesIO(value), mode="r:*") as archive:
            members = archive.getmembers()
    except (tarfile.TarError, OSError) as exc:
        raise SnapshotError(f"invalid untracked archive: {exc}") from exc

    names: set[str] = set()
    symlinks: set[PurePosixPath] = set()
    for member in members:
        path = PurePosixPath(member.name)
        if (
            not member.name
            or path.is_absolute()
            or member.name != path.as_posix()
            or ".." in path.parts
            or "\\" in member.name
        ):
            raise SnapshotError(f"unsafe archive path: {member.name}")
        if member.name in names:
            raise SnapshotError(f"duplicate archive path: {member.name}")
        names.add(member.name)
        if not (member.isreg() or member.issym()):
            raise SnapshotError(f"unsafe archive entry type: {member.name}")
        if any(parent in symlinks for parent in path.parents):
            raise SnapshotError(f"archive path traverses a symlink: {member.name}")
        if member.issym():
            if not _safe_link(member.name, member.linkname):
                raise SnapshotError(
                    f"unsafe symlink target for {member.name}: {member.linkname}"
                )
            symlinks.add(path)
    return members


def _safe_parent(checkout: Path, destination: Path) -> None:
    relative = destination.relative_to(checkout)
    current = checkout
    for part in relative.parts[:-1]:
        current /= part
        if current.is_symlink():
            raise SnapshotError(f"archive path traverses a symlink: {relative}")
        if current.exists() and not current.is_dir():
            raise SnapshotError(f"archive parent is not a directory: {relative}")
        current.mkdir(exist_ok=True)


def _extract_archive(checkout: Path, value: bytes, members: list[tarfile.TarInfo]) -> None:
    with tarfile.open(fileobj=io.BytesIO(value), mode="r:*") as archive:
        for member in members:
            destination = checkout / member.name
            _safe_parent(checkout, destination)
            if destination.exists() or destination.is_symlink():
                raise SnapshotError(f"archive path already exists: {member.name}")
            if member.issym():
                destination.symlink_to(member.linkname)
                continue
            source = archive.extractfile(member)
            if source is None:
                raise SnapshotError(f"archive content is missing: {member.name}")
            with destination.open("xb") as output:
                shutil.copyfileobj(source, output)
            destination.chmod(member.mode & 0o777)


def _validate_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict) or payload.get("version") != SNAPSHOT_VERSION:
        raise SnapshotError("unsupported snapshot version")
    for name in ("machine", "captured", "source", "project_version", "commit"):
        if not isinstance(payload.get(name), str):
            raise SnapshotError(f"invalid snapshot field: {name}")
    if payload.get("branch") is not None and not isinstance(payload.get("branch"), str):
        raise SnapshotError("invalid snapshot field: branch")
    expected = payload.get("fingerprint")
    if (
        not isinstance(expected, str)
        or len(expected) != 64
        or any(character not in "0123456789abcdef" for character in expected)
    ):
        raise SnapshotError("invalid snapshot field: fingerprint")


def validate(payload: dict[str, Any]) -> None:
    """Validate snapshot metadata and base64 artifact structure without mutation."""
    _validate_payload(payload)
    _decode_artifacts(payload)


def _apply_patch(checkout: Path, patch: Path, *, cached: bool) -> None:
    if patch.stat().st_size == 0:
        return
    command = ["git", "-C", str(checkout), "apply", "--binary", "--whitespace=nowarn"]
    if cached:
        command.append("--index")
    command.append(str(patch))
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SnapshotError(
            f"could not apply {'cached' if cached else 'working-tree'} snapshot diff"
        ) from exc


def materialize(full: str, payload: dict[str, Any]) -> Path:
    """Validate and reconstruct a snapshot under the managed skillset root."""
    _validate_payload(payload)
    artifacts = _decode_artifacts(payload)
    members = _archive_members(artifacts["untracked_tar"])
    expected = payload["fingerprint"]
    parent = paths.skillset_root(full) / "snapshots"
    destination = parent / expected
    if destination.is_dir():
        if fingerprint(destination) != expected:
            raise SnapshotError(f"managed snapshot fingerprint mismatch: {destination}")
        return destination
    parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=".snapshot-", dir=parent) as temporary:
        staging = Path(temporary)
        bundle = staging / "snapshot.bundle"
        bundle.write_bytes(artifacts["bundle"])
        verify = staging / "verify"
        try:
            subprocess.run(
                ["git", "-C", str(staging), "init", "-q", str(verify)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            subprocess.run(
                ["git", "-C", str(verify), "bundle", "verify", str(bundle)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise SnapshotError("invalid Git bundle") from exc

        checkout = staging / "checkout"
        try:
            subprocess.run(
                ["git", "clone", "-q", "--no-checkout", str(bundle), str(checkout)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            branch = payload.get("branch")
            switch = ["git", "-C", str(checkout), "checkout", "-q"]
            if branch:
                switch.extend(["-B", branch])
            else:
                switch.append("--detach")
            switch.append(payload["commit"])
            subprocess.run(
                switch,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise SnapshotError("Git bundle does not contain the recorded commit") from exc

        cached_patch = staging / "cached.patch"
        cached_patch.write_bytes(artifacts["cached_diff"])
        worktree_patch = staging / "worktree.patch"
        worktree_patch.write_bytes(artifacts["worktree_diff"])
        _apply_patch(checkout, cached_patch, cached=True)
        _apply_patch(checkout, worktree_patch, cached=False)
        _extract_archive(checkout, artifacts["untracked_tar"], members)

        actual = fingerprint(checkout)
        if actual != expected:
            raise SnapshotError(
                f"snapshot fingerprint mismatch: expected {expected}, reconstructed {actual}"
            )
        os.replace(checkout, destination)
    return destination
