from collections.abc import Callable
import json
import tkinter as tk
from dataclasses import dataclass
from datetime import date
from tkinter import font as tkfont

from tkinter import ttk, messagebox
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from database import DATA_DIR, SessionLocal, init_db
from dates import (
    DATE_ENTRY_HINT,
    PartialDate,
    format_partial_display,
    format_partial_entry,
    partial_to_column_values,
    person_partial_from_columns,
    try_parse_partial_date,
    _mask_date_digits,
)

# Только ASCII/кириллица: спецсимволы (• — →) на Linux/Tk часто рисуются квадратиками.
DATE_INPUT_HELP = (
    'Примеры ввода: 26051961 или 26-05-1961; 05-1961; 1961; ~1901 или около 1901'
)
from models import Address, DeathCause, Gender, NameVariant, Person, Phone, Relationship

UI_SETTINGS_PATH = DATA_DIR / 'ui_settings.json'
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 28
INFO_CONTACT_MAX_LINES = 5

# Ограничения размеров окон (подстраиваются под экран пользователя).
WIN_MIN_WIDTH = 360
WIN_MIN_HEIGHT = 240
WIN_MAX_WIDTH_RATIO = 0.96
WIN_MAX_HEIGHT_RATIO = 0.88
# Отступ сверху: заголовок окна + панель GNOME не должны уезжать за край.
WIN_TOP_MARGIN = 56
WIN_EDGE_MARGIN = 16

# (подпись в комбобоксе, режим сортировки)
_SORT_OPTIONS: tuple[tuple[str, str], ...] = (
    ('ФИО', 'fio'),
    ('Год рождения', 'birth_year'),
    ('Год смерти', 'death_year'),
)
_SORT_OPTION_LABELS: tuple[str, ...] = tuple(label for label, _ in _SORT_OPTIONS)
_SORT_MODE_BY_LABEL: dict[str, str] = {label: mode for label, mode in _SORT_OPTIONS}
_SORT_LABEL_BY_MODE: dict[str, str] = {mode: label for label, mode in _SORT_OPTIONS}


def _screen_size(widget: tk.Misc) -> tuple[int, int]:
    widget.update_idletasks()
    return widget.winfo_screenwidth(), widget.winfo_screenheight()


def _apply_window_geometry(
    window: tk.Misc,
    width: int,
    height: int,
    *,
    min_width: int = WIN_MIN_WIDTH,
    min_height: int = WIN_MIN_HEIGHT,
    max_width_ratio: float = WIN_MAX_WIDTH_RATIO,
    max_height_ratio: float = WIN_MAX_HEIGHT_RATIO,
    center: bool = True,
) -> tuple[int, int]:
    """Подогнать размер окна под экран; minsize — мягкий, пользователь может уменьшать.

    center=True — поставить по центру родителя (или экрана) с запасом сверху.
    center=False — только размер, координаты не трогаем (важно при догрузке полей).
    """
    sw, sh = _screen_size(window)
    max_w = max(min_width, int(sw * max_width_ratio))
    max_h = max(min_height, int(sh * max_height_ratio))
    w = max(min_width, min(width, max_w))
    h = max(min_height, min(height, max_h))
    window.minsize(min_width, min_height)
    if not center:
        window.geometry(f'{w}x{h}')
        return w, h

    parent = getattr(window, 'master', None)
    x = (sw - w) // 2
    y = (sh - h) // 2
    if parent is not None:
        try:
            parent.update_idletasks()
            px = int(parent.winfo_rootx())
            py = int(parent.winfo_rooty())
            pw = max(1, int(parent.winfo_width()))
            ph = max(1, int(parent.winfo_height()))
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
        except (tk.TclError, ValueError, TypeError):
            pass

    x = max(WIN_EDGE_MARGIN, min(x, max(WIN_EDGE_MARGIN, sw - w - WIN_EDGE_MARGIN)))
    y = max(WIN_TOP_MARGIN, min(y, max(WIN_TOP_MARGIN, sh - h - WIN_EDGE_MARGIN)))
    window.geometry(f'{w}x{h}+{x}+{y}')
    return w, h


@dataclass
class UiFontSettings:
    family: str
    size: int

    @classmethod
    def defaults(cls, root: tk.Misc) -> 'UiFontSettings':
        family = _pick_best_font_family(root)
        actual_size = int(tkfont.nametofont('TkDefaultFont').actual(displayof=root)['size'])
        size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, actual_size or 11))
        return cls(family=family, size=size)

    @classmethod
    def load(cls, root: tk.Misc) -> 'UiFontSettings':
        defaults = cls.defaults(root)
        if not UI_SETTINGS_PATH.is_file():
            return defaults
        try:
            raw = json.loads(UI_SETTINGS_PATH.read_text(encoding='utf-8'))
            family = str(raw.get('font_family', defaults.family)).strip() or defaults.family
            size = int(raw.get('font_size', defaults.size))
            size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))
            resolved = _resolve_font_family(root, family)
            return cls(family=resolved, size=size)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return defaults

    def save(self) -> None:
        UI_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {'font_family': self.family, 'font_size': self.size}
        UI_SETTINGS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    def tk_font(self, bold: bool = False) -> tuple[str, int, str] | tuple[str, int]:
        if bold:
            return (self.family, self.size, 'bold')
        return (self.family, self.size)

    def tree_rowheight(self) -> int:
        return self.size + 10


_PREFERRED_FONT_FAMILIES: tuple[str, ...] = (
    'Segoe UI',
    'Arial',
    'Helvetica Neue',
    'Helvetica',
    'DejaVu Sans',
    'Liberation Sans',
    'Noto Sans',
    'Ubuntu',
    'Cantarell',
)


def _pick_best_font_family(root: tk.Misc) -> str:
    available = {name.casefold(): name for name in tkfont.families(root)}
    for preferred in _PREFERRED_FONT_FAMILIES:
        if preferred.casefold() in available:
            return available[preferred.casefold()]
    return str(tkfont.nametofont('TkDefaultFont').actual(displayof=root)['family'])


def _resolve_font_family(root: tk.Misc, family: str) -> str:
    available = {name.casefold(): name for name in tkfont.families(root)}
    key = family.strip().casefold()
    if key in available:
        return available[key]
    return _pick_best_font_family(root)


def _sorted_font_families(root: tk.Misc) -> list[str]:
    return sorted(tkfont.families(root), key=str.casefold)


DATA_TREE_STYLE = 'Data.Treeview'
DATA_LABEL_STYLE = 'Data.TLabel'
CARD_BG = '#EAF6E4'  # нежно-салатовый фон карточки персоны
CARD_FRAME_STYLE = 'Card.TFrame'
CARD_LABEL_STYLE = 'Card.TLabel'
CARD_LABELED_FRAME_STYLE = 'Card.TLabelframe'


def _apply_data_fonts(style: ttk.Style, settings: UiFontSettings) -> None:
    """Шрифт для данных + подписей карточки; системные кнопки оставляем на TkDefaultFont."""
    normal = settings.tk_font()
    rowheight = settings.tree_rowheight()
    style.configure(DATA_TREE_STYLE, font=normal, rowheight=rowheight)
    style.configure(DATA_LABEL_STYLE, font=normal)
    style.configure(CARD_LABEL_STYLE, font=normal, background=CARD_BG)


def _apply_card_styles(style: ttk.Style) -> None:
    style.configure(CARD_FRAME_STYLE, background=CARD_BG)
    style.configure(CARD_LABEL_STYLE, background=CARD_BG)
    style.configure(CARD_LABELED_FRAME_STYLE, background=CARD_BG)
    style.configure(f'{CARD_LABELED_FRAME_STYLE}.Label', background=CARD_BG)


def _apply_app_fonts(root: tk.Misc, settings: UiFontSettings) -> None:
    """Применить выбранный шрифт к стандартным именованным шрифтам Tk."""
    family = settings.family
    size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, settings.size))
    ui_size = max(9, min(14, size - 2 if size >= 12 else size))
    for name, sz in (
        ('TkDefaultFont', ui_size),
        ('TkTextFont', size),
        ('TkHeadingFont', ui_size),
        ('TkMenuFont', ui_size),
        ('TkCaptionFont', ui_size),
    ):
        try:
            tkfont.nametofont(name).configure(family=family, size=sz)
        except tk.TclError:
            continue


def _bind_return_to_next(widget: tk.Misc, next_widget: tk.Misc) -> None:
    """Enter / Return переводит фокус на следующее поле формы."""

    def _go(_event: tk.Event) -> str:
        next_widget.focus_set()
        return 'break'

    widget.bind('<Return>', _go)
    widget.bind('<KP_Enter>', _go)


@dataclass
class ResidenceData:
    address: str
    kind: str = 'current'  # current | past
    period_note: str | None = None


@dataclass
class PersonData:
    first_name: str
    last_name: str
    middle_name: str | None
    maiden_name: str | None
    gender: Gender
    date_of_birth: PartialDate | None
    date_of_death: PartialDate | None
    place_of_birth: str | None
    place_of_death: str | None
    burial_place: str | None
    death_cause: DeathCause | None
    biography: str | None
    archive_records: str | None
    phones: list[str]
    name_variants: list[str]
    residences: list[ResidenceData]


RESIDENCE_KIND_LABELS: dict[str, str] = {
    'current': 'Сейчас',
    'past': 'В прошлом',
}
RESIDENCE_KIND_RU_TO_KEY: dict[str, str] = {v: k for k, v in RESIDENCE_KIND_LABELS.items()}


def format_residence_line(item: ResidenceData) -> str:
    addr = item.address.strip()
    if item.kind == 'past':
        period = f' ({item.period_note})' if item.period_note else ''
        return f'ранее{period}: {addr}'
    return f'сейчас: {addr}'


def _load_person_phones(session: Session, person_id: int) -> list[str]:
    stmt = select(Phone.number).where(Phone.person_id == person_id).order_by(Phone.id)
    return list(session.scalars(stmt).all())


def _load_person_name_variants(session: Session, person_id: int) -> list[str]:
    stmt = select(NameVariant.name).where(NameVariant.person_id == person_id).order_by(NameVariant.id)
    return list(session.scalars(stmt).all())


