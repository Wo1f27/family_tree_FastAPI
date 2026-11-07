"""Неполные и приблизительные даты для генеалогии.

Примеры:
- 26 мая 1961  / ввод 26051961 или 26-05-1961
- май 1961     / ввод 05-1961 или 051961
- 1961         / только год
- ок. 1901     / ~1901, около 1901
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import re


MONTH_NAMES_RU_GENITIVE: tuple[str, ...] = (
    '',
    'января',
    'февраля',
    'марта',
    'апреля',
    'мая',
    'июня',
    'июля',
    'августа',
    'сентября',
    'октября',
    'ноября',
    'декабря',
)

MONTH_NAMES_RU_NOMINATIVE: tuple[str, ...] = (
    '',
    'январь',
    'февраль',
    'март',
    'апрель',
    'май',
    'июнь',
    'июль',
    'август',
    'сентябрь',
    'октябрь',
    'ноябрь',
    'декабрь',
)

DATE_ENTRY_HINT = 'ДД-ММ-ГГГГ, ММ-ГГГГ, ГГГГ или ~ГГГГ'


@dataclass(frozen=True, slots=True)
class PartialDate:
    year: int
    month: int | None = None
    day: int | None = None
    approx: bool = False

    def __post_init__(self) -> None:
        if self.year < 1 or self.year > 9999:
            raise ValueError(f'Некорректный год: {self.year}')
        if self.month is not None and not (1 <= self.month <= 12):
            raise ValueError(f'Некорректный месяц: {self.month}')
        if self.day is not None:
            if self.month is None:
                raise ValueError('День без месяца недопустим')
            # проверка календарности через date()
            date(self.year, self.month, self.day)

    @classmethod
    def from_full_date(cls, value: date, *, approx: bool = False) -> PartialDate:
        return cls(year=value.year, month=value.month, day=value.day, approx=approx)

    def to_sort_date(self) -> date:
        """Для сортировки и legacy-колонки date_of_*."""
        return date(self.year, self.month or 1, self.day or 1)

    @property
    def is_complete(self) -> bool:
        return self.day is not None and self.month is not None and not self.approx


def format_partial_display(value: PartialDate | None, *, empty: str = '—') -> str:
    if value is None:
        return empty
    prefix = 'ок. ' if value.approx else ''
    if value.day is not None and value.month is not None:
        return f'{prefix}{value.day} {MONTH_NAMES_RU_GENITIVE[value.month]} {value.year} г.'
    if value.month is not None:
        return f'{prefix}{MONTH_NAMES_RU_NOMINATIVE[value.month]} {value.year} г.'
    return f'{prefix}{value.year} г.'


def format_partial_entry(value: PartialDate | None) -> str:
    if value is None:
        return ''
    if value.day is not None and value.month is not None:
        body = f'{value.day:02d}-{value.month:02d}-{value.year:04d}'
    elif value.month is not None:
        body = f'{value.month:02d}-{value.year:04d}'
    else:
        body = f'{value.year:04d}'
    return f'~{body}' if value.approx else body


def _mask_date_digits(digits: str) -> str:
    digits = digits[:8]
    if len(digits) <= 2:
        return digits
    if len(digits) <= 4:
        return f'{digits[:2]}-{digits[2:]}'
    return f'{digits[:2]}-{digits[2:4]}-{digits[4:]}'


def _try_build_partial(
    year: int,
    month: int | None = None,
    day: int | None = None,
    *,
    approx: bool = False,
) -> PartialDate | None:
    try:
        return PartialDate(year=year, month=month, day=day, approx=approx)
    except ValueError:
        return None


def try_parse_partial_date(value: str) -> PartialDate | None:
    text = value.strip()
    if not text:
        return None

    approx = False
    lowered = text.lower()
    for marker in ('около ', 'ок.', 'ок ', '~', '≈', 'примерно '):
        if lowered.startswith(marker):
            approx = True
            text = text[len(marker) :].strip()
            lowered = text.lower()
            break
    if text.startswith('~') or text.startswith('≈'):
        approx = True
        text = text[1:].strip()

    # Полные форматы с разделителями
    for fmt in ('%d-%m-%Y', '%d.%m.%Y', '%Y-%m-%d', '%Y.%m.%d'):
        try:
            d = datetime.strptime(text, fmt).date()
            return PartialDate.from_full_date(d, approx=approx)
        except ValueError:
            continue

    # Месяц-год
    for fmt in ('%m-%Y', '%m.%Y', '%Y-%m', '%Y.%m'):
        try:
            dt = datetime.strptime(text, fmt)
            if fmt.startswith('%Y'):
                return _try_build_partial(dt.year, dt.month, approx=approx)
            return _try_build_partial(dt.year, dt.month, approx=approx)
        except ValueError:
            continue

    # Только год
    if re.fullmatch(r'\d{4}', text):
        return _try_build_partial(int(text), approx=approx)

    digits = ''.join(ch for ch in text if ch.isdigit())
    if len(digits) == 8:
        for fmt in ('%d%m%Y', '%Y%m%d'):
            try:
                d = datetime.strptime(digits, fmt).date()
                return PartialDate.from_full_date(d, approx=approx)
            except ValueError:
                continue
    if len(digits) == 6:
        try:
            month = int(digits[:2])
            year = int(digits[2:])
            return _try_build_partial(year, month, approx=approx)
        except ValueError:
            return None
    if len(digits) == 4:
        return _try_build_partial(int(digits), approx=approx)

    return None


def person_partial_from_columns(
    *,
    year: int | None,
    month: int | None,
    day: int | None,
    approx: bool | int | None,
    legacy: date | None,
) -> PartialDate | None:
    """Собрать PartialDate из новых колонок; если пусто — из legacy date_*."""
    if year is not None:
        return _try_build_partial(
            int(year),
            int(month) if month is not None else None,
            int(day) if day is not None else None,
            approx=bool(approx),
        )
    if legacy is not None:
        return PartialDate.from_full_date(legacy, approx=False)
    return None


def partial_to_column_values(value: PartialDate | None) -> dict[str, int | None]:
    """Словарь year/month/day/approx + sort date для записи в Person."""
    if value is None:
        return {
            'year': None,
            'month': None,
            'day': None,
            'approx': None,
            'sort_date': None,
        }
    return {
        'year': value.year,
        'month': value.month,
        'day': value.day,
        'approx': 1 if value.approx else 0,
        'sort_date': value.to_sort_date(),
    }
