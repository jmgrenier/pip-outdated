import unittest
from datetime import UTC, datetime, timedelta

from pip_outdated.exclude_newer import parse_exclude_newer


class ParseExcludeNewerTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)

    def test_parses_rfc3339_timestamp(self):
        cutoff = parse_exclude_newer('2026-07-13T08:30:00-04:00', now=self.now)

        self.assertEqual(cutoff, datetime(2026, 7, 13, 12, 30, tzinfo=UTC))

    def test_parses_local_date_at_local_midnight(self):
        cutoff = parse_exclude_newer('2026-07-13', now=self.now)

        expected = datetime(2026, 7, 13).astimezone(UTC)
        self.assertEqual(cutoff, expected)

    def test_parses_friendly_duration(self):
        cutoff = parse_exclude_newer('2 weeks', now=self.now)

        self.assertEqual(cutoff, self.now - timedelta(days=14))

    def test_parses_iso_duration(self):
        cutoff = parse_exclude_newer('P14D', now=self.now)

        self.assertEqual(cutoff, self.now - timedelta(days=14))

    def test_rejects_calendar_duration(self):
        with self.assertRaisesRegex(ValueError, 'expected an RFC 3339'):
            parse_exclude_newer('P1M', now=self.now)

    def test_rejects_timestamp_without_timezone(self):
        with self.assertRaisesRegex(ValueError, 'must include a UTC offset'):
            parse_exclude_newer('2026-07-13T12:00:00', now=self.now)


if __name__ == '__main__':
    unittest.main()
