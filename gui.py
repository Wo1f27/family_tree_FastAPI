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
from models import Address, Gender, Person, Phone, Relationship

UI_SETTINGS_PATH = DATA_DIR / 'ui_settings.json'
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 28
INFO_CONTACT_MAX_LINES = 5


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
    biography: str | None
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
        self.root.geometry('1200x800')
        self.root.minsize(900, 600)

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
        self._info_death = row(4, 'Смерть:')
        self._info_value_labels = (
            self._info_name,
            self._info_middle,
            self._info_gender,
            self._info_birth,
            self._info_death,
        )

        ttk.Label(self._info_grid, text='Телефоны:', anchor=tk.NW).grid(
            row=5, column=0, sticky=tk.NW, pady=(4, 0)
        )
        self._info_phones = tk.Text(
            self._info_grid,
            height=1,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            font=self._font_settings.tk_font(),
        )
        self._info_phones.grid(row=5, column=1, sticky=tk.EW, pady=(4, 0))

        ttk.Label(self._info_grid, text='Адреса:', anchor=tk.NW).grid(
            row=6, column=0, sticky=tk.NW, pady=(4, 0)
        )
        self._info_addresses = tk.Text(
            self._info_grid,
            height=1,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            font=self._font_settings.tk_font(),
        )
        self._info_addresses.grid(row=6, column=1, sticky=tk.EW, pady=(4, 0))

        ttk.Label(self._info_grid, text='Биография:', anchor=tk.NW).grid(
            row=7, column=0, sticky=tk.NW, pady=(4, 0)
        )
        self._info_bio = tk.Text(
            self._info_grid,
            height=3,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            font=self._font_settings.tk_font(),
        )
        self._info_bio.grid(row=7, column=1, sticky=tk.EW, pady=(4, 0))

        ttk.Label(self._info_grid, text='Связи:', anchor=tk.NW).grid(
            row=8, column=0, sticky=tk.NW, pady=(4, 0)
        )
        self._info_rels = tk.Text(
            self._info_grid,
            height=3,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            font=self._font_settings.tk_font(),
        )
        self._info_rels.grid(row=8, column=1, sticky=tk.EW, pady=(4, 0))

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
        rows_h = 5 * line_h
        phone_lines = self._info_phone_line_count
        address_lines = self._info_address_line_count
        text_lines = self._info_text_height_lines()
        text_h = (phone_lines + address_lines + 2 * text_lines) * line_h
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
        for widget in (self._info_bio, self._info_rels):
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
                person.date_of_birth.strftime('%Y-%m-%d') if person.date_of_birth else '-',
                person.date_of_death.strftime('%Y-%m-%d') if person.date_of_death else '-',
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
                biography=dialog.result.biography,
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
            person.biography = dialog.result.biography
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
        self._info_death.config(text='—')
        self._set_info_text_widget(self._info_bio, '')
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
        self._info_birth.config(
            text=person.date_of_birth.strftime('%Y-%m-%d') if person.date_of_birth else '—'
        )
        self._info_death.config(
            text=person.date_of_death.strftime('%Y-%m-%d') if person.date_of_death else '—'
        )
        self._set_info_text_widget(self._info_bio, person.biography or '')
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
        self.geometry('520x280')
        self.minsize(480, 260)
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
        max_h = int(self.winfo_screenheight() * 0.92)
        width = max(460, min(560, self.winfo_reqwidth() + 24))

        if total_h <= max_h:
            self._scroll_visible = False
            self._vscroll.grid_remove()
            self._canvas.configure(height=form_h)
            self.geometry(f'{width}x{total_h}')
            self.minsize(420, min(total_h, max_h))
        else:
            self._scroll_visible = True
            canvas_h = max(280, max_h - btn_h - vertical_pad)
            self._canvas.configure(height=canvas_h)
            self._vscroll.grid(row=0, column=1, sticky=tk.NS)
            self.geometry(f'{width}x{max_h}')
            self.minsize(420, 360)

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

        ttk.Label(form, text='Дата рождения (ГГГГ-ММ-ДД):').pack(anchor=tk.W, pady=(8, 0))
        birth_date_str = person.date_of_birth.strftime('%Y-%m-%d') if person and person.date_of_birth else ''
        self.birth_date_var = tk.StringVar(value=birth_date_str)
        ttk.Entry(form, textvariable=self.birth_date_var, width=40).pack(fill=tk.X)

        ttk.Label(form, text='Дата смерти (опционально):').pack(anchor=tk.W, pady=(8, 0))
        death_date_str = person.date_of_death.strftime('%Y-%m-%d') if person and person.date_of_death else ''
        self.death_date_var = tk.StringVar(value=death_date_str)
        ttk.Entry(form, textvariable=self.death_date_var, width=40).pack(fill=tk.X)

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

        self._btn_frame = ttk.Frame(self)
        self._btn_frame.grid(row=1, column=0, pady=(8, 10))
        ttk.Button(self._btn_frame, text='OK', command=self._on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(self._btn_frame, text='Отмена', command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _on_ok(self) -> None:
        first_name = self.first_name_var.get().strip()
        last_name = self.last_name_var.get().strip()

        if not first_name or not last_name:
            messagebox.showerror('Ошибка', 'Имя и фамилия обязательны')
            return

        birth = self._parse_date(self.birth_date_var.get(), 'дата рождения')
        if birth is False:
            return
        death = self._parse_date(self.death_date_var.get(), 'дата смерти')
        if death is False:
            return

        gender_label = self.gender_var.get().strip()
        gender_key = GENDER_RU_TO_KEY.get(gender_label)
        if not gender_key:
            messagebox.showerror('Ошибка', 'Выберите пол из списка')
            return
        gender = Gender(gender_key)

        self.result = PersonData(
            first_name=first_name,
            last_name=last_name,
            middle_name=self.middle_name_var.get().strip() or None,
            gender=gender,
            date_of_birth=birth,
            date_of_death=death,
            biography=self.biography_text.get('1.0', tk.END).strip() or None,
            phones=self._phones_panel.get_values(),
            addresses=self._addresses_panel.get_values(),
        )
        self.destroy()

    @staticmethod
    def _parse_date(date_str: str, field_label: str) -> date | None | bool:
        """date | None — ок; False — ошибка показана."""
        if not date_str.strip():
            return None
        try:
            return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
        except ValueError:
            messagebox.showerror('Ошибка', f'Некорректная {field_label}. Формат: ГГГГ-ММ-ДД')
            return False


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
        self.geometry('720x560')
        self.minsize(520, 750)
        self.transient(parent)
        self.grab_set()

        self.person = person
        self.db_session = session
        self._font_settings = font_settings or UiFontSettings.load(parent)
        self._edge_rows: list[tuple[Relationship, Person, str]] = []

        self._create_widgets()
        self._reload_candidates()
        self._update_rel_listbox()

        self.protocol('WM_DELETE_WINDOW', self._on_close)

    def _on_close(self) -> None:
        self.grab_release()
        self.destroy()

    def _create_widgets(self) -> None:
        head = ttk.Label(
            self,
            text=f'Связи для: {self.person.last_name} {self.person.first_name}',
            font=('TkDefaultFont', 10, 'bold'),
        )
        head.pack(pady=(10, 4), padx=10, anchor=tk.W)

        lf_pick = ttk.LabelFrame(self, text='1. Выберите человека в списке (мышью)', padding=8)
        lf_pick.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))

        cols = ('Фамилия', 'Имя', 'Отчество')
        self.candidates_tree = ttk.Treeview(
            lf_pick,
            columns=cols,
            show='headings',
            height=10,
            selectmode='browse',
            style=DATA_TREE_STYLE,
        )
        for c, w in zip(cols, (160, 120, 130)):
            self.candidates_tree.heading(c, text=c)
            self.candidates_tree.column(c, width=w)

        cs = ttk.Scrollbar(lf_pick, orient=tk.VERTICAL, command=self.candidates_tree.yview)
        self.candidates_tree.configure(yscrollcommand=cs.set)
        self.candidates_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cs.pack(side=tk.RIGHT, fill=tk.Y)

        self.candidates_tree.bind('<Double-1>', lambda e: self._add_relationship())

        lf_add = ttk.LabelFrame(self, text='2. Тип связи и добавление', padding=8)
        lf_add.pack(fill=tk.X, padx=10, pady=0)

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
        ttk.Label(lf_add, text=hint, wraplength=680, foreground='gray').pack(anchor=tk.W, pady=(6, 0))

        lf_list = ttk.LabelFrame(self, text='3. Все связи (в том числе обратные)', padding=8)
        lf_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=(8, 4))

        self.rel_listbox = tk.Listbox(
            lf_list,
            height=9,
            width=80,
            exportselection=False,
            font=self._font_settings.tk_font(),
        )
        rs = ttk.Scrollbar(lf_list, orient=tk.VERTICAL, command=self.rel_listbox.yview)
        self.rel_listbox.configure(yscrollcommand=rs.set)
        self.rel_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rs.pack(side=tk.RIGHT, fill=tk.Y)

        del_row = ttk.Frame(self)
        del_row.pack(fill=tk.X, padx=10, pady=(0, 6))
        ttk.Button(del_row, text='Удалить выбранную связь', command=self._delete_relationship).pack(
            side=tk.LEFT
        )
        ttk.Label(
            del_row,
            text='Удаляется одна запись в базе (обратная «пропадёт» сама).',
            foreground='gray',
        ).pack(side=tk.LEFT, padx=(12, 0))

        bottom = ttk.Frame(self)
        bottom.pack(fill=tk.X, padx=10, pady=(4, 10))
        ttk.Button(bottom, text='Закрыть', command=self._on_close).pack(side=tk.RIGHT)

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