def _load_person_residences(session: Session, person_id: int) -> list[ResidenceData]:
    rows = session.execute(
        select(Address).where(Address.person_id == person_id).order_by(Address.id)
    ).scalars().all()
    result: list[ResidenceData] = []
    for row in rows:
        kind = (row.kind or 'current').strip().lower()
        if kind not in ('current', 'past'):
            kind = 'current'
        result.append(
            ResidenceData(
                address=row.address,
                kind=kind,
                period_note=row.period_note,
            )
        )
    return result


def _save_person_contacts(
    session: Session,
    person_id: int,
    phones: list[str],
    name_variants: list[str],
    residences: list[ResidenceData],
) -> None:
    session.execute(delete(Phone).where(Phone.person_id == person_id))
    session.execute(delete(NameVariant).where(NameVariant.person_id == person_id))
    session.execute(delete(Address).where(Address.person_id == person_id))
    for number in phones:
        session.add(Phone(person_id=person_id, number=number))
    for name in name_variants:
        session.add(NameVariant(person_id=person_id, name=name))
    for item in residences:
        session.add(
            Address(
                person_id=person_id,
                address=item.address,
                kind=item.kind,
                period_note=item.period_note,
            )
        )


GENDER_LABELS_RU: dict[str, str] = {
    'male': 'Мужской',
    'female': 'Женский',
    'other': 'Другой',
}
GENDER_COMBO_LABELS: list[str] = list(GENDER_LABELS_RU.values())
GENDER_RU_TO_KEY: dict[str, str] = {label: key for key, label in GENDER_LABELS_RU.items()}

DEATH_CAUSE_LABELS_RU: dict[str, str] = {
    DeathCause.NATURAL.value: 'Естественная',
    DeathCause.ILLNESS.value: 'По болезни',
    DeathCause.OTHER.value: 'Другое',
    DeathCause.UNKNOWN.value: 'Неизвестно',
}
DEATH_CAUSE_COMBO_LABELS: list[str] = list(DEATH_CAUSE_LABELS_RU.values())
DEATH_CAUSE_RU_TO_KEY: dict[str, str] = {
    label: key for key, label in DEATH_CAUSE_LABELS_RU.items()
}


def format_date_display(value: PartialDate | date | None, *, empty: str = '—') -> str:
    if value is None:
        return empty
    if isinstance(value, PartialDate):
        return format_partial_display(value, empty=empty)
    if isinstance(value, date):
        return format_partial_display(PartialDate.from_full_date(value), empty=empty)
    return empty


def parse_date_entry(date_str: str, field_label: str) -> PartialDate | None | bool:
    """PartialDate | None — ок; False — ошибка показана."""
    if not date_str.strip():
        return None
    parsed = try_parse_partial_date(date_str)
    if parsed is None:
        messagebox.showerror(
            'Ошибка',
            f'Некорректная {field_label}.\nДопустимо: {DATE_ENTRY_HINT}',
        )
        return False
    return parsed


def _person_birth_partial(person: Person) -> PartialDate | None:
    return person_partial_from_columns(
        year=person.birth_year,
        month=person.birth_month,
        day=person.birth_day,
        approx=person.birth_approx,
        legacy=person.date_of_birth,
    )


def _person_death_partial(person: Person) -> PartialDate | None:
    return person_partial_from_columns(
        year=person.death_year,
        month=person.death_month,
        day=person.death_day,
        approx=person.death_approx,
        legacy=person.date_of_death,
    )


def _apply_partial_to_person(
    person: Person,
    birth: PartialDate | None,
    death: PartialDate | None,
) -> None:
    b = partial_to_column_values(birth)
    person.birth_year = b['year']  # type: ignore[assignment]
    person.birth_month = b['month']  # type: ignore[assignment]
    person.birth_day = b['day']  # type: ignore[assignment]
    person.birth_approx = b['approx']  # type: ignore[assignment]
    person.date_of_birth = b['sort_date']  # type: ignore[assignment]

    d = partial_to_column_values(death)
    person.death_year = d['year']  # type: ignore[assignment]
    person.death_month = d['month']  # type: ignore[assignment]
    person.death_day = d['day']  # type: ignore[assignment]
    person.death_approx = d['approx']  # type: ignore[assignment]
    person.date_of_death = d['sort_date']  # type: ignore[assignment]


class DateMaskEntry(ttk.Entry):
    """Поле даты: полная / месяц-год / год / ~год."""

    def __init__(self, parent: tk.Misc, textvariable: tk.StringVar | None = None, **kwargs) -> None:
        self._date_var = textvariable or tk.StringVar()
        super().__init__(parent, textvariable=self._date_var, width=kwargs.pop('width', 18), **kwargs)
        self._updating = False
        self.bind('<KeyRelease>', self._on_key_release)
        self.bind('<FocusOut>', self._on_focus_out)

    def _on_key_release(self, event: tk.Event) -> None:
        if self._updating:
            return
        if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End'):
            return
        raw = self._date_var.get()
        if any(ch.isalpha() for ch in raw) or raw.lstrip().startswith(('~', '≈')):
            return
        digits = ''.join(ch for ch in raw if ch.isdigit())[:8]
        parsed = try_parse_partial_date(raw)
        if parsed is not None and len(digits) >= 8 and parsed.day is not None:
            formatted = format_partial_entry(parsed)
        else:
            formatted = _mask_date_digits(digits)
        if formatted == raw:
            return
        self._updating = True
        self._date_var.set(formatted)
        cursor = self._cursor_for_digits(min(8, len(''.join(ch for ch in formatted if ch.isdigit()))))
        self.icursor(cursor)
        self._updating = False

    def _on_focus_out(self, _event: tk.Event) -> None:
        raw = self._date_var.get().strip()
        if not raw:
            return
        parsed = try_parse_partial_date(raw)
        if parsed is None:
            return
        formatted = format_partial_entry(parsed)
        if formatted != raw:
            self._updating = True
            self._date_var.set(formatted)
            self._updating = False

    @staticmethod
    def _cursor_for_digits(digit_count: int) -> int:
        if digit_count <= 2:
            return digit_count
        if digit_count <= 4:
            return digit_count + 1
        return digit_count + 2


def _gender_key(gender: Gender | str | None) -> str:
    if gender is None:
        return ''
    if isinstance(gender, Gender):
        return gender.value
    return str(gender).strip().lower()


def _gender_display_raw(gender: Gender | str | None) -> str:
    if gender is None:
        return '-'
    return GENDER_LABELS_RU.get(_gender_key(gender), _gender_key(gender) or '-')


def _death_cause_key(cause: DeathCause | str | None) -> str:
    if cause is None:
        return ''
    if isinstance(cause, DeathCause):
        return cause.value
    return str(cause).strip().lower()


def _death_cause_display_raw(cause: DeathCause | str | None) -> str:
    if cause is None:
        return '—'
    return DEATH_CAUSE_LABELS_RU.get(_death_cause_key(cause), _death_cause_key(cause) or '—')


# Семантика записи Relationship:
# person_id — субъект, person_id_related — второй человек;
# relationship_type: роль второго по отношению к первому
# (у person_id второй — это его отец / мать / сын / супруга / …).

REL_LABELS_RU: dict[str, str] = {
    'father': 'Отец',
    'mother': 'Мать',
    'husband': 'Супруг',
    'wife': 'Супруга',
    'brother': 'Брат',
    'sister': 'Сестра',
    'son': 'Сын',
    'daughter': 'Дочь',
    'uncle': 'Дядя',
    'aunt': 'Тётя',
    'nephew': 'Племянник',
    'niece': 'Племянница',
    'grandson': 'Внук',
    'granddaughter': 'Внучка',
    'grandfather': 'Дедушка',
    'grandmother': 'Бабушка',
    # устаревшие ключи — только для чтения старых БД
    'child': 'Ребёнок',
    'spouse': 'Супруг(а)',
    'sibling': 'Брат или сестра',
    'parent': 'Родитель',
}

REL_ORDER_FOR_ADD: tuple[str, ...] = (
    'father',
    'mother',
    'husband',
    'wife',
    'brother',
    'sister',
    'son',
    'daughter',
    'uncle',
    'aunt',
    'nephew',
    'niece',
    'grandson',
    'granddaughter',
)

REL_COMBO_LABELS: list[str] = [REL_LABELS_RU[k] for k in REL_ORDER_FOR_ADD]
RU_LABEL_TO_KEY: dict[str, str] = {REL_LABELS_RU[k]: k for k in REL_ORDER_FOR_ADD}

# Базовые обратные роли (до уточнения по полу второго человека).
_REVERSE_BASE: dict[str, str] = {
    'father': 'child',
    'mother': 'child',
    'son': 'parent',
    'daughter': 'parent',
    'child': 'parent',
    'parent': 'child',
    'husband': 'wife',
    'wife': 'husband',
    'spouse': 'spouse',
    'brother': 'sibling',
    'sister': 'sibling',
    'sibling': 'sibling',
    'uncle': 'nibling',
    'aunt': 'nibling',
    'nephew': 'pibling',
    'niece': 'pibling',
    'grandson': 'grandparent',
    'granddaughter': 'grandparent',
    'grandfather': 'grandchild',
    'grandmother': 'grandchild',
}

_PARENT_CHILD_KEYS = frozenset({'father', 'mother', 'son', 'daughter', 'child', 'parent'})
_SPOUSE_KEYS = frozenset({'husband', 'wife', 'spouse'})
_SIBLING_KEYS = frozenset({'brother', 'sister', 'sibling'})
_NIBLING_KEYS = frozenset({'nephew', 'niece'})
_PIBLING_KEYS = frozenset({'uncle', 'aunt'})
_GRANDCHILD_KEYS = frozenset({'grandson', 'granddaughter'})
_GRANDPARENT_KEYS = frozenset({'grandfather', 'grandmother'})


def _refine_role_by_gender(base_role: str, person: Person | None) -> str:
    """Уточнить роль (сын/дочь, мама/папа, …) по полу человека."""
    g = _gender_key(person.gender) if person is not None else ''
    if base_role == 'child':
        if g == 'female':
            return 'daughter'
        if g == 'male':
            return 'son'
        return 'child'
    if base_role == 'parent':
        if g == 'female':
            return 'mother'
        if g == 'male':
            return 'father'
        return 'parent'
    if base_role == 'sibling':
        if g == 'female':
            return 'sister'
        if g == 'male':
            return 'brother'
        return 'sibling'
    if base_role == 'nibling':
        if g == 'female':
            return 'niece'
        if g == 'male':
            return 'nephew'
        return 'nephew'
    if base_role == 'pibling':
        if g == 'female':
            return 'aunt'
        if g == 'male':
            return 'uncle'
        return 'uncle'
    if base_role == 'grandparent':
        if g == 'female':
            return 'grandmother'
        if g == 'male':
            return 'grandfather'
        return 'parent'
    if base_role == 'grandchild':
        if g == 'female':
            return 'granddaughter'
        if g == 'male':
            return 'grandson'
        return 'child'
    return base_role


