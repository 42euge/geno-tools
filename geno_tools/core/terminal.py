"""TTY-aware terminal formatting shared by command modules."""

import os
import sys


def is_tty() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def color(code: str, value: str) -> str:
    return f"\033[{code}m{value}\033[0m" if is_tty() else value


def bold(value: str) -> str:
    return color("1", value)


def dim(value: str) -> str:
    return color("2", value)


def green(value: str) -> str:
    return color("32", value)


def yellow(value: str) -> str:
    return color("33", value)


def red(value: str) -> str:
    return color("31", value)


def cyan(value: str) -> str:
    return color("36", value)


def rule(label: str = "", width: int = 48) -> str:
    dash = "─" if is_tty() else "-"
    if label:
        head = f"{dash}{dash} {label} "
        return dim(head + dash * max(0, width - len(head)))
    return dim(dash * width)
