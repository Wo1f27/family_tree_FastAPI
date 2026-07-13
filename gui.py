from collections.abc import Callable
import json
import tkinter as tk
from dataclasses import dataclass
from datetime import date, datetime
from tkinter import font as tkfont

from tkinter import ttk, messagebox
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from database import DATA_DIR, SessionLocal, init_db
from models import Address, DeathCause, Gender, Person, Phone, Relationship

UI_SETTINGS_PATH = DATA_DIR / 'ui_settings.json'
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 28
INFO_CONTACT_MAX_LINES = 5

# Ограничения размеров окон (подстраиваются под экран пользователя).
WIN_MIN_WIDTH = 360
WIN_MIN_HEIGHT = 240
WIN_MAX_WIDTH_RATIO = 0.96
WIN_MAX_HEIGHT_RATIO = 0.92


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
    """Подогнать размер окна под экран; minsize — мягкий, пользователь может уменьшать."""
    sw, sh = _screen_size(window)
    max_w = max(min_width, int(sw * max_width_ratio))
    max_h = max(min_height, int(sh * max_height_ratio))
    w = max(min_width, min(width, max_w))
    h = max(min_height, min(height, max_h))
    window.minsize(min_width, min_height)
    if center:
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        window.geometry(f'{w}x{h}+{x}+{y}')
    else:
        window.geometry(f'{w}x{h}')
    return w, h


@dataclass
class UiFontSettings:
    family: str
    size: int

    @classmethod
    def defaults(cls, root: tk.Misc) -> 'UiFontSettings':
        actual = tkfont.nametofont('TkDefaultFont').actual(displayof=root)
        return cls(family=actual['family'], size=int(actual['size']))

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
            return cls(family=_resolve_font_family(root, family), size=size)
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


def _resolve_font_family(root: tk.Misc, family: str) -> str:
    available = {name.lower(): name for name in tkfont.families(root)}
    key = family.strip().lower()
    if key in available:
        return available[key]
    return UiFontSettings.defaults(root).family


def _sorted_font_families(root: tk.Misc) -> list[str]:
    return sorted(tkfont.families(root), key=str.casefold)


DATA_TREE_STYLE = 'Data.Treeview'
DATA_LABEL_STYLE = 'Data.TLabel'


def _apply_data_fonts(style: ttk.Style, settings: UiFontSettings) -> None:
    """Шрифт только для данных (таблицы, значения полей), не для кнопок и подписей UI."""
    normal = settings.tk_font()
    rowheight = settings.tree_rowheight()
    style.configure(DATA_TREE_STYLE, font=normal, rowheight=rowheight)
    style.configure(DATA_LABEL_STYLE, font=normal)


@dataclass
class PersonData:
    first_name: str
    last_name: str
    middle_name: str | None
    gender: Gender
    date_of_birth: date | None
    date_of_death: date | None
    place_of_birth: str | None
    place_of_death: str | None
    death_cause: DeathCause | None
    biography: str | None
    archive_records: str | None
    phones: list[str]
    addresses: list[str]


def _load_person_phones(session: Session, person_id: int) -> list[str]:
    stmt = select(Phone.number).where(Phone.person_id == person_id).order_by(Phone.id)
    return list(session.scalars(stmt).all())


def _load_person_addresses(session: Session, person_id: int) -> list[str]:
    stmt = select(Address.address).where(Address.person_id == person_id).order_by(Address.id)
    return list(session.scalars(stmt).all())


def _save_person_contacts(
    session: Session,
    person_id: int,
    phones: list[str],
    addresses: list[str],
) -> None:
    session.execute(delete(Phone).where(Phone.person_id == person_id))
    session.execute(delete(Address).where(Address.person_id == person_id))
    for number in phones:
        session.add(Phone(person_id=person_id, number=number))
    for addr in addresses:
        session.add(Address(person_id=person_id, address=addr))


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


DATE_ENTRY_FMT = '%d-%m-%Y'
DATE_ENTRY_HINT = 'ДД-ММ-ГГГГ'

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


def format_date_display(value: date | None, *, empty: str = '—') -> str:
    if value is None:
        return empty
    return f'{value.day} {MONTH_NAMES_RU_GENITIVE[value.month]} {value.year} г.'


