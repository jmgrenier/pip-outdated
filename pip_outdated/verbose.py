"""Simple namespace to share verbose state."""

VERBOSE: bool | None = None


def set_verbose(value: bool) -> None:
    global VERBOSE
    VERBOSE = value


def verbose() -> bool | None:
    return VERBOSE