def _reverse_relationship_type(stored_type: str, other: Person | None = None) -> str:
    """Обратная роль person_id для P=person_id_related; other — тот, кто в роли для P."""
    t = (stored_type or '').strip().lower()
    base = _REVERSE_BASE.get(t, t)
    return _refine_role_by_gender(base, other)


def _rel_type_label(type_key: str) -> str:
    return REL_LABELS_RU.get((type_key or '').strip().lower(), type_key or '?')


def _person_short_fio(person: Person) -> str:
    parts = [person.last_name or '', person.first_name or '']
    if person.middle_name:
        parts.append(person.middle_name)
    return ' '.join(p for p in parts if p).strip() or '—'


def _parent_role_word(type_key: str, person: Person) -> str:
    k = (type_key or '').strip().lower()
    if k == 'mother' or (k == 'parent' and _gender_key(person.gender) == 'female'):
        return 'мама'
    if k == 'father' or (k == 'parent' and _gender_key(person.gender) == 'male'):
        return 'папа'
    return 'родитель'


def _child_role_word(type_key: str, person: Person) -> str:
    k = (type_key or '').strip().lower()
    if k == 'daughter' or (k == 'child' and _gender_key(person.gender) == 'female'):
        return 'дочь'
    if k == 'son' or (k == 'child' and _gender_key(person.gender) == 'male'):
        return 'сын'
    return 'ребёнок'


def format_relationships_grouped(
    edges: list[tuple[Relationship, Person, str]],
) -> str:
    """Текст для карточки: «Родители: мама …, папа …» и т.п."""
    parents: list[str] = []
    spouses: list[str] = []
    children: list[str] = []
    siblings: list[str] = []
    uncles_aunts: list[str] = []
    nephews: list[str] = []
    grandparents: list[str] = []
    grandchildren: list[str] = []
    other: list[str] = []

    for _rel, person, type_key in edges:
        k = (type_key or '').strip().lower()
        fio = _person_short_fio(person)
        if k in ('father', 'mother', 'parent'):
            parents.append(f'{_parent_role_word(k, person)} {fio}')
        elif k in _SPOUSE_KEYS:
            spouses.append(f'{_rel_type_label(k).lower()} {fio}')
        elif k in ('son', 'daughter', 'child'):
            children.append(f'{_child_role_word(k, person)} {fio}')
        elif k in _SIBLING_KEYS:
            siblings.append(f'{_rel_type_label(k).lower()} {fio}')
        elif k in _PIBLING_KEYS:
            uncles_aunts.append(f'{_rel_type_label(k).lower()} {fio}')
        elif k in _NIBLING_KEYS:
            nephews.append(f'{_rel_type_label(k).lower()} {fio}')
        elif k in _GRANDPARENT_KEYS:
            grandparents.append(f'{_rel_type_label(k).lower()} {fio}')
        elif k in _GRANDCHILD_KEYS:
            grandchildren.append(f'{_rel_type_label(k).lower()} {fio}')
        else:
            other.append(f'{_rel_type_label(k)}: {fio}')

    lines: list[str] = []
    if parents:
        lines.append('Родители: ' + ', '.join(parents))
    if spouses:
        lines.append('Супруги: ' + ', '.join(spouses))
    if children:
        lines.append('Дети: ' + ', '.join(children))
    if siblings:
        lines.append('Братья и сёстры: ' + ', '.join(siblings))
    if grandparents:
        lines.append('Бабушки и дедушки: ' + ', '.join(grandparents))
    if grandchildren:
        lines.append('Внуки: ' + ', '.join(grandchildren))
    if uncles_aunts:
        lines.append('Дяди и тёти: ' + ', '.join(uncles_aunts))
    if nephews:
        lines.append('Племянники: ' + ', '.join(nephews))
    lines.extend(other)
    return '\n'.join(lines)


def iter_person_edges_view(
    session: Session, person_id: int
) -> list[tuple[Relationship, Person, str]]:
    """Все связи для карточки person_id: (строка БД, второй человек, ключ типа для подписи)."""
    rows: list[tuple[Relationship, Person, str]] = []
    for rel in session.execute(
        select(Relationship).where(Relationship.person_id == person_id).order_by(Relationship.id)
    ).scalars().all():
        other = session.get(Person, rel.person_id_related)
        if other:
            k = (rel.relationship_type or '').strip().lower()
            rows.append((rel, other, k))
    for rel in session.execute(
        select(Relationship)
        .where(Relationship.person_id_related == person_id)
        .order_by(Relationship.id)
    ).scalars().all():
        other = session.get(Person, rel.person_id)
        if other:
            # other — тот, кто создал запись; для P уточняем его роль по полу other
            k = _reverse_relationship_type(rel.relationship_type, other)
            rows.append((rel, other, k))
    rows.sort(
        key=lambda x: (
            x[1].last_name.lower(),
            x[1].first_name.lower(),
            x[0].id,
        )
    )
    return rows


def _equivalent_type_groups(type_key: str) -> frozenset[str]:
    t = type_key.strip().lower()
    if t in _PARENT_CHILD_KEYS:
        return _PARENT_CHILD_KEYS
    if t in _SPOUSE_KEYS:
        return _SPOUSE_KEYS
    if t in _SIBLING_KEYS:
        return _SIBLING_KEYS
    if t in _NIBLING_KEYS | _PIBLING_KEYS:
        return _NIBLING_KEYS | _PIBLING_KEYS
    if t in _GRANDCHILD_KEYS | _GRANDPARENT_KEYS:
        return _GRANDCHILD_KEYS | _GRANDPARENT_KEYS
    return frozenset({t})


def _has_equivalent_relationship(session: Session, person_id: int, related_id: int, type_key: str) -> bool:
    """Та же семантика, что и при добавлении (в т.ч. обратная запись)."""
    t = type_key.strip().lower()
    group = _equivalent_type_groups(t)

    if session.execute(
        select(Relationship).where(
            Relationship.person_id == person_id,
            Relationship.person_id_related == related_id,
            Relationship.relationship_type.in_(tuple(group)),
        )
    ).scalar_one_or_none():
        return True

    if session.execute(
        select(Relationship).where(
            Relationship.person_id == related_id,
            Relationship.person_id_related == person_id,
            Relationship.relationship_type.in_(tuple(group)),
        )
    ).scalar_one_or_none():
        return True

    return False


class GenealogyApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title('Семейное древо')
        sw, sh = _screen_size(root)
        _apply_window_geometry(
            root,
            min(1200, int(sw * 0.9)),
            min(800, int(sh * 0.85)),
            min_width=640,
            min_height=480,
        )

        self.db_session = SessionLocal()
        self._font_settings = UiFontSettings.load(root)
        self._style = ttk.Style(root)
        _apply_card_styles(self._style)
        _apply_app_fonts(root, self._font_settings)
        _apply_data_fonts(self._style, self._font_settings)
        self._sort_mode: str = 'fio'  # fio | birth_year | death_year
        self._sort_ascending: bool = True

        self._create_widgets()
        self._load_people()
        self._clear_info_panel()

    def on_closing(self) -> None:
        self.db_session.close()
        self.root.destroy()

    def _create_widgets(self) -> None:
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(top_frame, text='Добавить персону', command=self._add_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='Редактировать', command=self._edit_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='Удалить', command=self._delete_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='Связи', command=self._manage_relationships).pack(side=tk.LEFT, padx=5)

        ttk.Label(top_frame, text='Сортировка:').pack(side=tk.LEFT, padx=(16, 4))
        self._sort_combo_var = tk.StringVar()
        self._sort_combo = ttk.Combobox(
            top_frame,
            textvariable=self._sort_combo_var,
            values=list(_SORT_OPTION_LABELS),
            state='readonly',
            width=14,
        )
        self._sort_combo.pack(side=tk.LEFT, padx=(0, 4))
        self._sort_combo.bind('<<ComboboxSelected>>', self._on_sort_combo_selected)
        self._btn_sort_dir = ttk.Button(
            top_frame,
            text='↑',
            width=3,
            command=self._toggle_sort_direction,
        )
        self._btn_sort_dir.pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(
            top_frame,
            text='✕',
            width=3,
            command=self._reset_sort,
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(top_frame, text='Настройки', command=self._open_settings).pack(side=tk.RIGHT, padx=5)

        self._paned = ttk.Panedwindow(self.root, orient=tk.VERTICAL)
        self._paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        middle_frame = ttk.Frame(self._paned, padding=10)
        self._paned.add(middle_frame, weight=3)

        bottom_outer = ttk.Frame(self._paned, padding=(10, 0, 10, 10))
        self._paned.add(bottom_outer, weight=1)

        info_shell = ttk.LabelFrame(
            bottom_outer,
            text='Карточка персоны',
            padding=8,
            style=CARD_LABELED_FRAME_STYLE,
        )
        info_shell.pack(fill=tk.BOTH, expand=True)

        canvas_row = ttk.Frame(info_shell, style=CARD_FRAME_STYLE)
        canvas_row.pack(fill=tk.BOTH, expand=True)
        canvas_row.columnconfigure(0, weight=1)
        canvas_row.rowconfigure(0, weight=1)

        self._info_canvas = tk.Canvas(
            canvas_row,
            highlightthickness=0,
            borderwidth=0,
            background=CARD_BG,
        )
        info_scroll = ttk.Scrollbar(canvas_row, orient=tk.VERTICAL, command=self._info_canvas.yview)
        self._info_canvas.configure(yscrollcommand=info_scroll.set)
        self._info_canvas.grid(row=0, column=0, sticky=tk.NSEW)
        info_scroll.grid(row=0, column=1, sticky=tk.NS)

        self._info_grid = ttk.Frame(self._info_canvas, style=CARD_FRAME_STYLE)
        self._info_canvas_window = self._info_canvas.create_window(
            (0, 0), window=self._info_grid, anchor=tk.NW
        )

        def row(r: int, title: str) -> ttk.Label:
            ttk.Label(
                self._info_grid,
                text=title,
                anchor=tk.W,
                style=CARD_LABEL_STYLE,
            ).grid(row=r, column=0, sticky=tk.NW, padx=(0, 10), pady=1)
            lbl = ttk.Label(
                self._info_grid,
                text='—',
                anchor=tk.W,
                style=DATA_LABEL_STYLE,
            )
            lbl.grid(row=r, column=1, sticky=tk.EW, pady=1)
            return lbl

        self._info_name = row(0, 'ФИО:')
        self._info_maiden = row(1, 'Прежн. фам.:')
        self._info_middle = row(2, 'Отчество:')
        self._info_gender = row(3, 'Пол:')
        self._info_birth = row(4, 'Рождение:')
        self._info_birth_place = row(5, 'Место рожд.:')
        self._info_death = row(6, 'Смерть:')
        self._info_death_place = row(7, 'Место смерти:')
        self._info_burial = row(8, 'Погребение:')
        self._info_death_cause = row(9, 'Причина смерти:')
        self._info_value_labels = (
            self._info_name,
            self._info_maiden,
            self._info_middle,
            self._info_gender,
            self._info_birth,
            self._info_birth_place,
            self._info_death,
            self._info_death_place,
            self._info_burial,
            self._info_death_cause,
        )

        def card_title(r: int, title: str) -> None:
            ttk.Label(
                self._info_grid,
                text=title,
                anchor=tk.NW,
                style=CARD_LABEL_STYLE,
            ).grid(row=r, column=0, sticky=tk.NW, pady=(4, 0))

        def card_text(r: int, height: int) -> tk.Text:
            widget = tk.Text(
                self._info_grid,
                height=height,
                wrap=tk.WORD,
                state=tk.DISABLED,
                relief=tk.FLAT,
                font=self._font_settings.tk_font(),
                background=CARD_BG,
                highlightthickness=0,
            )
            widget.grid(row=r, column=1, sticky=tk.EW, pady=(4, 0))
            return widget

        card_title(10, 'Варианты имени:')
        self._info_name_variants = card_text(10, 1)

        card_title(11, 'Телефоны:')
        self._info_phones = card_text(11, 1)

        card_title(12, 'Места жительства:')
        self._info_addresses = card_text(12, 1)

        card_title(13, 'Примечание:')
        self._info_bio = card_text(13, 3)

        card_title(14, 'Архивные записи:')
        self._info_archive = card_text(14, 3)

        card_title(15, 'Связи:')
        self._info_rels = card_text(15, 3)

        self._info_grid.columnconfigure(1, weight=1)

        self._info_phone_line_count = 1
        self._info_address_line_count = 1
        self._info_name_variant_line_count = 1

        self._info_grid.bind('<Configure>', self._on_info_grid_configure)
        self._info_canvas.bind('<Configure>', self._on_info_canvas_configure)
        self.root.bind('<Configure>', self._on_root_configure, add='+')
        self._info_canvas.bind('<Enter>', self._bind_info_mousewheel)
        self._info_canvas.bind('<Leave>', self._unbind_info_mousewheel)

        columns = ('id', 'Фамилия', 'Имя', 'Отчество', 'Пол', 'Дата рождения', 'Дата смерти', 'Примечание')
        self.tree = ttk.Treeview(middle_frame, columns=columns, show='headings', style=DATA_TREE_STYLE)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        self.tree.heading('Фамилия', text='Фамилия', command=lambda: self._set_sort('fio'))
        self.tree.heading(
            'Дата рождения', text='Дата рождения', command=lambda: self._set_sort('birth_year')
        )
        self.tree.heading(
            'Дата смерти', text='Дата смерти', command=lambda: self._set_sort('death_year')
        )

        self.tree.column('id', width=0, stretch=False)
        self.tree.column('Имя', width=120)
        self.tree.column('Фамилия', width=150)
        self.tree.column('Отчество', width=150)
        self.tree.column('Дата рождения', width=165)
        self.tree.column('Дата смерти', width=165)
        self.tree.column('Примечание', width=200)
        self._update_sort_ui()


        scrollbar = ttk.Scrollbar(middle_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<Double-1>', lambda e: self._edit_person())
        self.tree.bind('<<TreeviewSelect>>', lambda e: self._show_person_info())

        self.root.after_idle(self._relayout_info_panel)

    def _info_text_height_lines(self) -> int:
        size = self._font_settings.size
        if size >= 22:
            return 2
        if size >= 16:
            return 3
        return 4

    @staticmethod
    def _info_lines_for_record_count(count: int) -> int:
        if count <= 0:
            return 1
        return min(count, INFO_CONTACT_MAX_LINES)

    def _info_panel_canvas_height(self) -> int:
        line_h = self._font_settings.size + 10
        rows_h = 10 * line_h
        phone_lines = self._info_phone_line_count
        address_lines = self._info_address_line_count
        variant_lines = self._info_name_variant_line_count
        text_lines = self._info_text_height_lines()
        text_h = (phone_lines + address_lines + variant_lines + 3 * text_lines) * line_h
        return rows_h + text_h + 28

    def _on_info_grid_configure(self, _event: tk.Event | None = None) -> None:
        self._info_canvas.configure(scrollregion=self._info_canvas.bbox('all'))

    def _on_info_canvas_configure(self, event: tk.Event) -> None:
        self._info_canvas.itemconfigure(self._info_canvas_window, width=event.width)

    def _on_root_configure(self, _event: tk.Event | None = None) -> None:
        self._update_info_wraplengths()

    def _bind_info_mousewheel(self, _event: tk.Event) -> None:
        self._info_canvas.bind_all('<MouseWheel>', self._on_info_mousewheel)
        self._info_canvas.bind_all('<Button-4>', self._on_info_mousewheel_linux)
        self._info_canvas.bind_all('<Button-5>', self._on_info_mousewheel_linux)

    def _unbind_info_mousewheel(self, _event: tk.Event) -> None:
        self._info_canvas.unbind_all('<MouseWheel>')
        self._info_canvas.unbind_all('<Button-4>')
        self._info_canvas.unbind_all('<Button-5>')

    def _on_info_mousewheel(self, event: tk.Event) -> None:
        self._info_canvas.yview_scroll(int(-event.delta / 120), 'units')

    def _on_info_mousewheel_linux(self, event: tk.Event) -> None:
        delta = -1 if event.num == 4 else 1
        self._info_canvas.yview_scroll(delta, 'units')

    def _update_info_wraplengths(self) -> None:
        if not hasattr(self, '_info_bio'):
            return
        # Не ставим крошечный wraplength — иначе буквы «ломаются» по одной.
        width = self._info_bio.winfo_width()
        if width < 80:
            return
        wrap = max(200, width - 4)
        for lbl in self._info_value_labels:
            lbl.configure(wraplength=wrap)

    def _relayout_info_panel(self) -> None:
        text_lines = self._info_text_height_lines()
        font = self._font_settings.tk_font()
        self._info_name_variants.configure(height=self._info_name_variant_line_count, font=font)
        self._info_phones.configure(height=self._info_phone_line_count, font=font)
        self._info_addresses.configure(height=self._info_address_line_count, font=font)
        for widget in (self._info_bio, self._info_archive, self._info_rels):
            widget.configure(height=text_lines, font=font)

        desired = self._info_panel_canvas_height()
        root_h = self.root.winfo_height()
        if root_h > 1:
            max_h = max(140, int(root_h * 0.45))
            desired = min(desired, max_h)

        self._info_canvas.configure(height=desired)
        self._on_info_grid_configure()
        self._update_info_wraplengths()

    def _apply_font_settings(self) -> None:
        _apply_app_fonts(self.root, self._font_settings)
        _apply_card_styles(self._style)
        _apply_data_fonts(self._style, self._font_settings)
        self._relayout_info_panel()

    def _open_settings(self) -> None:
        dialog = FontSettingsDialog(self.root, self._font_settings)
        dialog.wait_window()
        if dialog.result:
            self._font_settings = dialog.result
            self._font_settings.save()
            self._apply_font_settings()

    def _set_info_text_widget(self, widget: tk.Text, text: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete('1.0', tk.END)
        widget.insert('1.0', text or '')
        widget.configure(state=tk.DISABLED)

    def _set_sort(self, mode: str) -> None:
        """Клик по заголовку колонки: тот же режим — смена направления, иначе возрастание."""
        if mode == self._sort_mode:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_mode = mode
            self._sort_ascending = True
        self._update_sort_ui()
        self._load_people()

    def _toggle_sort_direction(self) -> None:
        self._sort_ascending = not self._sort_ascending
        self._update_sort_ui()
        self._load_people()

    def _reset_sort(self) -> None:
        """Сброс к сортировке по ФИО по возрастанию."""
        if self._sort_mode == 'fio' and self._sort_ascending:
            return
        self._sort_mode = 'fio'
        self._sort_ascending = True
        self._update_sort_ui()
        self._load_people()

    def _on_sort_combo_selected(self, _event: tk.Event | None = None) -> None:
        label = self._sort_combo_var.get().strip()
        mode = _SORT_MODE_BY_LABEL.get(label)
        if mode is None or mode == self._sort_mode:
            return
        self._sort_mode = mode
        self._update_sort_ui()
        self._load_people()

    def _sort_arrow(self, mode: str) -> str:
        if mode != self._sort_mode:
            return ''
        return ' ↑' if self._sort_ascending else ' ↓'

    def _update_sort_ui(self) -> None:
        label = _SORT_LABEL_BY_MODE.get(self._sort_mode, _SORT_OPTION_LABELS[0])
        if self._sort_combo_var.get() != label:
            self._sort_combo_var.set(label)
        self._btn_sort_dir.configure(text='↑' if self._sort_ascending else '↓')
        self.tree.heading('Фамилия', text=f'Фамилия{self._sort_arrow("fio")}')
        self.tree.heading('Дата рождения', text=f'Дата рождения{self._sort_arrow("birth_year")}')
        self.tree.heading('Дата смерти', text=f'Дата смерти{self._sort_arrow("death_year")}')

    def _fio_key(self, person: Person) -> tuple[str, str, str]:
        return (
            (person.last_name or '').casefold(),
            (person.first_name or '').casefold(),
            (person.middle_name or '').casefold(),
        )

    def _partial_sort_key(self, partial: PartialDate | None) -> tuple[int, int, int, int]:
        """Без даты — всегда в конце; направление задаётся знаком года/месяца/дня."""
        if partial is None:
            return (1, 0, 0, 0)
        sign = 1 if self._sort_ascending else -1
        return (
            0,
            sign * partial.year,
            sign * (partial.month or 0),
            sign * (partial.day or 0),
        )

    def _ordered_people(self) -> list[Person]:
        people = list(self.db_session.execute(select(Person)).scalars().all())
        if self._sort_mode == 'birth_year':
            people.sort(
                key=lambda p: (*self._partial_sort_key(_person_birth_partial(p)), *self._fio_key(p))
            )
        elif self._sort_mode == 'death_year':
            people.sort(
                key=lambda p: (*self._partial_sort_key(_person_death_partial(p)), *self._fio_key(p))
            )
        else:
            people.sort(key=self._fio_key, reverse=not self._sort_ascending)
        return people

    def _load_people(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for person in self._ordered_people():
            gender_str = _gender_display_raw(person.gender)
            birth = _person_birth_partial(person)
            death = _person_death_partial(person)
            self.tree.insert('', tk.END, values=(
                person.id,
                person.last_name,
                person.first_name,
                person.middle_name or '',
                gender_str,
                format_date_display(birth, empty='-'),
                format_date_display(death, empty='-'),
                (person.biography or '')[:80] + ('…' if person.biography and len(person.biography) > 80 else ''),
            ))

    def _get_selected_person(self) -> Person | None:
        selected = self.tree.selection()
        if not selected:
            return None

        item = self.tree.item(selected[0])
        person_id: int = item['values'][0]

        stmt = select(Person).where(Person.id == person_id)
        return self.db_session.execute(stmt).scalar_one_or_none()

    def _add_person(self) -> None:
        dialog = PersonDialog(self.root, 'Добавить персону', font_settings=self._font_settings)
        dialog.wait_window()

        if dialog.result:
            person = Person(
                first_name=dialog.result.first_name,
                last_name=dialog.result.last_name,
                middle_name=dialog.result.middle_name,
                maiden_name=dialog.result.maiden_name,
                gender=dialog.result.gender,
                place_of_birth=dialog.result.place_of_birth,
                place_of_death=dialog.result.place_of_death,
                burial_place=dialog.result.burial_place,
                death_cause=dialog.result.death_cause,
                biography=dialog.result.biography,
                archive_records=dialog.result.archive_records,
            )
            _apply_partial_to_person(
                person,
                dialog.result.date_of_birth,
                dialog.result.date_of_death,
            )
            self.db_session.add(person)
            self.db_session.flush()
            _save_person_contacts(
                self.db_session,
                person.id,
                dialog.result.phones,
                dialog.result.name_variants,
                dialog.result.residences,
            )
            self.db_session.commit()
            self._load_people()

    def _edit_person(self) -> None:
        person = self._get_selected_person()
        if not person:
            messagebox.showwarning('Внимание', 'Выберите человека для редактирования')
            return

        dialog = PersonDialog(
            self.root,
            'Редактировать персону',
            person,
            font_settings=self._font_settings,
            phones=_load_person_phones(self.db_session, person.id),
            name_variants=_load_person_name_variants(self.db_session, person.id),
            residences=_load_person_residences(self.db_session, person.id),
        )
        dialog.wait_window()
        if dialog.result:
            person.first_name = dialog.result.first_name
            person.last_name = dialog.result.last_name
            person.middle_name = dialog.result.middle_name
            person.maiden_name = dialog.result.maiden_name
            person.gender = dialog.result.gender
            person.place_of_birth = dialog.result.place_of_birth
            person.place_of_death = dialog.result.place_of_death
            person.burial_place = dialog.result.burial_place
            person.death_cause = dialog.result.death_cause
            person.biography = dialog.result.biography
            person.archive_records = dialog.result.archive_records
            _apply_partial_to_person(
                person,
                dialog.result.date_of_birth,
                dialog.result.date_of_death,
            )
            _save_person_contacts(
                self.db_session,
                person.id,
                dialog.result.phones,
                dialog.result.name_variants,
                dialog.result.residences,
            )

            self.db_session.commit()
            self._load_people()

    def _delete_person(self) -> None:
        person = self._get_selected_person()
        if not person:
            messagebox.showwarning('Внимание', 'Выберите человека для удаления')
            return

        if not messagebox.askyesno(
            'Подтверждение',
            f'Удалить {person.last_name} {person.first_name}, все связи, телефоны и адреса?',
        ):
            return

        pid = person.id
        self.db_session.execute(
            delete(Relationship).where(
                or_(Relationship.person_id == pid, Relationship.person_id_related == pid)
            )
        )
        self.db_session.delete(person)
        self.db_session.commit()
        self._load_people()
        self._clear_info_panel()

    def _clear_info_panel(self) -> None:
        self._info_name.config(text='—')
        self._info_maiden.config(text='—')
        self._info_middle.config(text='—')
        self._info_gender.config(text='—')
        self._info_birth.config(text='—')
        self._info_birth_place.config(text='—')
        self._info_death.config(text='—')
        self._info_death_place.config(text='—')
        self._info_burial.config(text='—')
        self._info_death_cause.config(text='—')
        self._set_info_text_widget(self._info_bio, '')
        self._set_info_text_widget(self._info_archive, '')
        self._set_info_text_widget(self._info_rels, 'Выберите человека в таблице.')
        self._set_info_text_widget(self._info_phones, '')
        self._set_info_text_widget(self._info_addresses, '')
        self._set_info_text_widget(self._info_name_variants, '')
        self._info_phone_line_count = 1
        self._info_address_line_count = 1
        self._info_name_variant_line_count = 1
        self._relayout_info_panel()

    def _manage_relationships(self) -> None:
        person = self._get_selected_person()
        if not person:
            messagebox.showwarning('Внимание', 'Выберите человека')
            return
        RelationsDialog(self.root, person, self.db_session, font_settings=self._font_settings)
        self.db_session.expire_all()
        self._load_people()
        self._show_person_info()

    def _show_person_info(self) -> None:
        person = self._get_selected_person()
        if not person:
            self._clear_info_panel()
            return

        edges = iter_person_edges_view(self.db_session, person.id)
        rel_text = format_relationships_grouped(edges)

        phones = _load_person_phones(self.db_session, person.id)
        variants = _load_person_name_variants(self.db_session, person.id)
        residences = _load_person_residences(self.db_session, person.id)
        self._info_phone_line_count = self._info_lines_for_record_count(len(phones))
        self._info_name_variant_line_count = self._info_lines_for_record_count(len(variants))
        self._info_address_line_count = self._info_lines_for_record_count(len(residences))

        fio = f'{person.last_name} {person.first_name}'.strip()
        self._info_name.config(text=fio)
        self._info_maiden.config(text=person.maiden_name or '—')
        self._info_middle.config(text=person.middle_name or '—')
        self._info_gender.config(text=_gender_display_raw(person.gender))
        birth = _person_birth_partial(person)
        death = _person_death_partial(person)
        self._info_birth.config(text=format_date_display(birth))
        self._info_birth_place.config(text=person.place_of_birth or '—')
        self._info_death.config(text=format_date_display(death))
        if death:
            self._info_death_place.config(text=person.place_of_death or '—')
            self._info_burial.config(text=person.burial_place or '—')
            self._info_death_cause.config(text=_death_cause_display_raw(person.death_cause))
        else:
            self._info_death_place.config(text='—')
            self._info_burial.config(text='—')
            self._info_death_cause.config(text='—')
        self._set_info_text_widget(self._info_bio, person.biography or '')
        self._set_info_text_widget(self._info_archive, person.archive_records or '')
        self._set_info_text_widget(
            self._info_name_variants,
            '\n'.join(variants) if variants else '—',
        )
        self._set_info_text_widget(
            self._info_phones,
            '\n'.join(phones) if phones else '—',
        )
        self._set_info_text_widget(
            self._info_addresses,
            '\n'.join(format_residence_line(r) for r in residences) if residences else '—',
        )
        self._set_info_text_widget(self._info_rels, rel_text if rel_text else 'Нет связей.')
        self._relayout_info_panel()


class FontSettingsDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, current: UiFontSettings) -> None:
        super().__init__(parent)
        self.title('Настройки шрифта')
        self.transient(parent)
        self.grab_set()
        self.result: UiFontSettings | None = None

        self._current = current
        self._families = _sorted_font_families(parent)

        body = ttk.Frame(self, padding=12)
        body.pack(fill=tk.BOTH, expand=True)

        ttk.Label(body, text='Шрифт:').grid(row=0, column=0, sticky=tk.W, pady=4)
        self.family_var = tk.StringVar(value=current.family)
        family_combo = ttk.Combobox(
            body,
            textvariable=self.family_var,
            values=self._families,
            width=36,
        )
        family_combo.grid(row=0, column=1, sticky=tk.EW, pady=4, padx=(8, 0))

        ttk.Label(body, text='Размер:').grid(row=1, column=0, sticky=tk.W, pady=4)
        size_row = ttk.Frame(body)
        size_row.grid(row=1, column=1, sticky=tk.W, pady=4, padx=(8, 0))
        self.size_var = tk.IntVar(value=current.size)
        ttk.Spinbox(
            size_row,
            from_=MIN_FONT_SIZE,
            to=MAX_FONT_SIZE,
            textvariable=self.size_var,
            width=6,
        ).pack(side=tk.LEFT)
        ttk.Label(
            size_row,
            text=f'({MIN_FONT_SIZE}–{MAX_FONT_SIZE} пт)',
            foreground='gray',
        ).pack(side=tk.LEFT, padx=(8, 0))

        preview_shell = ttk.LabelFrame(body, text='Предпросмотр', padding=10)
        preview_shell.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(12, 8))
        self._preview_label = ttk.Label(
            preview_shell,
            text='Семейное древо — Иванов Иван Иванович',
            anchor=tk.W,
        )
        self._preview_label.pack(fill=tk.X)

        btn_row = ttk.Frame(body)
        btn_row.grid(row=3, column=0, columnspan=2, sticky=tk.E, pady=(8, 0))
        ttk.Button(btn_row, text='Сбросить', command=self._reset_defaults).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text='Отмена', command=self._on_cancel).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text='Применить', command=self._on_apply).pack(side=tk.LEFT, padx=4)

        body.columnconfigure(1, weight=1)
        self.family_var.trace_add('write', lambda *_: self._update_preview())
        self.size_var.trace_add('write', lambda *_: self._update_preview())
        self._update_preview()
        self.protocol('WM_DELETE_WINDOW', self._on_cancel)
        self.after_idle(
            lambda: _apply_window_geometry(self, 520, 300, min_width=400, min_height=260)
        )

    def _preview_settings(self) -> UiFontSettings | None:
        try:
            size = int(self.size_var.get())
        except (tk.TclError, ValueError):
            return None
        family = self.family_var.get().strip()
        if not family:
            return None
        size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))
        return UiFontSettings(family=_resolve_font_family(self, family), size=size)

    def _update_preview(self) -> None:
        preview = self._preview_settings()
        if preview:
            self._preview_label.configure(font=preview.tk_font())

    def _reset_defaults(self) -> None:
        defaults = UiFontSettings.defaults(self)
        self.family_var.set(defaults.family)
        self.size_var.set(defaults.size)

    def _on_apply(self) -> None:
        preview = self._preview_settings()
        if not preview:
            messagebox.showerror('Ошибка', 'Укажите корректный шрифт и размер', parent=self)
            return
        self.result = preview
        self.grab_release()
        self.destroy()

    def _on_cancel(self) -> None:
        self.grab_release()
        self.destroy()


