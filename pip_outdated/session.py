import aiohttp


def get_session() -> aiohttp.ClientSession:
    headers = {"User-Agent": "pip-outdated"}
    connector = aiohttp.TCPConnector(limit_per_host=5, resolver=aiohttp.DefaultResolver())
    return aiohttp.ClientSession(headers=headers, connector=connector)
