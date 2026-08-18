"""Detection of coding agents installed on the current machine."""

from pathlib import Path


_AGENT_HOMES: dict[str, str] = {
    "claude-code": "~/.claude",
    "codex": "~/.codex",
    "cursor": "~/.cursor",
    "antigravity": "~/.gemini/antigravity",
    "gemini-cli": "~/.gemini",
    "github-copilot": "~/.copilot",
    "opencode": "~/.config/opencode",
}


def detect_installed() -> list[str]:
    """Return agents whose home directories exist."""
    return [
        name
        for name, home in _AGENT_HOMES.items()
        if Path(home).expanduser().is_dir()
    ]
