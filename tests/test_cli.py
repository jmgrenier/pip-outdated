import unittest
from datetime import UTC, datetime

from pip_outdated import parse_args


class ParseArgsTests(unittest.TestCase):
    def test_parses_exclude_newer(self):
        args = parse_args(['--exclude-newer', '2026-07-13T12:00:00Z', 'requirements.txt'])

        self.assertEqual(args.exclude_newer, datetime(2026, 7, 13, 12, tzinfo=UTC))
        self.assertEqual(args.pattern, ['requirements.txt'])


if __name__ == '__main__':
    unittest.main()
