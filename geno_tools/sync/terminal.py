"""Rich/readchar adapter for interactive sync source selection."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import readchar
from rich.console import Console, Group
from rich.text import Text


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


def _view(
    candidate: dict[str, Any],
    remaining: list[dict[str, Any]],
    options: list[tuple[str, str]],
    selected: int,
) -> Group:
    active = candidate["active"]
    stable = candidate["stable"]
    transfer_size = int(active.get("transfer_size", 0)) + int(
        candidate.get("stable_transfer_size", 0)
    )
    lines = [
        Text(),
        Text.from_markup(
            f"[bold]{candidate['name']}[/bold] has an active developer checkout"
        ),
        Text.from_markup(
            "  Dev snapshot "
            f"[bold]{active.get('project_version', '?')}[/bold] "
            f"{active.get('branch') or '(detached)'} "
            f"{str(active.get('commit', '?'))[:10]} ({_dirty(active)})"
        ),
        Text(f"    {active.get('source', '?')}"),
        Text(f"    estimated transfer {_size(transfer_size)}"),
        Text.from_markup(
            "  deactivate restores Stable "
            f"[bold]{stable.get('version', '?')}[/bold] "
            f"{stable.get('branch', '?')} {str(stable.get('sha', '?'))[:10]}"
        ),
        Text(f"    {stable.get('url', '?')}"),
        Text(),
    ]
    for index, (_value, label) in enumerate(options):
        pointer = "[bold cyan]›[/bold cyan]" if index == selected else " "
        lines.append(Text.from_markup(f"  {pointer} {label}"))
    lines.extend(
        [Text(), Text.from_markup("[dim]Use ↑/↓ and Enter. Ctrl-C cancels.[/dim]")]
    )
    return Group(*lines)


def _draw(console: Console, view: Group) -> int:
    height = len(console.render_lines(view, console.options, pad=False))
    console.print(view)
    return max(height, 1)


def _clear(console: Console, height: int) -> None:
    if not console.is_terminal:
        return
    for _ in range(height):
        console.file.write("\x1b[1A\r\x1b[2K")
    console.file.flush()


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
    height = _draw(output, _view(candidate, remaining, options, selected))
    while True:
        try:
            pressed = read_key()
        except KeyboardInterrupt:
            _clear(output, height)
            return "cancel"
        if pressed in {UP, "\x1b[A"}:
            selected = (selected - 1) % len(options)
            _clear(output, height)
            height = _draw(output, _view(candidate, remaining, options, selected))
        elif pressed in {DOWN, "\x1b[B"}:
            selected = (selected + 1) % len(options)
            _clear(output, height)
            height = _draw(output, _view(candidate, remaining, options, selected))
        elif pressed in {ENTER, "\n", "\r"}:
            _clear(output, height)
            return options[selected][0]
        elif pressed == "\x03":
            _clear(output, height)
            return "cancel"
