import argparse
import asyncio
import sys

__version__ = "0.7.0"

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


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
        "file",
        nargs="*",
        default=["requirements.txt", "setup.cfg", "pyproject.toml"],
        metavar="<patterns>",
        help="Read dependencies from requirements files. This option accepts glob pattern.",
    )
    return parser.parse_args()


def main() -> None:
    # FIXME: we can't use asyncio.run since it closes the event loop
    # https://github.com/aio-libs/aiohttp/issues/1925
    # asyncio.run(_main())
    asyncio.get_event_loop().run_until_complete(_main())


async def _main() -> None:
    args = parse_args()

    from .verbose import set_verbose

    set_verbose(args.verbose)

    from .check_outdated import check_outdated
    from .find_requirements import find_requirements
    from .print_outdated import print_outdated
    from .session import get_session

    requirements = find_requirements(args.patterns)
    async with get_session() as session:
        outdated_results = [
            asyncio.create_task(check_outdated(requirement, session))
            for requirement in requirements
            if requirement is not None
        ]
        await print_outdated(outdated_results, args.quiet)
