import argparse
import asyncio
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pip-outdated",
        description="Find outdated dependencies in your requirements.txt, setup.cfg or pyproject.toml file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Print verbose information.")
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Don't return exit code 1 if not everything is up to date."
    )
    parser.add_argument(
        "pattern",
        nargs="*",
        default=["requirements.txt", "setup.cfg", "pyproject.toml"],
        metavar="<pattern>",
        help="Read dependencies from requirements files. This option accepts glob pattern.",
    )
    return parser.parse_args()


def _windows_selector_loop_factory() -> asyncio.AbstractEventLoop:
    loop = asyncio.SelectorEventLoop()
    asyncio.set_event_loop(loop)
    return loop


def main() -> None:
    if sys.platform == 'win32':
        asyncio.run(_main(), loop_factory=_windows_selector_loop_factory)
    else:
        asyncio.run(_main())


async def _main() -> None:
    args = parse_args()

    from .verbose import set_verbose

    set_verbose(args.verbose)

    from .check_outdated import check_outdated
    from .find_requirements import find_requirements
    from .print_outdated import print_outdated
    from .session import get_session

    requirements = find_requirements(args.pattern)
    async with get_session() as session:
        outdated_results = [
            asyncio.create_task(check_outdated(requirement, session))
            for requirement in requirements
            if requirement is not None
        ]
        await print_outdated(outdated_results, args.quiet)
