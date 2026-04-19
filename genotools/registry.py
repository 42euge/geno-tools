"""Curated registry of known geno-* skillsets."""

_REGISTRY: dict[str, str] = {
    "agents":   "https://github.com/42euge/geno-agents.git",
    "media":    "https://github.com/42euge/geno-media.git",
    "research": "https://github.com/42euge/geno-research.git",
    "taxes":    "https://github.com/42euge/geno-taxes.git",
    "kaggle":   "https://github.com/42euge/geno-kaggle.git",
    "dev":      "https://github.com/42euge/geno-dev.git",
}


def available() -> dict[str, str]:
    return dict(_REGISTRY)


def resolve(name: str) -> str | None:
    """Return the git URL for a registered skillset name, or None."""
    return _REGISTRY.get(name)
