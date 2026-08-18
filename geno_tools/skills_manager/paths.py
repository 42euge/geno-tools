"""On-disk layout for managed skillset state.

Everything lives under ~/.geno-tools/. Each installed skillset gets its own
directory named with the full `geno-{name}` form:

    ~/.geno-tools/
    └── geno-{name}/                   # one per installed skillset
        ├── .git/                      # bare repo
        ├── main/                      # primary worktree
        ├── venvs/default/             # isolated Python runtime
        └── active -> main             # active skillset worktree symlink
"""

from pathlib import Path

HOME = Path.home()
ROOT = HOME / ".geno-tools"

GENO_DIR = HOME / ".geno"


def normalize(name: str) -> str:
    """Canonicalize to the `geno-{name}` form used on disk."""
    return name if name.startswith("geno-") else f"geno-{name}"


def skillset_root(name: str) -> Path:
    return ROOT / normalize(name)


def skillset_git(name: str) -> Path:
    return skillset_root(name) / ".git"


def skillset_worktree(name: str) -> Path:
    return skillset_root(name) / "main"


def skillset_active(name: str) -> Path:
    return skillset_root(name) / "active"


def skillset_venvs(name: str) -> Path:
    return skillset_root(name) / "venvs"
