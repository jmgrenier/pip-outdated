import contextlib
from dataclasses import dataclass
from importlib.metadata import version

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version
from packaging.version import parse as parse_version

from .verbose import verbose


@dataclass
class OutdateResult:
    requirement: Requirement
    version: Version | None
    all_versions: list[Version]

    wanted: Version | None = None
    latest: Version | None = None

    def __post_init__(self):
        if self.all_versions:
            with contextlib.suppress(StopIteration):
                self.wanted = next(v for v in reversed(self.all_versions) if v in self.requirement.specifier)
            self.latest = self.all_versions[-1]

    @property
    def name(self) -> str:
        return self.requirement.name

    def install_not_found(self) -> bool:
        return self.version is None

    def install_not_wanted(self) -> bool:
        if self.version is None:
            return False
        return self.version not in self.requirement.specifier

    def pypi_not_found(self) -> bool:
        return self.latest is None

    def outdated(self) -> bool:
        return self.version != self.wanted or self.version != self.latest


async def get_local_version(name: str) -> Version | None:
    return parse_version(version(name))


async def get_pypi_versions(name: str, session) -> list[Version]:
    async with session.get(f"https://pypi.org/pypi/{name}/json") as r:
        r.raise_for_status()
        keys = []
        for s in (await r.json())["releases"]:
            try:
                version = parse_version(s)
            except InvalidVersion:
                continue
            if version.is_prerelease:
                continue
            keys.append(version)
        keys.sort()
        return keys


async def check_outdated(require, session) -> OutdateResult:
    if verbose():
        print(f"Checking: {require.name} {require.specifier}")
    name = canonicalize_name(require.name)
    current_version = await get_local_version(name)
    pypi_versions = await get_pypi_versions(name, session)
    return OutdateResult(require, current_version, pypi_versions)
