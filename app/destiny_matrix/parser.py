"""Date-of-birth parsing and validation for calculator tool inputs."""

from dataclasses import dataclass
from datetime import date
import re
from typing import Mapping, Union


@dataclass(frozen=True)
class DOB:
    """A validated date of birth."""

    day: int
    month: int
    year: int


DOBInput = Union[DOB, date, str, Mapping[str, int]]


def validate_dob(
    day: int,
    month: int,
    year: int,
    *,
    minimum_year: int = 1900,
    maximum_age: int = 150,
    allow_future: bool = False,
) -> DOB:
    """Validate DOB components and return a normalized ``DOB``."""
    try:
        parsed = date(int(year), int(month), int(day))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid date of birth") from exc

    today = date.today()
    if parsed.year < minimum_year:
        raise ValueError(f"Year must be {minimum_year} or later")
    if not allow_future and parsed > today:
        raise ValueError("Date of birth cannot be in the future")

    age = today.year - parsed.year - (
        (today.month, today.day) < (parsed.month, parsed.day)
    )
    if age > maximum_age:
        raise ValueError(f"Age cannot exceed {maximum_age} years")

    return DOB(day=parsed.day, month=parsed.month, year=parsed.year)


_MONTH_NAMES = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}


def _month_from_name(name: str) -> int | None:
    return _MONTH_NAMES.get(name.strip().lower())


def parse_dob(value: DOBInput) -> DOB:
    """
    Parse a DOB from common formats:

    - ``DD/MM/YYYY``, ``DD-MM-YYYY``, ``DD.MM.YYYY``
    - ``YYYY-MM-DD``
    - ``11 July 1998``, ``July 11, 1998``
    - a ``datetime.date``, a ``DOB``, or a mapping with day/month/year
    """
    if isinstance(value, DOB):
        return validate_dob(value.day, value.month, value.year)
    if isinstance(value, date):
        return validate_dob(value.day, value.month, value.year)
    if isinstance(value, Mapping):
        try:
            return validate_dob(value["day"], value["month"], value["year"])
        except KeyError as exc:
            raise ValueError("DOB mapping requires day, month, and year") from exc
    if not isinstance(value, str):
        raise TypeError("DOB must be a date string, date, DOB, or mapping")

    text = value.strip()
    iso_match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if iso_match:
        year, month, day = map(int, iso_match.groups())
        return validate_dob(day, month, year)

    local_match = re.fullmatch(
        r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", text
    )
    if local_match:
        day, month, year = map(int, local_match.groups())
        return validate_dob(day, month, year)

    # "11 July 1998" / "11 Jul 1998"
    day_month_year = re.fullmatch(
        r"(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})",
        text,
    )
    if day_month_year:
        day_s, month_name, year_s = day_month_year.groups()
        month = _month_from_name(month_name)
        if month is not None:
            return validate_dob(int(day_s), month, int(year_s))

    # "July 11, 1998" / "July 11 1998"
    month_day_year = re.fullmatch(
        r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})",
        text,
    )
    if month_day_year:
        month_name, day_s, year_s = month_day_year.groups()
        month = _month_from_name(month_name)
        if month is not None:
            return validate_dob(int(day_s), month, int(year_s))

    raise ValueError(
        "Invalid date format. Use DD/MM/YYYY, YYYY-MM-DD, "
        "or a form like 11 July 1998"
    )