class MultiValuePanel(ttk.LabelFrame):
    """Список строк (телефоны, адреса) с добавлением и удалением."""

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        initial: list[str] | None = None,
        *,
        font_settings: UiFontSettings | None = None,
        min_rows: int = 1,
        max_rows: int = 5,
        on_change: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, text=title, padding=4)
        self._min_rows = min_rows
        self._max_rows = max_rows
        self._on_change = on_change
        font = (font_settings or UiFontSettings.load(parent)).tk_font()

        list_row = ttk.Frame(self)
        list_row.pack(fill=tk.X)

        self._listbox = tk.Listbox(
            list_row,
            height=min_rows,
            exportselection=False,
            font=font,
        )
        self._scrollbar = ttk.Scrollbar(list_row, orient=tk.VERTICAL, command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=self._scrollbar.set)
        self._listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        for value in initial or []:
            if value.strip():
                self._listbox.insert(tk.END, value.strip())

        input_row = ttk.Frame(self)
        input_row.pack(fill=tk.X, pady=(4, 0))
        self._entry_var = tk.StringVar()
        self._entry = ttk.Entry(input_row, textvariable=self._entry_var, width=24)
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._entry.bind('<Return>', lambda _e: self._add_value())
        ttk.Button(input_row, text='+', command=self._add_value, width=3).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Button(input_row, text='−', command=self._remove_selected, width=3).pack(
            side=tk.LEFT, padx=(2, 0)
        )

        self._resize_list(notify=False)

    def _notify_change(self) -> None:
        if self._on_change:
            self._on_change()

    def _resize_list(self, notify: bool = True) -> None:
        count = self._listbox.size()
        rows = min(max(self._min_rows, count), self._max_rows)
        self._listbox.configure(height=rows)
        if count > self._max_rows:
            self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self._scrollbar.pack_forget()
        if notify:
            self._notify_change()

    def _add_value(self) -> None:
        value = self._entry_var.get().strip()
        if not value:
            return
        self._listbox.insert(tk.END, value)
        self._entry_var.set('')
        self._resize_list()

    def _remove_selected(self) -> None:
        selection = self._listbox.curselection()
        if not selection:
            return
        self._listbox.delete(selection[0])
        self._resize_list()

    def get_values(self) -> list[str]:
        return [
            self._listbox.get(i).strip()
            for i in range(self._listbox.size())
            if self._listbox.get(i).strip()
        ]


