import tkinter as tk
from dataclasses import dataclass
from datetime import date, datetime

from tkinter import ttk, messagebox
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Person, Relationship, Gender
from database import SessionLocal, init_db
from collections.abc import Generator


@dataclass
class PersonData:
    first_name: str
    second_name: str
    middle_name: str | None
    gender: Gender
    date_of_birth: date | None
    date_of_death: date | None
    biography: str | None


class GenealogyApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title('Семейное древо')
        self.root.geometry('1200x800')

        self.db_session = SessionLocal()

        self._create_widgets()
        self._load_people()

    def on_closing(self) -> None:
        self.db_session.close()
        self.root.destroy()

    def _create_widgets(self) -> None:
        """Верхняя панель с кнопками"""
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Button(top_frame, text='Добавить человека', command=self._add_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='Редактировать', command=self._edit_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='Удалить', command=self._delete_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='Связи', command=self._manage_relationships).pack(side=tk.LEFT, padx=5)

        # Таблица людей
        middle_frame = ttk.Frame(self.root, padding=10)
        middle_frame.pack(fill=tk.BOTH, expand=True)
        columns = ('Фамилия', 'Имя',  'Отчество', 'Пол', 'Дата рождения', 'Дата смерти', 'Биография')
        self.tree = ttk.Treeview(middle_frame, columns=columns, show='headings')

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        self.tree.column('Имя', width=120)
        self.tree.column('Фамилия', width=150)
        self.tree.column('Отчество', width=150)

        scrollbar = ttk.Scrollbar(middle_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<Double-1>', lambda e: self._edit_person)

        # Панель информации о выбранном человеке
        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        self.info_label = ttk.Label(bottom_frame, text='Выберите человека', font=('Arial', 12, 'bold'))
        self.info_label.pack()

    def _load_people(self) -> None:
        """Загрузка данных из базы данных"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        stmt = select(Person).order_by(Person.last_name, Person.first_name)
        people = self.db_session.execute(stmt).scalars().all()

        for person in people:
            self.tree.insert('', tk.END, values=(
                person.id,
                person.last_name,
                person.first_name,
                person.middle_name,
                person.gender,
                person.date_of_birth.strftime('%Y-%m-%d') if person.date_of_birth else '-',
                person.date_of_death.strftime('%Y-%m-%d') if person.date_of_death else '-',
                person.biography
            ))

    def _get_selected_person(self) -> Person | None:
        """Возвращает выбранного человека"""
        selected = self.tree.selection()
        if not selected:
            return None

        item = self.tree.item(selected[0])
        person_id: int = item['values'][0]

        stmt = select(Person).filter(Person.id == person_id)
        return self.db_session.execute(stmt).scalar_one_or_none()


    def _add_person(self):
        pass

    def _edit_person(self):
        pass

    def _delete_person(self):
        pass

    def _manage_relationships(self):
        pass




def main() -> None:
    init_db()

    root = tk.Tk()
    app = GenealogyApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

