"""
Find requirements.
https://pip.pypa.io/en/stable/reference/pip_install/#requirements-file-format
"""

import contextlib
import re
from collections.abc import Iterator
from itertools import chain
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement
from setuptools.config.setupcfg import read_configuration

from .verbose import verbose


def iter_files(patterns: str) -> Iterator[Path]:
    """Yield path.Path(pattern) from multiple glob patterns."""
    for pattern in patterns:
        if Path(pattern).is_file():
            yield Path(pattern)
        else:
            yield from Path(".").glob(pattern)


def iter_lines(path: Path) -> Iterator[str]:
    """Yield line from a file. Handle '#' comment and '\' continuation escape."""
    if verbose():
        print(f"Parse: {path}")
    pre_line = ""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"(.*?)(^|\s)#", line)
            if match:
                yield pre_line + match.group(1)
                pre_line = ""
                continue
            if line.endswith("\\\n"):
                pre_line += line[0:-2]
                continue
            if line.endswith("\n"):
                yield pre_line + line[0:-1]
                pre_line = ""
                continue
            yield pre_line + line
            pre_line = ""


def parse_requirements_file(path: Path) -> Iterator[Requirement | None]:
    for line in iter_lines(path):
        require = parse_requirement(line)
        if require:
            yield require


def parse_cfg_file(path: Path) -> Iterator[Requirement | None]:
    conf = read_configuration(path, ignore_option_errors=True)
    requires = []

    with contextlib.suppress(KeyError):
        requires.extend(conf["options"]["setup_requires"])

    with contextlib.suppress(KeyError):
        requires.extend(conf["options"]["install_requires"])

    with contextlib.suppress(KeyError):
        requires.extend(chain.from_iterable(conf["options"]["extras_require"].values()))

    for require in requires:
        require = parse_requirement(require)
        if require:
            yield require


def find_requirements(patterns: str) -> Iterator[Requirement | None]:
    for path in iter_files(patterns):
        requirement = parse_cfg_file(path) if path.suffix == ".cfg" else parse_requirements_file(path)
        yield from requirement


def parse_requirement(line: str) -> Requirement | None:
    # strip options
    match = re.match(r"(.*?)\s--?[a-z]", line)
    if match:
        line = match.group(1)
    try:
        return Requirement(line)
    except InvalidRequirement:
        return None
