from datetime import datetime
from typing import Optional

import pytz
import pytz.reference


def date_to_iso(date: datetime | str | None) -> Optional[str]:
    if isinstance(date, datetime):
        return date.isoformat()

    if isinstance(date, str):
        return date

    return None


def get_end_of_date(date: datetime | str | None) -> datetime:
    if isinstance(date, datetime):
        return date.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif isinstance(date, str):
        return datetime.fromisoformat(date).replace(hour=23, minute=59, second=59, microsecond=999999)
    return datetime.now(pytz.UTC).replace(hour=23, minute=59, second=59, microsecond=999999)


def get_start_of_date(date: datetime | str | None) -> datetime:
    if isinstance(date, datetime):
        return date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif isinstance(date, str):
        return datetime.fromisoformat(date).replace(hour=0, minute=0, second=0, microsecond=0)
    return datetime.now(pytz.UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def get_start_of_day(
    client_tz: Optional[pytz.BaseTzInfo] = None, date: Optional[datetime | str] = None
) -> datetime:
    if client_tz:
        return datetime.now(client_tz).replace(hour=0, minute=0, second=0, microsecond=0)

    if date:
        return get_start_of_date(date)

    return datetime.now(pytz.UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def get_end_of_day(
    client_tz: Optional[pytz.BaseTzInfo] = None, date: Optional[datetime | str] = None
) -> datetime:
    if client_tz:
        return datetime.now(client_tz).replace(hour=23, minute=59, second=59, microsecond=999999)

    if date:
        return get_end_of_date(date)

    return datetime.now(pytz.UTC).replace(hour=23, minute=59, second=59, microsecond=999999)


def is_date_today(d: datetime):
    return get_start_of_date(d) > get_start_of_day() and get_end_of_date(d) < get_end_of_day()


def get_datetime_from_string(date_string: datetime | str | None) -> Optional[datetime]:
    if isinstance(date_string, datetime):
        return date_string

    if not date_string or not isinstance(date_string, str):
        return None

    try:
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None
