"""geno-tools self-management and shared runtime support."""


def add_parser(*args, **kwargs):
    from .commands import add_parser as implementation

    return implementation(*args, **kwargs)


def dispatch(*args, **kwargs):
    from .commands import dispatch as implementation

    return implementation(*args, **kwargs)

__all__ = ["add_parser", "dispatch"]
