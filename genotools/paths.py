from pathlib import Path

HOME = Path.home()
ROOT = HOME / ".geno-tools"
LINKDB = ROOT / "linkdb.json"


def skillset_root(name: str) -> Path:
    return ROOT / f"geno-{name}"


def skillset_repo(name: str) -> Path:
    return skillset_root(name) / "repo"


def skillset_venvs(name: str) -> Path:
    return skillset_root(name) / "venvs"


def skillset_scripts(name: str) -> Path:
    return skillset_root(name) / "scripts"


def skillset_configs(name: str) -> Path:
    return skillset_root(name) / "configs"
