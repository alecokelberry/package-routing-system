"""Clock values are hours since midnight. 9.5 is 9:30 AM."""

from __future__ import annotations

import re


def format_time(hours: float) -> str:
    """Format hours since midnight as '9:05 AM'."""
    total_minutes = int(round(hours * 60))
    hour, minute = divmod(total_minutes, 60)
    suffix = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    return f"{hour12}:{minute:02d} {suffix}"


def parse_time(text: str) -> float | None:
    """Parse '9:00 AM', '14:30', or '9' into hours since midnight.

    Returns None when the text is not a time of day.
    """
    match = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?", text.strip().upper())
    if not match:
        return None
    hours = int(match.group(1))
    minutes = int(match.group(2) or 0)
    suffix = match.group(3)
    if minutes > 59:
        return None
    if suffix == "PM" and hours != 12:
        hours += 12
    if suffix == "AM" and hours == 12:
        hours = 0
    if hours > 23:
        return None
    return hours + minutes / 60.0


def to_minutes(hours: float) -> int:
    """Minute of day, using the same rounding as format_time."""
    return int(round(hours * 60))
