"""Rich/readchar adapter for interactive sync source selection."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import readchar
from rich.console import Console


UP = readchar.key.UP
DOWN = readchar.key.DOWN
ENTER = readchar.key.ENTER


def _size(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if amount < 1024 or unit == "GiB":
            return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{amount:.1f} GiB"  # pragma: no cover - loop always returns


def _dirty(value: dict[str, Any]) -> str:
    dirty = value.get("dirty") or {}
    parts = []
    if dirty.get("cached"):
        parts.append("staged")
    if dirty.get("worktree"):
        parts.append("unstaged")
    if dirty.get("untracked"):
        parts.append(f"{dirty['untracked']} untracked")
    return f"dirty: {', '.join(parts)}" if parts else "clean"


def _render(
    console: Console,
    candidate: dict[str, Any],
    remaining: list[dict[str, Any]],
    options: list[tuple[str, str]],
    selected: int,
) -> None:
    active = candidate["active"]
    stable = candidate["stable"]
    console.print(f"\n[bold]{candidate['name']}[/bold] has an active developer checkout")
    console.print(
        "  Dev snapshot "
        f"[bold]{active.get('project_version', '?')}[/bold] "
        f"{active.get('branch') or '(detached)'} "
        f"{str(active.get('commit', '?'))[:10]} ({_dirty(active)})"
    )
    console.print(f"    {active.get('source', '?')}")
    transfer_size = int(active.get("transfer_size", 0)) + int(
        candidate.get("stable_transfer_size", 0)
    )
    console.print(f"    estimated transfer {_size(transfer_size)}")
    console.print(
        "  deactivate restores Stable "
        f"[bold]{stable.get('version', '?')}[/bold] "
        f"{stable.get('branch', '?')} {str(stable.get('sha', '?'))[:10]}"
    )
    console.print(f"    {stable.get('url', '?')}")
    console.print()
    for index, (_value, label) in enumerate(options):
        pointer = "[bold cyan]›[/bold cyan]" if index == selected else " "
        console.print(f"  {pointer} {label}")
    console.print("\n[dim]Use ↑/↓ and Enter. Ctrl-C cancels.[/dim]")


def choose_one(
    candidate: dict[str, Any],
    remaining: list[dict[str, Any]],
    *,
    read_key: Callable[[], str] = readchar.readkey,
    console: Console | None = None,
) -> str:
    """Prompt for one candidate and return a pure selection answer."""
    output = console or Console(highlight=False)
    eligible_count = len(remaining)
    options = [
        ("active", "Dev snapshot"),
        ("stable", "Stable fallback"),
        ("active-all", f"Dev for all remaining ({eligible_count})"),
        ("stable-all", f"Stable for all remaining ({eligible_count})"),
        ("cancel", "Cancel"),
    ]
    selected = 0
    while True:
        _render(output, candidate, remaining, options, selected)
        try:
            pressed = read_key()
        except KeyboardInterrupt:
            output.print()
            return "cancel"
        if pressed in {UP, "\x1b[A"}:
            selected = (selected - 1) % len(options)
        elif pressed in {DOWN, "\x1b[B"}:
            selected = (selected + 1) % len(options)
        elif pressed in {ENTER, "\n", "\r"}:
            return options[selected][0]
        elif pressed == "\x03":
            return "cancel"
