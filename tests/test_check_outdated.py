import unittest
from datetime import UTC, datetime

from packaging.version import Version

from pip_outdated.check_outdated import get_pypi_versions


class FakeResponse:
    def __init__(self, releases):
        self.releases = releases

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    def raise_for_status(self):
        return None

    async def json(self):
        return {'releases': self.releases}


class FakeSession:
    def __init__(self, releases):
        self.releases = releases

    def get(self, url):
        return FakeResponse(self.releases)


class GetPypiVersionsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.releases = {
            '1.0': [{'upload_time_iso_8601': '2026-07-01T00:00:00Z'}],
            '2.0': [
                {'upload_time_iso_8601': '2026-07-10T00:00:00Z'},
                {'upload_time_iso_8601': '2026-07-20T00:00:00Z'},
            ],
            '3.0': [{'upload_time_iso_8601': '2026-07-14T00:00:00Z'}],
            '4.0': [{'upload_time_iso_8601': '2026-07-15T00:00:00Z'}],
            '5.0rc1': [{'upload_time_iso_8601': '2026-07-01T00:00:00Z'}],
            'not-a-version': [{'upload_time_iso_8601': '2026-07-01T00:00:00Z'}],
            '6.0': [],
        }
        self.session = FakeSession(self.releases)

    async def test_filters_versions_by_artifact_upload_time(self):
        cutoff = datetime(2026, 7, 14, tzinfo=UTC)

        versions = await get_pypi_versions('demo', self.session, cutoff)

        self.assertEqual(versions, [Version('1.0'), Version('2.0'), Version('3.0')])

    async def test_preserves_existing_behavior_without_cutoff(self):
        versions = await get_pypi_versions('demo', self.session)

        self.assertEqual(
            versions,
            [Version('1.0'), Version('2.0'), Version('3.0'), Version('4.0'), Version('6.0')],
        )


if __name__ == '__main__':
    unittest.main()
