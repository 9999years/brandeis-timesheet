import enum
import functools
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Iterator
from typing import Tuple, Optional

from decouple import config

import creds

DOCUMENT_PREFIX = r'''
\documentclass[12pt]{article}
\usepackage{brandeis-timesheet}
\begin{document}
'''.lstrip()

# note leading and trailing linebreaks
DOCUMENT_SUFFIX = r'''
\end{document}
'''


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

    def next(self, dt: datetime) -> datetime:
        days = (int(self) - int(Weekday.from_datetime(dt)) - 1) % len(Weekday) + 1
        # days = len(Weekday) - (int(Weekday.from_datetime(dt)) + int(self) - 1) % len(Weekday)
        return dt + timedelta(days=days)

    @property
    def abbr(self) -> str:
        return self.value[1]

    @classmethod
    def from_int(cls, weekday: int) -> 'Weekday':
        return next(filter(lambda wd: int(wd) == weekday,
                           cls.__members__.values()))

    @classmethod
    def from_datetime(cls, dt: datetime) -> 'Weekday':
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


WEEK_START = Weekday.MONDAY
WEEK_END = Weekday.SUNDAY
TIMESHEET_GEN = Weekday.THURSDAY
TIMESHEET_DUE = Weekday.MONDAY


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
    service = creds.build_service()
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
    service = creds.build_service()
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


def format_time(dt: datetime) -> str:
    if dt.minute == 0:
        return dt.strftime('%I%p').lstrip('0').lower()
    else:
        return dt.strftime('%I:%M%p').lstrip('0').lower()


def format_float(f: float) -> str:
    if f.is_integer():
        f = int(f)
    return str(round(f, 3))


def format_timedelta(td: timedelta) -> str:
    return format_float(td.seconds / 3600)


def timesheet_data(during=None) -> dict:
    start, end = work_week(during)
    events = work_events(start, end)

    def filter_events(day: datetime):
        day_end = day + timedelta(hours=24)

        def time_in_day(event: dict):
            start, _ = event_time(event)
            return day <= start <= day_end

        return filter(time_in_day, events)

    ret = {
        'start': start.date().isoformat(),
        'end': end.date().isoformat(),
        'due': TIMESHEET_DUE.next(start).date().isoformat(),
        'name': config('NAME'),
        'employeeRcd': config('RCD'),
        'serviceDate': config('SERVICE_DATE'),
        'employeeID': config('EMPLOYEE_ID'),
        'dept': config('DEPARTMENT'),
        'paygroup': config('PAYGROUP'),
        'payRate': config('PAY_RATE'),
        'position': config('POSITION'),
        'status': config('STATUS'),
        'fiscalYear': str(start.year),
        'awardAmt': config('AWARD_AMT'),
        'awardBal': config('AWARD_BAL'),
        'fundingDate': TIMESHEET_GEN.next(start).date().isoformat(),
        'fund': config('FUND'),
        'program': config('PROGRAM'),
        'fundAcct': config('ACCOUNT'),
        'dist': config('DISTRIBUTION'),
        'employeeSignatureDate': datetime.now().date().isoformat(),
        'supervisor': config('SUPERVISOR'),
        'employeeSignature': config('SIGNATURE'),
    }


    total = timedelta()
    for day in date_range(start, end):
        abbr = Weekday.from_datetime(day).abbr
        shift_counter = 1

        def inKey() -> str:
            return abbr + 'In' + str(shift_counter)

        def outKey() -> str:
            return abbr + 'Out' + str(shift_counter)

        today_events = filter_events(day)
        day_total = timedelta()
        for event in today_events:
            start, end = event_time(event)
            ret[inKey()] = format_time(start)
            ret[outKey()] = format_time(end)
            day_total += end - start
            shift_counter += 1

        ret[abbr + 'Date'] = day.date().isoformat()
        total += day_total
        if day_total:
            ret[abbr + 'Total'] = format_timedelta(day_total)

    ret['totalHours'] = format_timedelta(total)
    return ret


def tex_escape(s: str) -> str:
    """
    Escapes a string for use in a LaTeX document
    """
    # characters that have to be escaped manually
    for c in '\\~^':
        s = s.replace(c, '\\char"' + format(ord(c), 'X'))
    # characters that can be escaped regularly
    for c in '&%$#_{}':
        s = s.replace(c, '\\' + c)
    return s


def timesheet_cmd(data: dict, cmd_name='timesheet') -> str:
    keyvals = []
    for key, val in data.items():
        val = tex_escape(val)
        if ',' in val:
            val = '{' + val + '}'
        keyvals.append('\t' + key + '=' + val + ',\n')
    return '\\' + cmd_name + '{\n' + ''.join(keyvals) + '}'


def timesheet_doc(data: dict, cmd_name='timesheet') -> str:
    return (DOCUMENT_PREFIX
            + timesheet_cmd(data, cmd_name)
            + DOCUMENT_SUFFIX)


def main():
    import sys
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    print(timesheet_doc(timesheet_data()))


if __name__ == '__main__':
    main()
