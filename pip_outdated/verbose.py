"""Simple namespace to share verbose state."""

_VERBOSE: bool | None = None


def set_verbose(value: bool) -> None:
    global _VERBOSE
    _VERBOSE = value


def verbose() -> bool | None:
    return _VERBOSE
