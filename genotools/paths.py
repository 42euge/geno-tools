"""On-disk layout for geno-tools state.

Everything lives under ~/.geno-tools/. Each installed skillset gets its own
directory named with the full `geno-{name}` form:

    ~/.geno-tools/
    ├── .state-hash                    # bumped on any state change
    ├── geno-bootstrap/                # meta-plugin geno-tools owns
    └── geno-{name}/                   # one per installed skillset
        ├── .git/                      # bare repo
        ├── main/                      # primary worktree
        ├── .worktrees/<variant>/      # additional worktrees
        ├── venvs/<venv-name>/         # shared by default; per-worktree if isolated
        └── active -> main             # symlink; `geno-tools use` repoints this
"""

from pathlib import Path

HOME = Path.home()
ROOT = HOME / ".geno-tools"
STATE_HASH = ROOT / ".state-hash"
BOOTSTRAP = ROOT / "geno-bootstrap"

GENO_DIR = HOME / ".geno"
TRACES_DIR = GENO_DIR / "traces"
HEALTH_DIR = GENO_DIR / "health"
DISCOVERY_DIR = GENO_DIR / "discovery"
DATASETS_DIR = GENO_DIR / "datasets"
ISO_DIR = GENO_DIR / "iso"


def normalize(name: str) -> str:
    """Canonicalize to the `geno-{name}` form used on disk."""
    return name if name.startswith("geno-") else f"geno-{name}"


def short(full_name: str) -> str:
    return full_name.removeprefix("geno-")


def skillset_root(name: str) -> Path:
    return ROOT / normalize(name)


def skillset_git(name: str) -> Path:
    return skillset_root(name) / ".git"


def skillset_worktree(name: str, variant: str = "main") -> Path:
    if variant == "main":
        return skillset_root(name) / "main"
    return skillset_root(name) / ".worktrees" / variant


def skillset_active(name: str) -> Path:
    return skillset_root(name) / "active"


def skillset_venvs(name: str) -> Path:
    return skillset_root(name) / "venvs"
