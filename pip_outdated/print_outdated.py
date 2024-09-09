import sys
from asyncio import Task

import colorama
from termcolor import colored
from terminaltables import AsciiTable as Table

from .check_outdated import Result


def make_row(result: Result) -> list[str] | None:
    if not result.outdated:
        return None

    def colored_current():
        if result.install_not_found or result.install_not_wanted:
            return colored(str(result.version), "red", attrs=["bold"])
        return str(result.version)

    def colored_wanted():
        if result.pypi_not_found or not result.wanted:
            return colored("None", "red", attrs=["bold"])
        if not result.install_not_found and result.version < result.wanted:  # type: ignore
            return colored(str(result.wanted), "green", attrs=["bold"])
        return str(result.wanted)

    def colored_latest():
        if result.pypi_not_found:
            return colored("None", "red", attrs=["bold"])
        if not result.install_not_found and result.version < result.latest:  # type: ignore
            return colored(str(result.latest), "green", attrs=["bold"])
        return str(result.latest)

    return [result.name, colored_current(), colored_wanted(), colored_latest()]


async def print_outdated(results: list[Task[Result]], quiet: bool):
    colorama.init()

    data = [["Name", "Installed", "Wanted", "Latest"]]
    count = 0
    for count, outdate in enumerate(results, 1):
        row = make_row(await outdate)
        if row:
            data.append(row)

    if not count:
        print(colored("No requirements found.", "red"))
        return

    if len(data) == 1:
        print(colored("Everything is up-to-date!", "cyan", attrs=["bold"]))
        return

    print(colored("Red = unavailable/outdated/out of version specifier", "red", attrs=["bold"]))
    print(colored("Green = updatable", "green", attrs=["bold"]))
    table = Table(data)
    print(table.table)
    if not quiet:
        sys.exit(1)