def format_date_entry(value: date | None) -> str:
    if value is None:
        return ''
    return value.strftime(DATE_ENTRY_FMT)


def _mask_date_digits(digits: str) -> str:
    digits = digits[:8]
    if len(digits) <= 2:
        return digits
    if len(digits) <= 4:
        return f'{digits[:2]}-{digits[2:]}'
    return f'{digits[:2]}-{digits[2:4]}-{digits[4:]}'


def _try_parse_date_flexible(value: str) -> date | None:
    text = value.strip()
    if not text:
        return None
    for fmt in ('%d-%m-%Y', '%d.%m.%Y', '%Y-%m-%d', '%Y.%m.%d'):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    digits = ''.join(ch for ch in text if ch.isdigit())
    if len(digits) == 8:
        for fmt in ('%d%m%Y', '%Y%m%d'):
            try:
                return datetime.strptime(digits, fmt).date()
            except ValueError:
                continue
    return None


def parse_date_entry(date_str: str, field_label: str) -> date | None | bool:
    """date | None — ок; False — ошибка показана."""
    if not date_str.strip():
        return None
    parsed = _try_parse_date_flexible(date_str)
    if parsed is None:
        messagebox.showerror('Ошибка', f'Некорректная {field_label}. Формат: {DATE_ENTRY_HINT}')
        return False
    return parsed


class DateMaskEntry(ttk.Entry):
    """Поле даты: ввод цифр, автоматически ДД-ММ-ГГГГ."""

    def __init__(self, parent: tk.Misc, textvariable: tk.StringVar | None = None, **kwargs) -> None:
        self._date_var = textvariable or tk.StringVar()
        super().__init__(parent, textvariable=self._date_var, width=kwargs.pop('width', 14), **kwargs)
        self._updating = False
        self.bind('<KeyRelease>', self._on_key_release)
        self.bind('<FocusOut>', self._on_focus_out)

    def _on_key_release(self, _event: tk.Event) -> None:
        if self._updating:
            return
        raw = self._date_var.get()
        parsed = _try_parse_date_flexible(raw)
        if parsed is not None and len(''.join(ch for ch in raw if ch.isdigit())) >= 8:
            formatted = format_date_entry(parsed)
        else:
            digits = ''.join(ch for ch in raw if ch.isdigit())[:8]
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
        parsed = _try_parse_date_flexible(raw)
        if parsed is None:
            return
        formatted = format_date_entry(parsed)
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
# (у person_id второй — это его отец / мать / ребёнок / супруг / брат или сестра).

REL_LABELS_RU: dict[str, str] = {
    'father': 'Отец',
    'mother': 'Мать',
    'child': 'Ребёнок',
    'spouse': 'Супруг(а)',
    'sibling': 'Брат или сестра',
    'parent': 'Родитель',
}

REL_ORDER_FOR_ADD: tuple[str, ...] = ('father', 'mother', 'child', 'spouse', 'sibling')

REL_COMBO_LABELS: list[str] = [REL_LABELS_RU[k] for k in REL_ORDER_FOR_ADD]
RU_LABEL_TO_KEY: dict[str, str] = {REL_LABELS_RU[k]: k for k in REL_ORDER_FOR_ADD}


def _reverse_relationship_type(stored_type: str) -> str:
    """Для строки, где person_id_related = P: какую роль имеет person_id для P (обратная роль)."""
    t = (stored_type or '').strip().lower()
    return {
        'father': 'child',
        'mother': 'child',
        'child': 'parent',
        'spouse': 'spouse',
        'sibling': 'sibling',
    }.get(t, t)


def _rel_type_label(type_key: str) -> str:
    return REL_LABELS_RU.get((type_key or '').strip().lower(), type_key or '?')


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
            k = _reverse_relationship_type(rel.relationship_type)
            rows.append((rel, other, k))
    rows.sort(
        key=lambda x: (
            x[1].last_name.lower(),
            x[1].first_name.lower(),
            x[0].id,
        )
    )
    return rows


