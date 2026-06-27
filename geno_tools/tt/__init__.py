"""tt — terminal/session + workspace manager, vendored into geno-tools.

Invoked as `geno-tools tt …`; see geno_tools/shell/tt.sh for the interactive
`tt` shell function (cd + iTerm hooks)."""

from .cli import main

__all__ = ["main"]
