import re
from datetime import UTC, date, datetime, time, timedelta

_FRIENDLY_DURATION = re.compile(
    r'^(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>seconds?|minutes?|hours?|days?|weeks?)$',
    re.IGNORECASE,
)
_ISO_DURATION = re.compile(
    r'^P'
    r'(?:(?P<weeks>\d+(?:\.\d+)?)W)?'
    r'(?:(?P<days>\d+(?:\.\d+)?)D)?'
    r'(?:T'
    r'(?:(?P<hours>\d+(?:\.\d+)?)H)?'
    r'(?:(?P<minutes>\d+(?:\.\d+)?)M)?'
    r'(?:(?P<seconds>\d+(?:\.\d+)?)S)?'
    r')?$',
    re.IGNORECASE,
)


def parse_exclude_newer(value: str, *, now: datetime | None = None) -> datetime:
    """Parse an exclude-newer timestamp or cooldown into a UTC cutoff."""
    value = value.strip()
    reference_time = now or datetime.now(UTC)
    if reference_time.tzinfo is None:
        raise ValueError('The reference time must include a time zone')
    reference_time = reference_time.astimezone(UTC)

    duration = _parse_duration(value)
    if duration is not None:
        return reference_time - duration

    try:
        local_date = date.fromisoformat(value)
    except ValueError:
        pass
    else:
        return datetime.combine(local_date, time.min).astimezone(UTC)

    normalized_value = f'{value[:-1]}+00:00' if value.upper().endswith('Z') else value
    try:
        cutoff = datetime.fromisoformat(normalized_value)
    except ValueError as error:
        raise ValueError(
            'expected an RFC 3339 timestamp, an ISO date, or a duration such as "2 weeks" or "P14D"'
        ) from error
    if cutoff.tzinfo is None:
        raise ValueError('RFC 3339 timestamps must include a UTC offset')
    return cutoff.astimezone(UTC)


def _parse_duration(value: str) -> timedelta | None:
    friendly_match = _FRIENDLY_DURATION.fullmatch(value)
    if friendly_match:
        amount = float(friendly_match.group('value'))
        unit = friendly_match.group('unit').lower().removesuffix('s')
        seconds_per_unit = {
            'second': 1,
            'minute': 60,
            'hour': 60 * 60,
            'day': 24 * 60 * 60,
            'week': 7 * 24 * 60 * 60,
        }
        return timedelta(seconds=amount * seconds_per_unit[unit])

    iso_match = _ISO_DURATION.fullmatch(value)
    if not iso_match or not any(iso_match.groupdict().values()):
        return None

    parts = {name: float(amount or 0) for name, amount in iso_match.groupdict().items()}
    return timedelta(
        weeks=parts['weeks'],
        days=parts['days'],
        hours=parts['hours'],
        minutes=parts['minutes'],
        seconds=parts['seconds'],
    )
