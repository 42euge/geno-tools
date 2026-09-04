import base64
import copy
import io
import os
from pathlib import Path
import subprocess
import tarfile

import pytest

from geno_tools.sync import snapshot


def git(repository: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repository), *arguments], text=True
    ).strip()


def git_bytes(repository: Path, *arguments: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repository), *arguments])


def commit(repository: Path, message: str) -> str:
    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "-c",
            "user.name=Snapshot Test",
            "-c",
            "user.email=snapshot@example.test",
            "commit",
            "-q",
            "-m",
            message,
        ],
        check=True,
    )
    return git(repository, "rev-parse", "HEAD")


def make_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "checkout"
    repository.mkdir()
    subprocess.run(
        ["git", "-C", str(repository), "init", "-q", "-b", "feature/snapshot"],
        check=True,
    )
    (repository / ".gitignore").write_text(".env\n.cache/\n")
    (repository / "mixed.txt").write_text("base one\nbase two\n")
    (repository / "deleted.txt").write_text("remove me\n")
    (repository / "run.sh").write_text("#!/bin/sh\necho base\n")
    (repository / "pyproject.toml").write_text(
        '[project]\nname = "geno-snapshot"\nversion = "1.2.3"\n'
    )
    subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
    commit(repository, "published base")

    origin = tmp_path / "origin.git"
    subprocess.run(
        ["git", "clone", "-q", "--bare", str(repository), str(origin)], check=True
    )
    subprocess.run(
        ["git", "-C", str(repository), "remote", "add", "origin", str(origin)],
        check=True,
    )

    (repository / "unpublished.txt").write_text("only in the snapshot\n")
    subprocess.run(
        ["git", "-C", str(repository), "add", "unpublished.txt"], check=True
    )
    commit(repository, "unpublished commit")
    return repository


def dirty_repository(repository: Path) -> None:
    (repository / "mixed.txt").write_text("staged one\nbase two\n")
    subprocess.run(
        ["git", "-C", str(repository), "add", "mixed.txt"], check=True
    )
    (repository / "mixed.txt").write_text("staged one\nunstaged two\n")
    (repository / "deleted.txt").unlink()
    (repository / "run.sh").chmod(0o755)
    subprocess.run(["git", "-C", str(repository), "add", "run.sh"], check=True)

    (repository / "notes.txt").write_text("portable notes\n")
    (repository / "executable-untracked").write_text("#!/bin/sh\nexit 0\n")
    (repository / "executable-untracked").chmod(0o755)
    (repository / "notes-link").symlink_to("notes.txt")
    (repository / ".env").write_text("TOKEN=do-not-copy\n")
    (repository / ".cache").mkdir()
    (repository / ".cache" / "generated").write_text("do-not-copy\n")


def test_snapshot_round_trip_preserves_every_git_layer(
    tmp_path, tmp_root
):
    source = make_repository(tmp_path)
    dirty_repository(source)

    payload = snapshot.capture(source, machine="laptop")
    restored = snapshot.materialize("geno-snapshot", payload)

    assert git(restored, "rev-parse", "HEAD") == git(source, "rev-parse", "HEAD")
    assert git(restored, "branch", "--show-current") == "feature/snapshot"
    assert git_bytes(restored, "diff", "--cached", "--binary", "HEAD", "--") == (
        git_bytes(source, "diff", "--cached", "--binary", "HEAD", "--")
    )
    assert git_bytes(restored, "diff", "--binary", "--") == git_bytes(
        source, "diff", "--binary", "--"
    )
    assert not (restored / "deleted.txt").exists()
    assert (restored / "notes.txt").read_text() == "portable notes\n"
    assert (restored / "executable-untracked").stat().st_mode & 0o777 == 0o755
    assert (restored / "notes-link").is_symlink()
    assert os.readlink(restored / "notes-link") == "notes.txt"
    assert not (restored / ".env").exists()
    assert not (restored / ".cache").exists()
    assert payload["commit"] != git(
        tmp_path / "origin.git", "rev-parse", "refs/heads/feature/snapshot"
    )
    assert snapshot.fingerprint(restored) == snapshot.fingerprint(source)
    assert payload["fingerprint"] == snapshot.fingerprint(source)
    assert snapshot.encoded_size(payload) > 0


def clean_payload(tmp_path: Path) -> dict:
    repository = make_repository(tmp_path)
    return snapshot.capture(repository, machine="laptop")


def archive_with(member: tarfile.TarInfo, content: bytes = b"") -> str:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        if member.isreg():
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
        else:
            archive.addfile(member)
    return base64.b64encode(stream.getvalue()).decode("ascii")


@pytest.mark.parametrize("name", ["/tmp/geno-outside", "../../geno-outside"])
def test_materialize_rejects_absolute_and_traversal_archive_names(
    name, tmp_path, tmp_root
):
    payload = clean_payload(tmp_path)
    member = tarfile.TarInfo(name)
    member.type = tarfile.REGTYPE
    payload["artifacts"]["untracked_tar"] = archive_with(member, b"unsafe")

    with pytest.raises(snapshot.SnapshotError, match="unsafe archive path"):
        snapshot.materialize("geno-snapshot", payload)

    assert not (tmp_path / "geno-outside").exists()


def test_materialize_rejects_archive_device_entries(tmp_path, tmp_root):
    payload = clean_payload(tmp_path)
    member = tarfile.TarInfo("device")
    member.type = tarfile.CHRTYPE
    payload["artifacts"]["untracked_tar"] = archive_with(member)

    with pytest.raises(snapshot.SnapshotError, match="unsafe archive entry"):
        snapshot.materialize("geno-snapshot", payload)


def test_materialize_rejects_unsafe_symlink_targets(tmp_path, tmp_root):
    payload = clean_payload(tmp_path)
    member = tarfile.TarInfo("link")
    member.type = tarfile.SYMTYPE
    member.linkname = "../../outside"
    payload["artifacts"]["untracked_tar"] = archive_with(member)

    with pytest.raises(snapshot.SnapshotError, match="unsafe symlink target"):
        snapshot.materialize("geno-snapshot", payload)


def test_materialize_rejects_malformed_base64(tmp_path, tmp_root):
    payload = clean_payload(tmp_path)
    payload["artifacts"]["cached_diff"] = "%%%"

    with pytest.raises(snapshot.SnapshotError, match="invalid base64"):
        snapshot.materialize("geno-snapshot", payload)


def test_materialize_rejects_invalid_git_bundles(tmp_path, tmp_root):
    payload = clean_payload(tmp_path)
    payload["artifacts"]["bundle"] = base64.b64encode(b"not a bundle").decode()

    with pytest.raises(snapshot.SnapshotError, match="invalid Git bundle"):
        snapshot.materialize("geno-snapshot", payload)


def test_materialize_rejects_mismatched_fingerprints(tmp_path, tmp_root):
    payload = copy.deepcopy(clean_payload(tmp_path))
    payload["fingerprint"] = "0" * 64

    with pytest.raises(snapshot.SnapshotError, match="fingerprint mismatch"):
        snapshot.materialize("geno-snapshot", payload)
