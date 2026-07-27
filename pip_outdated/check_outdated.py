import contextlib
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import aiohttp
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version
from packaging.version import parse as parse_version

from .verbose import verbose


@dataclass
class Result:
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

    @property
    def install_not_found(self) -> bool:
        return self.version is None

    @property
    def install_not_wanted(self) -> bool:
        if self.version is None:
            return False
        return self.version not in self.requirement.specifier

    @property
    def pypi_not_found(self) -> bool:
        return self.latest is None

    @property
    def outdated(self) -> bool:
        return self.version != self.wanted or self.version != self.latest


async def get_local_version(name: str) -> Version | None:
    try:
        local_version = version(name)
    except PackageNotFoundError:
        return None

    if local_version is None:
        return None

    try:
        return parse_version(local_version)
    except InvalidVersion:
        return None


def _parse_upload_time(file_data: dict[str, Any]) -> datetime | None:
    value = file_data.get('upload_time_iso_8601') or file_data.get('upload_time')
    if not value:
        return None

    normalized_value = f'{value[:-1]}+00:00' if value.upper().endswith('Z') else value
    try:
        upload_time = datetime.fromisoformat(normalized_value)
    except ValueError:
        return None
    if upload_time.tzinfo is None:
        upload_time = upload_time.replace(tzinfo=UTC)
    return upload_time.astimezone(UTC)


def _uploaded_by_cutoff(files: list[dict[str, Any]], exclude_newer: datetime) -> bool:
    for file_data in files:
        upload_time = _parse_upload_time(file_data)
        if upload_time is not None and upload_time <= exclude_newer:
            return True
    return False


async def get_pypi_versions(
    name: str, session: aiohttp.ClientSession, exclude_newer: datetime | None = None
) -> list[Version]:
    async with session.get(f'https://pypi.org/pypi/{name}/json') as res:
        res.raise_for_status()

        versions = []
        for release, files in (await res.json())['releases'].items():
            if exclude_newer is not None and not _uploaded_by_cutoff(files, exclude_newer):
                continue
            try:
                package_version = parse_version(release)
            except InvalidVersion:
                continue
            if package_version.is_prerelease:
                continue
            versions.append(package_version)

        versions.sort()
        return versions


async def check_outdated(
    dependency: Requirement, session: aiohttp.ClientSession, exclude_newer: datetime | None = None
) -> Result:
    if verbose():
        print(f'Checking: {dependency.name} {dependency.specifier}')
    name = canonicalize_name(dependency.name)
    current_version = await get_local_version(name)
    pypi_versions = await get_pypi_versions(name, session, exclude_newer)
    return Result(dependency, current_version, pypi_versions)