def _has_equivalent_relationship(session: Session, person_id: int, related_id: int, type_key: str) -> bool:
    """Та же семантика, что и при добавлении (в т.ч. обратная запись child↔father/mother)."""
    t = type_key.strip().lower()
    if session.execute(
        select(Relationship).where(
            Relationship.person_id == person_id,
            Relationship.person_id_related == related_id,
            Relationship.relationship_type == t,
        )
    ).scalar_one_or_none():
        return True
    if t in ('father', 'mother'):
        if session.execute(
            select(Relationship).where(
                Relationship.person_id == related_id,
                Relationship.person_id_related == person_id,
                Relationship.relationship_type == 'child',
            )
        ).scalar_one_or_none():
            return True
    if t == 'child':
        if session.execute(
            select(Relationship).where(
                Relationship.person_id == related_id,
                Relationship.person_id_related == person_id,
                Relationship.relationship_type.in_(('father', 'mother')),
            )
        ).scalar_one_or_none():
            return True
    if t in ('spouse', 'sibling'):
        if session.execute(
            select(Relationship).where(
                Relationship.person_id == related_id,
                Relationship.person_id_related == person_id,
                Relationship.relationship_type == t,
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
        _apply_data_fonts(self._style, self._font_settings)

        self._create_widgets()
        self._load_people()
        self._clear_info_panel()

    def on_closing(self) -> None:
        self.db_session.close()
        self.root.destroy()

    def _create_widgets(self) -> None:
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(top_frame, text='Добавить человека', command=self._add_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='Редактировать', command=self._edit_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='Удалить', command=self._delete_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='Связи', command=self._manage_relationships).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='Настройки', command=self._open_settings).pack(side=tk.RIGHT, padx=5)

        self._paned = ttk.Panedwindow(self.root, orient=tk.VERTICAL)
        self._paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        middle_frame = ttk.Frame(self._paned, padding=10)
        self._paned.add(middle_frame, weight=3)

        bottom_outer = ttk.Frame(self._paned, padding=(10, 0, 10, 10))
        self._paned.add(bottom_outer, weight=1)

        info_shell = ttk.LabelFrame(bottom_outer, text='Информация о выбранном человеке', padding=8)
        info_shell.pack(fill=tk.BOTH, expand=True)

        canvas_row = ttk.Frame(info_shell)
        canvas_row.pack(fill=tk.BOTH, expand=True)
        canvas_row.columnconfigure(0, weight=1)
        canvas_row.rowconfigure(0, weight=1)

        self._info_canvas = tk.Canvas(canvas_row, highlightthickness=0, borderwidth=0)
        info_scroll = ttk.Scrollbar(canvas_row, orient=tk.VERTICAL, command=self._info_canvas.yview)
        self._info_canvas.configure(yscrollcommand=info_scroll.set)
        self._info_canvas.grid(row=0, column=0, sticky=tk.NSEW)
        info_scroll.grid(row=0, column=1, sticky=tk.NS)

        self._info_grid = ttk.Frame(self._info_canvas)
        self._info_canvas_window = self._info_canvas.create_window(
            (0, 0), window=self._info_grid, anchor=tk.NW
        )

        def row(r: int, title: str) -> ttk.Label:
            ttk.Label(self._info_grid, text=title, width=14, anchor=tk.W).grid(
                row=r, column=0, sticky=tk.NW, pady=1
            )
            lbl = ttk.Label(self._info_grid, text='—', anchor=tk.W, style=DATA_LABEL_STYLE)
            lbl.grid(row=r, column=1, sticky=tk.EW, pady=1)
            return lbl

        self._info_name = row(0, 'ФИО:')
        self._info_middle = row(1, 'Отчество:')
        self._info_gender = row(2, 'Пол:')
        self._info_birth = row(3, 'Рождение:')
        self._info_birth_place = row(4, 'Место рожд.:')
        self._info_death = row(5, 'Смерть:')
        self._info_death_place = row(6, 'Место смерти:')
        self._info_death_cause = row(7, 'Причина смерти:')
        self._info_value_labels = (
            self._info_name,
            self._info_middle,
            self._info_gender,
            self._info_birth,
            self._info_birth_place,
            self._info_death,
            self._info_death_place,
            self._info_death_cause,
        )

        ttk.Label(self._info_grid, text='Телефоны:', anchor=tk.NW).grid(
            row=8, column=0, sticky=tk.NW, pady=(4, 0)
        )
        self._info_phones = tk.Text(
            self._info_grid,
            height=1,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            font=self._font_settings.tk_font(),
        )
        self._info_phones.grid(row=8, column=1, sticky=tk.EW, pady=(4, 0))

        ttk.Label(self._info_grid, text='Адреса:', anchor=tk.NW).grid(
            row=9, column=0, sticky=tk.NW, pady=(4, 0)
        )
        self._info_addresses = tk.Text(
            self._info_grid,
            height=1,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            font=self._font_settings.tk_font(),
        )
        self._info_addresses.grid(row=9, column=1, sticky=tk.EW, pady=(4, 0))

        ttk.Label(self._info_grid, text='Биография:', anchor=tk.NW).grid(
            row=10, column=0, sticky=tk.NW, pady=(4, 0)
        )
        self._info_bio = tk.Text(
            self._info_grid,
            height=3,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            font=self._font_settings.tk_font(),
        )
        self._info_bio.grid(row=10, column=1, sticky=tk.EW, pady=(4, 0))

        ttk.Label(self._info_grid, text='Архивные записи:', anchor=tk.NW).grid(
            row=11, column=0, sticky=tk.NW, pady=(4, 0)
        )
        self._info_archive = tk.Text(
            self._info_grid,
            height=3,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            font=self._font_settings.tk_font(),
        )
        self._info_archive.grid(row=11, column=1, sticky=tk.EW, pady=(4, 0))

        ttk.Label(self._info_grid, text='Связи:', anchor=tk.NW).grid(
            row=12, column=0, sticky=tk.NW, pady=(4, 0)
        )
        self._info_rels = tk.Text(
            self._info_grid,
            height=3,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            font=self._font_settings.tk_font(),
        )
        self._info_rels.grid(row=12, column=1, sticky=tk.EW, pady=(4, 0))

        self._info_grid.columnconfigure(1, weight=1)

        self._info_phone_line_count = 1
        self._info_address_line_count = 1

        self._info_grid.bind('<Configure>', self._on_info_grid_configure)
        self._info_canvas.bind('<Configure>', self._on_info_canvas_configure)
        self.root.bind('<Configure>', self._on_root_configure, add='+')
        self._info_canvas.bind('<Enter>', self._bind_info_mousewheel)
        self._info_canvas.bind('<Leave>', self._unbind_info_mousewheel)

        columns = ('id', 'Фамилия', 'Имя', 'Отчество', 'Пол', 'Дата рождения', 'Дата смерти', 'Биография')
        self.tree = ttk.Treeview(middle_frame, columns=columns, show='headings', style=DATA_TREE_STYLE)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        self.tree.column('id', width=0, stretch=False)
        self.tree.column('Имя', width=120)
        self.tree.column('Фамилия', width=150)
        self.tree.column('Отчество', width=150)
        self.tree.column('Дата рождения', width=165)
        self.tree.column('Дата смерти', width=165)
        self.tree.column('Биография', width=200)

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
        rows_h = 8 * line_h
        phone_lines = self._info_phone_line_count
        address_lines = self._info_address_line_count
        text_lines = self._info_text_height_lines()
        text_h = (phone_lines + address_lines + 3 * text_lines) * line_h
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
        wrap = max(120, self._info_bio.winfo_width() - 4)
        if wrap <= 1:
            return
        for lbl in self._info_value_labels:
            lbl.configure(wraplength=wrap)

    def _relayout_info_panel(self) -> None:
        text_lines = self._info_text_height_lines()
        font = self._font_settings.tk_font()
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

    def _load_people(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        stmt = select(Person).order_by(Person.last_name, Person.first_name)
        people = self.db_session.execute(stmt).scalars().all()

        for person in people:
            gender_str = _gender_display_raw(person.gender)
            self.tree.insert('', tk.END, values=(
                person.id,
                person.last_name,
                person.first_name,
                person.middle_name or '',
                gender_str,
                format_date_display(person.date_of_birth, empty='-'),
                format_date_display(person.date_of_death, empty='-'),
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
        dialog = PersonDialog(self.root, 'Добавить человека', font_settings=self._font_settings)
        dialog.wait_window()

        if dialog.result:
            person = Person(
                first_name=dialog.result.first_name,
                last_name=dialog.result.last_name,
                middle_name=dialog.result.middle_name,
                gender=dialog.result.gender,
                date_of_birth=dialog.result.date_of_birth,
                date_of_death=dialog.result.date_of_death,
                place_of_birth=dialog.result.place_of_birth,
                place_of_death=dialog.result.place_of_death,
                death_cause=dialog.result.death_cause,
                biography=dialog.result.biography,
                archive_records=dialog.result.archive_records,
            )
            self.db_session.add(person)
            self.db_session.flush()
            _save_person_contacts(
                self.db_session,
                person.id,
                dialog.result.phones,
                dialog.result.addresses,
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
            'Редактировать',
            person,
            font_settings=self._font_settings,
            phones=_load_person_phones(self.db_session, person.id),
            addresses=_load_person_addresses(self.db_session, person.id),
        )
        dialog.wait_window()
        if dialog.result:
            person.first_name = dialog.result.first_name
            person.last_name = dialog.result.last_name
            person.middle_name = dialog.result.middle_name
            person.gender = dialog.result.gender
            person.date_of_birth = dialog.result.date_of_birth
            person.date_of_death = dialog.result.date_of_death
            person.place_of_birth = dialog.result.place_of_birth
            person.place_of_death = dialog.result.place_of_death
            person.death_cause = dialog.result.death_cause
            person.biography = dialog.result.biography
            person.archive_records = dialog.result.archive_records
            _save_person_contacts(
                self.db_session,
                person.id,
                dialog.result.phones,
                dialog.result.addresses,
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
        self._info_middle.config(text='—')
        self._info_gender.config(text='—')
        self._info_birth.config(text='—')
        self._info_birth_place.config(text='—')
        self._info_death.config(text='—')
        self._info_death_place.config(text='—')
        self._info_death_cause.config(text='—')
        self._set_info_text_widget(self._info_bio, '')
        self._set_info_text_widget(self._info_archive, '')
        self._set_info_text_widget(self._info_rels, 'Выберите человека в таблице.')
        self._set_info_text_widget(self._info_phones, '')
        self._set_info_text_widget(self._info_addresses, '')
        self._info_phone_line_count = 1
        self._info_address_line_count = 1
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

        rel_lines: list[str] = []
        for _rel, other, type_key in iter_person_edges_view(self.db_session, person.id):
            rel_lines.append(
                f'{_rel_type_label(type_key)}: {other.last_name} {other.first_name}'
            )

        phones = _load_person_phones(self.db_session, person.id)
        addresses = _load_person_addresses(self.db_session, person.id)
        self._info_phone_line_count = self._info_lines_for_record_count(len(phones))
        self._info_address_line_count = self._info_lines_for_record_count(len(addresses))

        fio = f'{person.last_name} {person.first_name}'.strip()
        self._info_name.config(text=fio)
        self._info_middle.config(text=person.middle_name or '—')
        self._info_gender.config(text=_gender_display_raw(person.gender))
        self._info_birth.config(text=format_date_display(person.date_of_birth))
        self._info_birth_place.config(text=person.place_of_birth or '—')
        self._info_death.config(text=format_date_display(person.date_of_death))
        if person.date_of_death:
            self._info_death_place.config(text=person.place_of_death or '—')
            self._info_death_cause.config(text=_death_cause_display_raw(person.death_cause))
        else:
            self._info_death_place.config(text='—')
            self._info_death_cause.config(text='—')
        self._set_info_text_widget(self._info_bio, person.biography or '')
        self._set_info_text_widget(self._info_archive, person.archive_records or '')
        self._set_info_text_widget(
            self._info_phones,
            '\n'.join(phones) if phones else '—',
        )
        self._set_info_text_widget(
            self._info_addresses,
            '\n'.join(addresses) if addresses else '—',
        )
        self._set_info_text_widget(self._info_rels, '\n'.join(rel_lines) if rel_lines else 'Нет связей.')
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


class PersonDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        title: str,
        person: Person | None = None,
        *,
        font_settings: UiFontSettings | None = None,
        phones: list[str] | None = None,
        addresses: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.result: PersonData | None = None
        self._font_settings = font_settings or UiFontSettings.load(parent)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_widgets(person, phones or [], addresses or [])
        self.after_idle(self._fit_window)

    def _schedule_fit(self) -> None:
        self.after_idle(self._fit_window)

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

    def _fit_window(self) -> None:
        self.update_idletasks()
        form_h = self._form.winfo_reqheight()
        btn_h = self._btn_frame.winfo_reqheight()
        vertical_pad = 42
        total_h = form_h + btn_h + vertical_pad
        _, sh = _screen_size(self)
        max_h = int(sh * WIN_MAX_HEIGHT_RATIO)
        width = max(460, min(560, self.winfo_reqwidth() + 24))

        if total_h <= max_h:
            self._scroll_visible = False
            self._vscroll.grid_remove()
            self._canvas.configure(height=form_h)
            _apply_window_geometry(self, width, total_h, min_width=400, min_height=280)
        else:
            self._scroll_visible = True
            canvas_h = max(200, max_h - btn_h - vertical_pad)
            self._canvas.configure(height=canvas_h)
            self._vscroll.grid(row=0, column=1, sticky=tk.NS)
            _apply_window_geometry(self, width, max_h, min_width=400, min_height=280)

        self._on_form_configure()

    def _create_widgets(
        self,
        person: Person | None,
        phones: list[str],
        addresses: list[str],
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

        ttk.Label(form, text='Имя:').pack(anchor=tk.W)
        self.first_name_var = tk.StringVar(value=person.first_name if person else '')
        ttk.Entry(form, textvariable=self.first_name_var, width=40).pack(fill=tk.X)

        ttk.Label(form, text='Фамилия:').pack(anchor=tk.W, pady=(8, 0))
        self.last_name_var = tk.StringVar(value=person.last_name if person else '')
        ttk.Entry(form, textvariable=self.last_name_var, width=40).pack(fill=tk.X)

        ttk.Label(form, text='Отчество:').pack(anchor=tk.W, pady=(8, 0))
        self.middle_name_var = tk.StringVar(value=person.middle_name or '' if person else '')
        ttk.Entry(form, textvariable=self.middle_name_var, width=40).pack(fill=tk.X)

        ttk.Label(form, text='Пол:').pack(anchor=tk.W, pady=(8, 0))
        if person and person.gender:
            gender_label = _gender_display_raw(person.gender)
        else:
            gender_label = GENDER_LABELS_RU[Gender.MALE.value]
        self.gender_var = tk.StringVar(value=gender_label)
        ttk.Combobox(
            form,
            textvariable=self.gender_var,
            values=GENDER_COMBO_LABELS,
            state='readonly',
            width=12,
        ).pack(anchor=tk.W)

        ttk.Label(form, text=f'Дата рождения ({DATE_ENTRY_HINT}):').pack(anchor=tk.W, pady=(8, 0))
        self.birth_date_var = tk.StringVar(
            value=format_date_entry(person.date_of_birth) if person and person.date_of_birth else ''
        )
        DateMaskEntry(form, textvariable=self.birth_date_var).pack(fill=tk.X)

        ttk.Label(form, text='Место рождения:').pack(anchor=tk.W, pady=(8, 0))
        self.place_of_birth_var = tk.StringVar(value=person.place_of_birth or '' if person else '')
        ttk.Entry(form, textvariable=self.place_of_birth_var, width=40).pack(fill=tk.X)

        ttk.Label(form, text=f'Дата смерти ({DATE_ENTRY_HINT}, опционально):').pack(anchor=tk.W, pady=(8, 0))
        self.death_date_var = tk.StringVar(
            value=format_date_entry(person.date_of_death) if person and person.date_of_death else ''
        )
        self._death_date_entry = DateMaskEntry(form, textvariable=self.death_date_var)
        self._death_date_entry.pack(fill=tk.X)

        self._death_details = ttk.Frame(form)
        ttk.Label(self._death_details, text='Место смерти:').pack(anchor=tk.W)
        self.place_of_death_var = tk.StringVar(value=person.place_of_death or '' if person else '')
        ttk.Entry(self._death_details, textvariable=self.place_of_death_var, width=40).pack(fill=tk.X)

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
        ).pack(anchor=tk.W)

        self._phones_panel = MultiValuePanel(
            form,
            'Телефоны',
            phones,
            font_settings=self._font_settings,
            on_change=self._schedule_fit,
        )
        self._phones_panel.pack(fill=tk.X, pady=(8, 0))

        self._addresses_panel = MultiValuePanel(
            form,
            'Адреса',
            addresses,
            font_settings=self._font_settings,
            on_change=self._schedule_fit,
        )
        self._addresses_panel.pack(fill=tk.X, pady=(4, 0))

        ttk.Label(form, text='Архивные записи:').pack(anchor=tk.W, pady=(8, 0))
        archive_frame = ttk.Frame(form)
        archive_frame.pack(fill=tk.X, pady=(0, 4))
        self.archive_text = tk.Text(
            archive_frame,
            height=3,
            wrap=tk.WORD,
            font=self._font_settings.tk_font(),
        )
        self.archive_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        archive_sb = ttk.Scrollbar(archive_frame, command=self.archive_text.yview)
        archive_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.archive_text.configure(yscrollcommand=archive_sb.set)
        if person and person.archive_records:
            self.archive_text.insert('1.0', person.archive_records)

        ttk.Label(form, text='Биография:').pack(anchor=tk.W, pady=(8, 0))
        bio_frame = ttk.Frame(form)
        bio_frame.pack(fill=tk.X, pady=(0, 4))
        self.biography_text = tk.Text(
            bio_frame,
            height=4,
            wrap=tk.WORD,
            font=self._font_settings.tk_font(),
        )
        self.biography_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
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
        return _try_parse_date_flexible(self.death_date_var.get()) is not None

    def _update_death_details_visibility(self, *_args: object) -> None:
        if self._has_complete_death_date():
            if not self._death_details.winfo_ismapped():
                self._death_details.pack(fill=tk.X, pady=(8, 0), before=self._phones_panel)
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
            death_cause = None
        else:
            place_of_death = self.place_of_death_var.get().strip() or None
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
            gender=gender,
            date_of_birth=birth,
            date_of_death=death,
            place_of_birth=self.place_of_birth_var.get().strip() or None,
            place_of_death=place_of_death,
            death_cause=death_cause,
            biography=self.biography_text.get('1.0', tk.END).strip() or None,
            archive_records=self.archive_text.get('1.0', tk.END).strip() or None,
            phones=self._phones_panel.get_values(),
            addresses=self._addresses_panel.get_values(),
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
            min(720, int(sw * 0.85)),
            min(620, int(sh * 0.82)),
            min_width=480,
            min_height=360,
        )

    def _on_window_configure(self, event: tk.Event) -> None:
        if event.widget is self and hasattr(self, '_hint_label'):
            self._hint_label.configure(wraplength=max(160, event.width - 48))

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
        default_ru = REL_LABELS_RU['spouse']
        self.rel_type_var = tk.StringVar(value=default_ru)
        self.type_combo = ttk.Combobox(
            add_row,
            textvariable=self.rel_type_var,
            values=REL_COMBO_LABELS,
            state='readonly',
            width=22,
        )
        self.type_combo.pack(side=tk.LEFT, padx=(8, 12))
        ttk.Button(add_row, text='Добавить связь', command=self._add_relationship).pack(side=tk.LEFT)

        hint = (
            'Смысл: у человека, для которого открыто окно, выбранный в списке — это '
            '«Отец» / «Мать» / «Ребёнок» / «Супруг(а)» / «Брат или сестра» '
            '(как в поле «Тип»). Двойной клик по строке списка тоже добавляет связь.'
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

        bottom = ttk.Frame(self, padding=(10, 6, 10, 10))
        bottom.grid(row=2, column=0, sticky=tk.EW)
        ttk.Button(bottom, text='Закрыть', command=self._on_close).pack(side=tk.RIGHT)

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
            label = f'{_rel_type_label(type_key)}: {other.last_name} {other.first_name}'
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
