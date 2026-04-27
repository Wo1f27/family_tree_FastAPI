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
    last_name: str
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
            gender_str = 'М' if person.gender == Gender.MALE else \
                'Ж' if person.gender == Gender.FEMALE else 'Другой'

            self.tree.insert('', tk.END, values=(
                person.id,
                person.last_name,
                person.first_name,
                person.middle_name,
                gender_str,
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


    def _add_person(self) -> None:
        dialog = PersonDialog(self.root, 'Добавить человека')
        if dialog.result:
            person = Person(
                first_name=dialog.result.first_name,
                last_name=dialog.result.last_name,
                middle_name=dialog.result.middle_name,
                gender=dialog.result.gender,
                date_of_birth=dialog.result.date_of_birth,
                date_of_death=dialog.result.date_of_death,
                biography=dialog.result.biography
            )
            self._db_session.add(person)
            self._db_session.commit()
            self._load_people()

    def _edit_person(self) -> None:
        person = self._get_selected_person()
        if not person:
            messagebox.showwarning('Внимание', 'Выберите человека для редактирования')
            return

        dialog = PersonDialog(self.root, 'Редактировать', person)
        if dialog.result:
            person.first_name = dialog.result.first_name
            person.last_name = dialog.result.last_name
            person.middle_name = dialog.result.middle_name
            person.gender = dialog.result.gender
            person.date_of_birth = dialog.result.date_of_birth
            person.date_of_death = dialog.result.date_of_death
            person.biography = dialog.result.biography

            self.db_session.commit()
            self._load_people()

    def _delete_person(self):
        person = self._get_selected_person()
        if not person:
            messagebox.showwarning('Внимание', 'Выберите человека для удаления')
            return

        if messagebox.askyesno('Подтверждение',
                               f'Вы действительно хотите удалить {person.last_name} {person.first_name}?'):
            self.db_session.delete(person)
            self.db_session.commit()
            self._load_people()

    def _manage_relationships(self):
        person = self._get_selected_person()
        if not person:
            messagebox.showwarning("Внимание", "Выберите человека")
            return
        dialog = RelationsDialog(self.root, person, self.db_session)
        self._load_people()
        self._show_person_info()

    def _show_person_info(self):
        person = self._get_selected_person()
        if not person:
            self.info_label.config(text="Выберите человека")
            return

        stmt = select(Relationship).where(Relationship.person_id == person.id)
        relationships = self.db_session.execuete(stmt).scalars().all()

        rel_text: list[str] = []
        for rel in relationships:
            stmt = select(Person).where(Person.id == rel.related_person_id)
            related = self.db_session.execute(stmt).scalar_one_or_none()
            if related:
                rel_text.append(
                    f"{rel.relationship_type}: {related.first_name} {related.last_name}"
                )

        info = f"{person.first_name} {person.last_name}\n"
        info += f"Дата рождения: {person.date_of_birth or '-'}\n"
        info += f"Пол: {person.gender}\n"
        if rel_text:
            info += "\nСвязи:\n" + "\n".join(rel_text)

        self.info_label.config(text=info)


class PersonDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, title: str, person: Person) -> None:
        super().__init__(parent)
        self.title = title
        self.person = person
        self.geometry("400x300")
        self.result: PersonData | None = None

        self._create_widgets()

    def _create_widgets(self, person: Person | None) -> None:
        ttk.Label(self, text='Имя: ').pack(pady=5)
        self.first_name_var = tk.StringVar(value=person.first_name if person else '')
        ttk.Entry(self, textvariable=self.first_name_var, width=30).pack()

        ttk.Label(self, text='Отчество: ').pack(pady=5)
        self.middle_name_var = tk.StringVar(value=person.middle_name if person else '')
        ttk.Entry(self, textvariable=self.middle_name_var, width=30).pack()

        ttk.Label(self, text='Фамилия: ').pack(pady=5)
        self.last_name_var = tk.StringVar(value=person.last_name if person else '')
        ttk.Entry(self, textvariable=self.last_name_var, width=30).pack()

        ttk.Label(self, text='Пол: ').pack(pady=5)
        self.gender_var = tk.StringVar(value=person.gender if person else 'MALE')
        gender_combo = ttk.Combobox(
            self, textvariable=self.gender_var,
            values=['male', 'female', 'other'],
            state='readonly',
            width=10
        )
        gender_combo.pack()

        ttk.Label(self, text='Дата рождения: ').pack(pady=5)
        birth_date_str = ''
        if person and person.date_of_birth:
            birth_date_str = person.date_of_birth.strftime('%Y-%m-%d')
        self.birth_date_var = tk.StringVar(value=birth_date_str)
        ttk.Entry(self, textvariable=self.birth_date_var, width=30).pack()

        ttk.Label(self, text='Дата смерти (опционально): ').pack(pady=5)
        death_date_str = ''
        if person and person.date_of_death:
            death_date_str = person.date_of_death.strftime('%Y-%m-%d')
        self.death_date_var = tk.StringVar(value=death_date_str)
        ttk.Entry(self, textvariable=self.death_date_var, width=30).pack()

        ttk.Label(self, text='Биография(опционально): ').pack(pady=5)
        self.biography = tk.StringVar(value=person.biography if person else '')
        ttk.Entry(self, textvariable=self.biography, width=30).pack()

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text='Сохранить', command=self._on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='Отмена', command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _on_save(self) -> None:
        first_name = self.first_name_var
        last_name = self.last_name_var

        if not first_name or not last_name:
            messagebox.showerror("Ошибка", "Необходимо заполнить все поля")

        gender_value = self.gender_var.get()
        gender = Gender(gender_value) if gender_value else None

        date_birth = self._parse_date(self.birth_date_var.get())
        death_date = self._parse_date(self.death_date_var.get())

        self.result = PersonData(
            first_name=first_name,
            last_name=last_name,
            middle_name=self.middle_name_var,
            gender=gender,
            date_of_birth=date_birth,
            date_of_death=death_date,
            biography=self.biography
        )
        self.destroy()

    @classmethod
    def _parse_date(cls, date_str: str) -> date | None:
        if not date_str.strip():
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None


class RelationsDialog(tk.Toplevel):
    def __init__(
            self,
            parent: tk.Tk,
            person: Person,
            session: Session
    ) -> None:
        super().__init__(parent)
        self.title("Управление связями")
        self.geometry("500x400")
        self.person = person
        self.db_session = session

        self._create_widgets()
        self._update_rel_listbox()

    def _create_widgets(self) -> None:
        # Список существующих связей
        ttk.Label(self, text="Существующие связи:").pack(pady=5)

        self.rel_listbox = tk.Listbox(self, height=8, width=60)
        self.rel_listbox.pack(pady=5)

        # Добавить связь
        add_frame = ttk.Frame(self)
        add_frame.pack(pady=10)

        ttk.Label(add_frame, text="Тип:").pack(side=tk.LEFT)
        self.rel_type_var = tk.StringVar(value="spouse")
        ttk.Combobox(
            add_frame,
            textvariable=self.rel_type_var,
            values=["father", "mother", "spouse", "child", "sibling"],
            width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(add_frame, text="ID человека:").pack(side=tk.LEFT)
        self.related_id_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.related_id_var, width=10).pack(side=tk.LEFT, padx=5)

        ttk.Button(add_frame, text="Добавить", command=self._add_relationship).pack(side=tk.LEFT, padx=5)
        ttk.Button(add_frame, text="Удалить", command=self._delete_relationship).pack(side=tk.LEFT, padx=5)

        # Кнопка закрыть
        ttk.Button(self, text="Закрыть", command=self.destroy).pack(pady=10)

    def _update_rel_listbox(self) -> None:
        self.rel_listbox.delete(0, tk.END)

        stmt = select(Relationship).where(Relationship.person_id == self.person.id)
        relationships = self.db_session.execute(stmt).scalars().all()

        for rel in relationships:
            stmt = select(Person).where(Person.id == rel.related_person_id)
            related = self.db_session.execute(stmt).scalar_one_or_none()
            if related:
                self.rel_listbox.insert(
                    tk.END,
                    f"{rel.relationship_type}: {related.first_name} {related.last_name} (ID:{related.id})"
                )

    def _add_relationship(self) -> None:
        try:
            related_id = int(self.related_id_var.get())
            rel_type = self.rel_type_var.get()

            # Проверить что человек существует
            stmt = select(Person).where(Person.id == related_id)
            related = self.db_session.execute(stmt).scalar_one_or_none()

            if not related:
                messagebox.showerror("Ошибка", "Человек с таким ID не найден")
                return

            # Проверить что связь еще нет
            stmt = select(Relationship).where(
                (Relationship.person_id == self.person.id) &
                (Relationship.related_person_id == related_id)
            )
            existing = self.db_session.execute(stmt).scalar_one_or_none()

            if existing:
                messagebox.showerror("Ошибка", "Такая связь уже существует")
                return

            rel = Relationship(
                person_id=self.person.id,
                related_person_id=related_id,
                relationship_type=rel_type
            )
            self.db_session.add(rel)
            self.db_session.commit()
            self._update_rel_listbox()
            self.related_id_var.set("")

        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный ID")

    def _delete_relationship(self) -> None:
        selection = self.rel_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите связь для удаления")
            return

        stmt = select(Relationship).where(Relationship.person_id == self.person.id)
        relationships = self.db_session.execute(stmt).scalars().all()

        if selection[0] < len(relationships):
            rel = relationships[selection[0]]
            self.db_session.delete(rel)
            self.db_session.commit()
            self._update_rel_listbox()


def main() -> None:
    init_db()

    root = tk.Tk()
    app = GenealogyApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