class ResidencePanel(ttk.LabelFrame):
    """Места жительства: сейчас / в прошлом (+ период)."""

    def __init__(
        self,
        parent: tk.Misc,
        initial: list[ResidenceData] | None = None,
        *,
        font_settings: UiFontSettings | None = None,
        min_rows: int = 1,
        max_rows: int = 5,
        on_change: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, text='Места жительства', padding=4)
        self._min_rows = min_rows
        self._max_rows = max_rows
        self._on_change = on_change
        self._items: list[ResidenceData] = []
        font = (font_settings or UiFontSettings.load(parent)).tk_font()

        list_row = ttk.Frame(self)
        list_row.pack(fill=tk.X)
        self._listbox = tk.Listbox(
            list_row,
            height=min_rows,
            exportselection=False,
            font=font,
        )
        self._scrollbar = ttk.Scrollbar(list_row, orient=tk.VERTICAL, command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=self._scrollbar.set)
        self._listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        for item in initial or []:
            if item.address.strip():
                self._items.append(
                    ResidenceData(
                        address=item.address.strip(),
                        kind=item.kind,
                        period_note=(item.period_note or '').strip() or None,
                    )
                )
                self._listbox.insert(tk.END, format_residence_line(self._items[-1]))

        kind_row = ttk.Frame(self)
        kind_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(kind_row, text='Тип:').pack(side=tk.LEFT)
        self._kind_var = tk.StringVar(value=RESIDENCE_KIND_LABELS['current'])
        self._kind_combo = ttk.Combobox(
            kind_row,
            textvariable=self._kind_var,
            values=list(RESIDENCE_KIND_LABELS.values()),
            state='readonly',
            width=12,
        )
        self._kind_combo.pack(side=tk.LEFT, padx=(4, 8))
        ttk.Label(kind_row, text='Период:').pack(side=tk.LEFT)
        self._period_var = tk.StringVar()
        self._period_entry = ttk.Entry(kind_row, textvariable=self._period_var, width=16)
        self._period_entry.pack(side=tk.LEFT, padx=(4, 0))
        self._kind_var.trace_add('write', self._sync_period_state)
        self._sync_period_state()

        input_row = ttk.Frame(self)
        input_row.pack(fill=tk.X, pady=(4, 0))
        self._entry_var = tk.StringVar()
        self._entry = ttk.Entry(input_row, textvariable=self._entry_var)
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._entry.bind('<Return>', lambda _e: self._add_value())
        ttk.Button(input_row, text='+', command=self._add_value, width=3).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Button(input_row, text='−', command=self._remove_selected, width=3).pack(
            side=tk.LEFT, padx=(2, 0)
        )

        self._resize_list(notify=False)

    def _sync_period_state(self, *_args: object) -> None:
        kind = RESIDENCE_KIND_RU_TO_KEY.get(self._kind_var.get().strip(), 'current')
        state = tk.NORMAL if kind == 'past' else tk.DISABLED
        self._period_entry.configure(state=state)
        if kind != 'past':
            self._period_var.set('')

    def _notify_change(self) -> None:
        if self._on_change:
            self._on_change()

    def _resize_list(self, notify: bool = True) -> None:
        count = self._listbox.size()
        rows = min(max(self._min_rows, count), self._max_rows)
        self._listbox.configure(height=rows)
        if count > self._max_rows:
            self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self._scrollbar.pack_forget()
        if notify:
            self._notify_change()

    def _add_value(self) -> None:
        address = self._entry_var.get().strip()
        if not address:
            return
        kind = RESIDENCE_KIND_RU_TO_KEY.get(self._kind_var.get().strip(), 'current')
        period = self._period_var.get().strip() or None if kind == 'past' else None
        item = ResidenceData(address=address, kind=kind, period_note=period)
        self._items.append(item)
        self._listbox.insert(tk.END, format_residence_line(item))
        self._entry_var.set('')
        self._period_var.set('')
        self._kind_var.set(RESIDENCE_KIND_LABELS['current'])
        self._resize_list()

    def _remove_selected(self) -> None:
        selection = self._listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        self._listbox.delete(idx)
        if 0 <= idx < len(self._items):
            del self._items[idx]
        self._resize_list()

    def get_values(self) -> list[ResidenceData]:
        return list(self._items)


class PersonDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        title: str,
        person: Person | None = None,
        *,
        font_settings: UiFontSettings | None = None,
        phones: list[str] | None = None,
        name_variants: list[str] | None = None,
        residences: list[ResidenceData] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.result: PersonData | None = None
        self._font_settings = font_settings or UiFontSettings.load(parent)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._fitted_once = False
        self._create_widgets(
            person,
            phones or [],
            name_variants or [],
            residences or [],
        )
        self.after_idle(lambda: self._fit_window(reposition=True))

    def _schedule_fit(self) -> None:
        # Только подстроить высоту/скролл — не сбрасывать позицию и ширину, заданные пользователем.
        self.after_idle(lambda: self._fit_window(reposition=False))

    def _on_form_configure(self, _event: tk.Event | None = None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self._canvas.itemconfigure(self._canvas_window, width=event.width)

    def _bind_form_mousewheel(self, _event: tk.Event) -> None:
        if self._scroll_visible:
            self._canvas.bind_all('<MouseWheel>', self._on_form_mousewheel)
            self._canvas.bind_all('<Button-4>', self._on_form_mousewheel_linux)
            self._canvas.bind_all('<Button-5>', self._on_form_mousewheel_linux)

    def _unbind_form_mousewheel(self, _event: tk.Event) -> None:
        self._canvas.unbind_all('<MouseWheel>')
        self._canvas.unbind_all('<Button-4>')
        self._canvas.unbind_all('<Button-5>')

    def _on_form_mousewheel(self, event: tk.Event) -> None:
        self._canvas.yview_scroll(int(-event.delta / 120), 'units')

    def _on_form_mousewheel_linux(self, event: tk.Event) -> None:
        delta = -1 if event.num == 4 else 1
        self._canvas.yview_scroll(delta, 'units')

    def _fit_window(self, *, reposition: bool | None = None) -> None:
        self.update_idletasks()
        form_h = self._form.winfo_reqheight()
        btn_h = self._btn_frame.winfo_reqheight()
        vertical_pad = 42
        total_h = form_h + btn_h + vertical_pad
        _, sh = _screen_size(self)
        max_h = int(sh * WIN_MAX_HEIGHT_RATIO)
        # Шире по умолчанию: две колонки + «Примечание» / архив рядом.
        width = max(1000, min(1120, self.winfo_reqwidth() + 48))
        if self._fitted_once and not reposition:
            # Сохраняем текущую ширину, если пользователь уже ресайзил окно.
            width = max(640, self.winfo_width())

        do_center = self._fitted_once is False if reposition is None else reposition

        if total_h <= max_h:
            self._scroll_visible = False
            self._vscroll.grid_remove()
            self._canvas.configure(height=form_h)
            _apply_window_geometry(
                self, width, total_h, min_width=720, min_height=280, center=do_center
            )
        else:
            self._scroll_visible = True
            canvas_h = max(200, max_h - btn_h - vertical_pad)
            self._canvas.configure(height=canvas_h)
            self._vscroll.grid(row=0, column=1, sticky=tk.NS)
            _apply_window_geometry(
                self, width, max_h, min_width=720, min_height=280, center=do_center
            )

        self._fitted_once = True
        self._on_form_configure()

    def _create_widgets(
        self,
        person: Person | None,
        phones: list[str],
        name_variants: list[str],
        residences: list[ResidenceData],
    ) -> None:
        self._scroll_visible = False

        body = ttk.Frame(self)
        body.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=(10, 0))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(body, highlightthickness=0, borderwidth=0)
        self._vscroll = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vscroll.set)
        self._canvas.grid(row=0, column=0, sticky=tk.NSEW)

        self._form = ttk.Frame(self._canvas)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._form, anchor=tk.NW)
        self._form.bind('<Configure>', self._on_form_configure)
        self._canvas.bind('<Configure>', self._on_canvas_configure)
        self._canvas.bind('<Enter>', self._bind_form_mousewheel)
        self._canvas.bind('<Leave>', self._unbind_form_mousewheel)

        form = self._form
        data_font = self._font_settings.tk_font()

        def _entry(parent: tk.Misc, textvariable: tk.StringVar, **kwargs) -> ttk.Entry:
            widget = ttk.Entry(parent, textvariable=textvariable, font=data_font, **kwargs)
            return widget

        # --- две колонки: слева ФИО/даты, справа имя/места ---
        columns = ttk.Frame(form)
        columns.pack(fill=tk.X)
        left = ttk.Frame(columns)
        right = ttk.Frame(columns)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        ttk.Label(left, text='Фамилия:').pack(anchor=tk.W)
        self.last_name_var = tk.StringVar(value=person.last_name if person else '')
        last_name_entry = _entry(left, self.last_name_var)
        last_name_entry.pack(fill=tk.X)

        ttk.Label(left, text='Девичья / прежняя фамилия:').pack(anchor=tk.W, pady=(8, 0))
        self.maiden_name_var = tk.StringVar(
            value=(person.maiden_name or '') if person else ''
        )
        maiden_entry = _entry(left, self.maiden_name_var)
        maiden_entry.pack(fill=tk.X)

        ttk.Label(right, text='Имя:').pack(anchor=tk.W)
        self.first_name_var = tk.StringVar(value=person.first_name if person else '')
        first_name_entry = _entry(right, self.first_name_var)
        first_name_entry.pack(fill=tk.X)

        ttk.Label(right, text='Отчество:').pack(anchor=tk.W, pady=(8, 0))
        self.middle_name_var = tk.StringVar(value=person.middle_name or '' if person else '')
        middle_name_entry = _entry(right, self.middle_name_var)
        middle_name_entry.pack(fill=tk.X)

        ttk.Label(left, text='Пол:').pack(anchor=tk.W, pady=(8, 0))
        if person and person.gender:
            gender_label = _gender_display_raw(person.gender)
        else:
            gender_label = GENDER_LABELS_RU[Gender.MALE.value]
        self.gender_var = tk.StringVar(value=gender_label)
        gender_combo = ttk.Combobox(
            left,
            textvariable=self.gender_var,
            values=GENDER_COMBO_LABELS,
            state='readonly',
            width=14,
            font=data_font,
        )
        gender_combo.pack(anchor=tk.W)

        ttk.Label(left, text='Дата рождения:').pack(anchor=tk.W, pady=(8, 0))
        birth_partial = _person_birth_partial(person) if person else None
        self.birth_date_var = tk.StringVar(
            value=format_partial_entry(birth_partial) if birth_partial else ''
        )
        birth_entry = DateMaskEntry(left, textvariable=self.birth_date_var)
        birth_entry.configure(font=data_font)
        birth_entry.pack(fill=tk.X)

        ttk.Label(right, text='Место рождения:').pack(anchor=tk.W, pady=(8, 0))
        self.place_of_birth_var = tk.StringVar(value=person.place_of_birth or '' if person else '')
        place_birth_entry = _entry(right, self.place_of_birth_var)
        place_birth_entry.pack(fill=tk.X)

        ttk.Label(left, text='Дата смерти (опционально):').pack(anchor=tk.W, pady=(8, 0))
        death_partial = _person_death_partial(person) if person else None
        self.death_date_var = tk.StringVar(
            value=format_partial_entry(death_partial) if death_partial else ''
        )
        self._death_date_entry = DateMaskEntry(left, textvariable=self.death_date_var)
        self._death_date_entry.configure(font=data_font)
        self._death_date_entry.pack(fill=tk.X)

        ttk.Label(
            form,
            text=DATE_INPUT_HELP,
            foreground='gray',
            justify=tk.LEFT,
            wraplength=960,
        ).pack(anchor=tk.W, pady=(6, 0))

        _bind_return_to_next(last_name_entry, maiden_entry)
        _bind_return_to_next(maiden_entry, first_name_entry)
        _bind_return_to_next(first_name_entry, middle_name_entry)
        _bind_return_to_next(middle_name_entry, gender_combo)
        _bind_return_to_next(gender_combo, birth_entry)
        _bind_return_to_next(birth_entry, place_birth_entry)
        _bind_return_to_next(place_birth_entry, self._death_date_entry)

        self._death_slot = ttk.Frame(form)
        self._death_slot.pack(fill=tk.X)
        self._death_details = ttk.Frame(self._death_slot)

        death_cols = ttk.Frame(self._death_details)
        death_cols.pack(fill=tk.X, pady=(8, 0))
        death_left = ttk.Frame(death_cols)
        death_right = ttk.Frame(death_cols)
        death_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        death_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        ttk.Label(death_left, text='Место смерти:').pack(anchor=tk.W)
        self.place_of_death_var = tk.StringVar(value=person.place_of_death or '' if person else '')
        _entry(death_left, self.place_of_death_var).pack(fill=tk.X)

        ttk.Label(death_right, text='Место погребения:').pack(anchor=tk.W)
        self.burial_place_var = tk.StringVar(
            value=(person.burial_place or '') if person else ''
        )
        _entry(death_right, self.burial_place_var).pack(fill=tk.X)

        ttk.Label(self._death_details, text='Причина смерти:').pack(anchor=tk.W, pady=(8, 0))
        if person and person.death_cause:
            death_cause_label = _death_cause_display_raw(person.death_cause)
        else:
            death_cause_label = DEATH_CAUSE_LABELS_RU[DeathCause.UNKNOWN.value]
        self.death_cause_var = tk.StringVar(value=death_cause_label)
        ttk.Combobox(
            self._death_details,
            textvariable=self.death_cause_var,
            values=DEATH_CAUSE_COMBO_LABELS,
            state='readonly',
            width=24,
            font=data_font,
        ).pack(anchor=tk.W)

        contacts = ttk.Frame(form)
        contacts.pack(fill=tk.X, pady=(8, 0))
        self._name_variants_panel = MultiValuePanel(
            contacts,
            'Варианты имени',
            name_variants,
            font_settings=self._font_settings,
            on_change=self._schedule_fit,
        )
        self._name_variants_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self._phones_panel = MultiValuePanel(
            contacts,
            'Телефоны',
            phones,
            font_settings=self._font_settings,
            on_change=self._schedule_fit,
        )
        self._phones_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        self._residences_panel = ResidencePanel(
            form,
            residences,
            font_settings=self._font_settings,
            on_change=self._schedule_fit,
        )
        self._residences_panel.pack(fill=tk.X, pady=(8, 0))

        # Архив и примечание друг под другом на всю ширину — иначе «Примечание» обрезается.
        ttk.Label(form, text='Архивные записи:').pack(anchor=tk.W, pady=(8, 0))
        archive_frame = ttk.Frame(form)
        archive_frame.pack(fill=tk.X)
        self.archive_text = tk.Text(
            archive_frame,
            height=3,
            wrap=tk.WORD,
            font=data_font,
        )
        self.archive_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        archive_sb = ttk.Scrollbar(archive_frame, command=self.archive_text.yview)
        archive_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.archive_text.configure(yscrollcommand=archive_sb.set)
        if person and person.archive_records:
            self.archive_text.insert('1.0', person.archive_records)

        ttk.Label(form, text='Примечание:').pack(anchor=tk.W, pady=(8, 0))
        bio_frame = ttk.Frame(form)
        bio_frame.pack(fill=tk.X)
        self.biography_text = tk.Text(
            bio_frame,
            height=3,
            wrap=tk.WORD,
            font=data_font,
        )
        self.biography_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(bio_frame, command=self.biography_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.biography_text.configure(yscrollcommand=sb.set)
        if person and person.biography:
            self.biography_text.insert('1.0', person.biography)

        self.death_date_var.trace_add('write', self._update_death_details_visibility)
        self._update_death_details_visibility()

        self._btn_frame = ttk.Frame(self)
        self._btn_frame.grid(row=1, column=0, pady=(8, 10))
        ttk.Button(self._btn_frame, text='OK', command=self._on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(self._btn_frame, text='Отмена', command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _has_complete_death_date(self) -> bool:
        return try_parse_partial_date(self.death_date_var.get()) is not None

    def _update_death_details_visibility(self, *_args: object) -> None:
        if self._has_complete_death_date():
            if not self._death_details.winfo_ismapped():
                self._death_details.pack(fill=tk.X)
        elif self._death_details.winfo_ismapped():
            self._death_details.pack_forget()
        self._schedule_fit()

    def _on_ok(self) -> None:
        first_name = self.first_name_var.get().strip()
        last_name = self.last_name_var.get().strip()

        if not first_name or not last_name:
            messagebox.showerror('Ошибка', 'Имя и фамилия обязательны')
            return

        birth = parse_date_entry(self.birth_date_var.get(), 'дата рождения')
        if birth is False:
            return
        death = parse_date_entry(self.death_date_var.get(), 'дата смерти')
        if death is False:
            return

        gender_label = self.gender_var.get().strip()
        gender_key = GENDER_RU_TO_KEY.get(gender_label)
        if not gender_key:
            messagebox.showerror('Ошибка', 'Выберите пол из списка')
            return
        gender = Gender(gender_key)

        if death is None:
            place_of_death = None
            burial_place = None
            death_cause = None
        else:
            place_of_death = self.place_of_death_var.get().strip() or None
            burial_place = self.burial_place_var.get().strip() or None
            cause_label = self.death_cause_var.get().strip()
            cause_key = DEATH_CAUSE_RU_TO_KEY.get(cause_label)
            if not cause_key:
                messagebox.showerror('Ошибка', 'Выберите причину смерти из списка')
                return
            death_cause = DeathCause(cause_key)

        self.result = PersonData(
            first_name=first_name,
            last_name=last_name,
            middle_name=self.middle_name_var.get().strip() or None,
            maiden_name=self.maiden_name_var.get().strip() or None,
            gender=gender,
            date_of_birth=birth,
            date_of_death=death,
            place_of_birth=self.place_of_birth_var.get().strip() or None,
            place_of_death=place_of_death,
            burial_place=burial_place,
            death_cause=death_cause,
            biography=self.biography_text.get('1.0', tk.END).strip() or None,
            archive_records=self.archive_text.get('1.0', tk.END).strip() or None,
            phones=self._phones_panel.get_values(),
            name_variants=self._name_variants_panel.get_values(),
            residences=self._residences_panel.get_values(),
        )
        self.destroy()


class RelationsDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        person: Person,
        session: Session,
        *,
        font_settings: UiFontSettings | None = None,
    ) -> None:
        super().__init__(parent)
        self.title(f'Связи — {person.last_name} {person.first_name}')
        self.transient(parent)
        self.grab_set()

        self.person = person
        self.db_session = session
        self._font_settings = font_settings or UiFontSettings.load(parent)
        self._edge_rows: list[tuple[Relationship, Person, str]] = []

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_widgets()
        self._reload_candidates()
        self._update_rel_listbox()

        self.protocol('WM_DELETE_WINDOW', self._on_close)
        self.after_idle(self._fit_window)

    def _fit_window(self) -> None:
        sw, sh = _screen_size(self)
        _apply_window_geometry(
            self,
            min(560, int(sw * 0.72)),
            min(480, int(sh * 0.72)),
            min_width=420,
            min_height=320,
        )

    def _on_window_configure(self, event: tk.Event) -> None:
        if event.widget is self and hasattr(self, '_hint_label'):
            self._hint_label.configure(wraplength=max(160, event.width - 48))

    def _save(self) -> None:
        """Связи уже пишутся в БД при добавлении/удалении; кнопка фиксирует состояние."""
        try:
            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
            messagebox.showerror('Ошибка', 'Не удалось сохранить изменения', parent=self)
            return
        messagebox.showinfo('Сохранено', 'Изменения сохранены', parent=self)

    def _save_and_close(self) -> None:
        try:
            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
            messagebox.showerror('Ошибка', 'Не удалось сохранить изменения', parent=self)
            return
        self._on_close()

    def _on_close(self) -> None:
        self.grab_release()
        self.destroy()

    def _create_widgets(self) -> None:
        main = ttk.Frame(self, padding=(10, 10, 10, 0))
        main.grid(row=0, column=0, sticky=tk.NSEW)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=2)
        main.grid_rowconfigure(3, weight=1)

        head = ttk.Label(
            main,
            text=f'Связи для: {self.person.last_name} {self.person.first_name}',
            font=('TkDefaultFont', 10, 'bold'),
        )
        head.grid(row=0, column=0, sticky=tk.W, pady=(0, 6))

        lf_pick = ttk.LabelFrame(main, text='1. Выберите человека в списке (мышью)', padding=8)
        lf_pick.grid(row=1, column=0, sticky=tk.NSEW, pady=(0, 6))
        lf_pick.grid_columnconfigure(0, weight=1)
        lf_pick.grid_rowconfigure(0, weight=1)

        cols = ('Фамилия', 'Имя', 'Отчество')
        self.candidates_tree = ttk.Treeview(
            lf_pick,
            columns=cols,
            show='headings',
            height=5,
            selectmode='browse',
            style=DATA_TREE_STYLE,
        )
        for c, w in zip(cols, (160, 120, 130)):
            self.candidates_tree.heading(c, text=c)
            self.candidates_tree.column(c, width=w)

        cs = ttk.Scrollbar(lf_pick, orient=tk.VERTICAL, command=self.candidates_tree.yview)
        self.candidates_tree.configure(yscrollcommand=cs.set)
        self.candidates_tree.grid(row=0, column=0, sticky=tk.NSEW)
        cs.grid(row=0, column=1, sticky=tk.NS)

        self.candidates_tree.bind('<Double-1>', lambda e: self._add_relationship())

        lf_add = ttk.LabelFrame(main, text='2. Тип связи и добавление', padding=8)
        lf_add.grid(row=2, column=0, sticky=tk.EW, pady=(0, 6))

        add_row = ttk.Frame(lf_add)
        add_row.pack(fill=tk.X)
        ttk.Label(add_row, text='Тип:').pack(side=tk.LEFT)
        default_ru = REL_LABELS_RU['wife']
        self.rel_type_var = tk.StringVar(value=default_ru)
        self.type_combo = ttk.Combobox(
            add_row,
            textvariable=self.rel_type_var,
            values=REL_COMBO_LABELS,
            state='readonly',
            width=18,
        )
        self.type_combo.pack(side=tk.LEFT, padx=(8, 12))
        ttk.Button(add_row, text='Добавить связь', command=self._add_relationship).pack(side=tk.LEFT)

        hint = (
            'Смысл: у персоны, для которой открыто окно, выбранный в списке — это '
            'её «Отец» / «Мать» / «Супруга» / «Сын» / «Брат» / «Тётя» и т.д. '
            '(как в поле «Тип»). Пример: чтобы у Владимира появились родители, '
            'откройте Владимира и добавьте «Мать» / «Отец». '
            'Двойной клик по строке списка тоже добавляет связь.'
        )
        self._hint_label = ttk.Label(lf_add, text=hint, wraplength=400, foreground='gray')
        self._hint_label.pack(anchor=tk.W, pady=(6, 0))

        lf_list = ttk.LabelFrame(main, text='3. Все связи (в том числе обратные)', padding=8)
        lf_list.grid(row=3, column=0, sticky=tk.NSEW)
        lf_list.grid_columnconfigure(0, weight=1)
        lf_list.grid_rowconfigure(0, weight=1)

        self.rel_listbox = tk.Listbox(
            lf_list,
            height=4,
            exportselection=False,
            font=self._font_settings.tk_font(),
        )
        rs = ttk.Scrollbar(lf_list, orient=tk.VERTICAL, command=self.rel_listbox.yview)
        self.rel_listbox.configure(yscrollcommand=rs.set)
        self.rel_listbox.grid(row=0, column=0, sticky=tk.NSEW)
        rs.grid(row=0, column=1, sticky=tk.NS)

        del_row = ttk.Frame(self, padding=(10, 6, 10, 0))
        del_row.grid(row=1, column=0, sticky=tk.EW)
        ttk.Button(del_row, text='Удалить выбранную связь', command=self._delete_relationship).pack(
            side=tk.LEFT
        )
        ttk.Label(
            del_row,
            text='Удаляется одна запись в базе (обратная «пропадёт» сама).',
            foreground='gray',
        ).pack(side=tk.LEFT, padx=(12, 0))

        bottom = ttk.Frame(self, padding=(10, 8, 10, 10))
        bottom.grid(row=2, column=0, sticky=tk.EW)
        ttk.Button(bottom, text='Сохранить и закрыть', command=self._save_and_close).pack(
            side=tk.RIGHT, padx=(8, 0)
        )
        ttk.Button(bottom, text='Сохранить', command=self._save).pack(side=tk.RIGHT)

        self.bind('<Configure>', self._on_window_configure, add='+')

    def _reload_candidates(self) -> None:
        for iid in self.candidates_tree.get_children():
            self.candidates_tree.delete(iid)

        stmt = (
            select(Person)
            .where(Person.id != self.person.id)
            .order_by(Person.last_name, Person.first_name)
        )
        for p in self.db_session.execute(stmt).scalars().all():
            self.candidates_tree.insert(
                '',
                tk.END,
                iid=str(p.id),
                values=(p.last_name, p.first_name, p.middle_name or ''),
            )

    def _selected_candidate_id(self) -> int | None:
        sel = self.candidates_tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def _update_rel_listbox(self) -> None:
        self.rel_listbox.delete(0, tk.END)
        self._edge_rows.clear()

        for rel, other, type_key in iter_person_edges_view(self.db_session, self.person.id):
            label = f'{_rel_type_label(type_key)}: {_person_short_fio(other)}'
            self.rel_listbox.insert(tk.END, label)
            self._edge_rows.append((rel, other, type_key))

    def _add_relationship(self) -> None:
        related_id = self._selected_candidate_id()
        if related_id is None:
            messagebox.showwarning('Внимание', 'Выберите человека в верхнем списке')
            return

        label_ru = self.rel_type_var.get().strip()
        type_key = RU_LABEL_TO_KEY.get(label_ru)
        if not type_key:
            messagebox.showwarning('Внимание', 'Выберите тип связи из списка')
            return

        related = self.db_session.get(Person, related_id)
        if not related:
            messagebox.showerror('Ошибка', 'Запись не найдена')
            self._reload_candidates()
            return

        if _has_equivalent_relationship(self.db_session, self.person.id, related_id, type_key):
            messagebox.showinfo('Уже есть', 'Такая связь уже учтена (включая обратную запись).')
            return

        self.db_session.add(
            Relationship(
                person_id=self.person.id,
                person_id_related=related_id,
                relationship_type=type_key,
            )
        )
        self.db_session.commit()
        self._update_rel_listbox()

    def _delete_relationship(self) -> None:
        selection = self.rel_listbox.curselection()
        if not selection:
            messagebox.showwarning('Внимание', 'Выберите строку в списке связей')
            return

        idx = selection[0]
        if idx >= len(self._edge_rows):
            return

        rel, other, _type_key = self._edge_rows[idx]
        if not messagebox.askyesno(
            'Подтверждение',
            f'Удалить связь с {other.last_name} {other.first_name}?',
        ):
            return

        self.db_session.delete(rel)
        self.db_session.commit()
        self._update_rel_listbox()


def main() -> None:
    init_db()

    root = tk.Tk()
    app = GenealogyApp(root)
    root.protocol('WM_DELETE_WINDOW', app.on_closing)
    root.mainloop()
