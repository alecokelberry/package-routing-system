"""Clock values are hours since midnight. 9.5 is 9:30 AM."""

from __future__ import annotations

import re

_TIME_PATTERN = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?")


def format_time(hours: float) -> str:
    """Format hours since midnight as '9:05 AM'."""
    hour, minute = divmod(to_minutes(hours), 60)
    suffix = "AM" if hour % 24 < 12 else "PM"
    hour12 = hour % 12 or 12
    return f"{hour12}:{minute:02d} {suffix}"


def parse_time(text: str) -> float | None:
    """Parse '9:00 AM', '14:30', or '9' into hours since midnight.

    Returns None when the text is not a time of day. With AM/PM the hour must
    be 1-12. Without it, the hour is read on a 24-hour clock (0-23).
    """
    match = _TIME_PATTERN.fullmatch(text.strip().upper())
    if not match:
        return None
    hours = int(match.group(1))
    minutes = int(match.group(2) or 0)
    suffix = match.group(3)
    if minutes > 59:
        return None
    if suffix is None:
        if hours > 23:
            return None
    else:
        if not 1 <= hours <= 12:
            return None
        hours %= 12
        if suffix == "PM":
            hours += 12
    return hours + minutes / 60.0


def to_minutes(hours: float) -> int:
    """Minute of day, rounded to the nearest minute."""
    return round(hours * 60)
