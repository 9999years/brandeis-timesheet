import enum
import functools
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Iterator
from typing import Tuple, Optional

from decouple import config

import creds


class Weekday(enum.Enum):
    """
    Corresponds with the datetime.weekday() method
    """
    MONDAY = (0, 'mon')
    TUESDAY = (1, 'tues')
    WEDNESDAY = (2, 'wed')
    THURSDAY = (3, 'thurs')
    FRIDAY = (4, 'fri')
    SATURDAY = (5, 'sat')
    SUNDAY = (6, 'sun')

    def __int__(self):
        return self.value[0]

    @property
    def abbr(self):
        return self.value[1]

    @classmethod
    def from_int(cls, weekday: int):
        return next(filter(lambda wd: int(wd) == weekday,
                           cls.__members__.values()))

    @classmethod
    def from_datetime(cls, dt: datetime):
        return cls.from_int(dt.weekday())


@dataclass
class Calendar:
    kind: str
    etag: str
    id: str
    summary: str
    timeZone: str
    colorId: str
    backgroundColor: str
    foregroundColor: str
    accessRole: str
    defaultReminders: List[dict]
    summaryOverride: str = ''
    description: str = ''
    selected: bool = False
    notificationSettings: dict = field(default_factory=dict)
    primary: bool = False
    conferenceProperties: dict = field(default_factory=dict)


WEEK_START = Weekday.SATURDAY
WEEK_END = Weekday.FRIDAY


def date_range(start: datetime, end: datetime) -> Iterator[datetime]:
    while start < end:
        yield start
        start += timedelta(days=1)


def work_week(during: datetime = None) -> Tuple[datetime, datetime]:
    """
    Endpoints for the work week that contains `during`.
    Args:
        during: A datetime in the requested week. If omitted or None, centers
        around `datetime.utcnow()`. MUST be a tz-aware datetime

    Returns:
        A tuple (start, end) of `datetime`s.
    """
    if during is None:
        during = datetime.now().astimezone()
    during = during.replace(hour=0, minute=0, second=0, microsecond=0)

    # The work week starts on saturday and ends on friday
    days_since_start = (during.weekday() - int(WEEK_START)) % len(Weekday)
    days_until_end = (int(WEEK_END) - during.weekday()) % len(Weekday)
    start = during - timedelta(days=days_since_start)
    end = (during + timedelta(days=days_until_end)).replace(hour=23, minute=59, second=59)
    return start, end


@functools.lru_cache()
def calendars() -> List[Calendar]:
    _, _, service = creds.build_creds()
    return [Calendar(**cal)
            for cal
            in service.calendarList().list().execute()['items']]


def work_calendar() -> Optional[Calendar]:
    pat = re.compile(config('WORK_CALENDAR_PAT'))
    for cal in calendars():
        if pat.search(cal.summary):
            return cal


def events(calendar_id: str, start: datetime, end: datetime, **kwargs) -> List[dict]:
    """
    Events in a given calendar in a given time range, ordered by startTime
    Args:
        calendar_id: id of the calendar to query
        start: start time for events
        end: end time for events
        **kwargs: other args passed to the Google cal API

    Returns:

    """
    args = {
        'calendarId': calendar_id,
        'orderBy': 'startTime',
        'singleEvents': 'true',
        'timeMin': start.isoformat(),
        'timeMax': end.isoformat(),
    }

    args.update(kwargs)
    _, _, service = creds.build_creds()
    events = service.events().list(**args).execute()
    return events.get('items', [])


def work_events(start: datetime, end: datetime) -> List[dict]:
    events_ = events(work_calendar().id, start=start, end=end)
    author = config('WORK_EVENT_EMAIL')
    return list(filter(
        lambda event: event['creator'].get('email', '') == author,
        events_))


def event_time(event: dict) -> Tuple[datetime, datetime]:
    return (datetime.fromisoformat(event['start']['dateTime']),
            datetime.fromisoformat(event['end']['dateTime']))


def timesheet_data() -> dict:
    start, end = work_week()
    events = work_events(start, end)

    def filter_events(day: datetime):
        day_end = day + timedelta(hours=24)

        def time_in_day(event: dict):
            start, _ = event_time(event)
            return start >= day and start <= day_end

        return filter(time_in_day, events)

    ret = {
        'name': config('NAME'),
        'supervisor': config('SUPERVISOR'),
        'employeeSignature': config('SIGNATURE'),
        'dept': config('DEPARTMENT'),
        'payRate': config('PAY_RATE'),
    }

    today_data = {}
    for day in date_range(start, end):
        abbr = Weekday.from_int(day.weekday())
        today_events = filter_events(day)

