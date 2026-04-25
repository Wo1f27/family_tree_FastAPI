# План разработки генеалогического приложения (SQLAlchemy 2.0+)

## Концепция

Простое десктопное приложение для хранения информации о родственниках. Никаких сложных визуализаций — просто карточки людей и связи между ними.

## Технологический стек

- **Python 3.10+** — основной язык с type hints
- **Tkinter** — графический интерфейс (встроен в Python)
- **SQLite** — база данных (тоже встроена в Python)
- **SQLAlchemy 2.0+** — современная ORM

## Структура проекта

```
genealogy_app/
├── main.py              # Точка входа
├── database.py          # Настройка базы данных
├── models.py            # Модели данных
├── gui.py               # Графический интерфейс
└── requirements.txt     # Зависимости
```

## База данных

### Таблица Person

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PRIMARY KEY | Уникальный идентификатор |
| first_name | TEXT | Имя |
| last_name | TEXT | Фамилия |
| birth_date | TEXT | Дата рождения (YYYY-MM-DD) |
| death_date | TEXT | Дата смерти (опционально) |
| gender | TEXT | M/F |
| notes | TEXT | Примечания |

### Таблица Relationship

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PRIMARY KEY | Уникальный идентификатор |
| person_id | INTEGER | ID первого человека |
| related_person_id | INTEGER | ID второго человека |
| relationship_type | TEXT | Тип связи (father, mother, spouse, child, sibling) |

---

## Код

### database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Создаем подключение к SQLite файлу
engine = create_engine(
    'sqlite:///genealogy.db',
    echo=False,
    future=True  # Включает будущие функции SQLAlchemy 2.0
)

# Создаем сессию для работы с БД (используем future=True)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Базовый класс для моделей (SQLAlchemy 2.0 стиль)"""
    pass


def get_db() -> SessionLocal:
    """Получить новую сессию БД (context manager)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Создать таблицы если их нет"""
    Base.metadata.create_all(engine)
```

### models.py

```python
from __future__ import annotations

from datetime import date
from typing import List

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Person(Base):
    """Модель человека в генеалогическом древе"""
    
    __tablename__ = 'person'
    
    # Используем Mapped и mapped_column для SQLAlchemy 2.0
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(nullable=True)
    death_date: Mapped[date | None] = mapped_column(nullable=True)
    gender: Mapped[str] = mapped_column(String(1), default='M')
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Отношения (используем type annotation для SQLAlchemy 2.0)
    relationships: Mapped[List[Relationship]] = relationship(
        back_populates="person",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Person(name='{self.first_name} {self.last_name}', id={self.id})>"


class Relationship(Base):
    """Модель связи между двумя людьми"""
    
    __tablename__ = 'relationship'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey('person.id'), nullable=False)
    related_person_id: Mapped[int] = mapped_column(ForeignKey('person.id'), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Обратная связь
    person: Mapped[Person] = relationship(
        back_populates="relationships",
        foreign_keys=[person_id]
    )
    
    def __repr__(self) -> str:
        return f"<Relationship({self.person_id} -> {self.related_person_id}, type='{self.relationship_type}')>"
```

### gui.py

```python
from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Person, Relationship
from database import SessionLocal, init_db

if TYPE_CHECKING:
    from collections.abc import Generator


@dataclass
class PersonData:
    """Dataclass для передачи данных из диалогов"""
    first_name: str
    last_name: str
    birth_date: date | None
    death_date: date | None
    gender: str
    notes: str | None


class GenealogyApp:
    """Главное окно приложения"""
    
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Genealogy App")
        self.root.geometry("800x600")
        
        self.db_session: Session = SessionLocal()
        
        self._create_widgets()
        self._load_people()
    
    def _create_widgets(self) -> None:
        # Верхняя панель с кнопками
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)
        
        ttk.Button(top_frame, text="Добавить человека", 
                   command=self._add_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Редактировать", 
                   command=self._edit_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Удалить", 
                   command=self._delete_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Связи", 
                   command=self._manage_relationships).pack(side=tk.LEFT, padx=5)
        
        # Таблица людей
        middle_frame = ttk.Frame(self.root, padding=10)
        middle_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('ID', 'Имя', 'Фамилия', 'Дата рождения', 'Пол')
        self.tree = ttk.Treeview(middle_frame, columns=columns, show='headings')
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        self.tree.column('Имя', width=150)
        self.tree.column('Фамилия', width=150)
        self.tree.column('Дата рождения', width=120)
        
        scrollbar = ttk.Scrollbar(middle_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<Double-1>', lambda e: self._edit_person())
        
        # Панель информации о выбранном человеке
        bottom_frame = ttk.LabelFrame(self.root, text="Информация", padding=10)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.info_label = ttk.Label(bottom_frame, text="Выберите человека")
        self.info_label.pack()
    
    def _load_people(self) -> None:
        """Загрузить всех людей из БД"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        stmt = select(Person).order_by(Person.last_name, Person.first_name)
        people = self.db_session.execute(stmt).scalars().all()
        
        for person in people:
            self.tree.insert('', tk.END, values=(
                person.id,
                person.first_name,
                person.last_name,
                person.birth_date.strftime('%Y-%m-%d') if person.birth_date else '-',
                person.gender
            ))
    
    def _get_selected_person(self) -> Person | None:
        """Получить выбранного человека"""
        selected = self.tree.selection()
        if not selected:
            return None
        
        item = self.tree.item(selected[0])
        person_id: int = item['values'][0]
        
        stmt = select(Person).where(Person.id == person_id)
        return self.db_session.execute(stmt).scalar_one_or_none()
    
    def _add_person(self) -> None:
        """Добавить нового человека"""
        dialog = PersonDialog(self.root, "Добавить человека")
        if dialog.result:
            person = Person(
                first_name=dialog.result.first_name,
                last_name=dialog.result.last_name,
                birth_date=dialog.result.birth_date,
                death_date=dialog.result.death_date,
                gender=dialog.result.gender,
                notes=dialog.result.notes
            )
            self.db_session.add(person)
            self.db_session.commit()
            self._load_people()
    
    def _edit_person(self) -> None:
        """Редактировать человека"""
        person = self._get_selected_person()
        if not person:
            messagebox.showwarning("Внимание", "Выберите человека для редактирования")
            return
        
        dialog = PersonDialog(self.root, "Редактировать", person)
        if dialog.result:
            person.first_name = dialog.result.first_name
            person.last_name = dialog.result.last_name
            person.birth_date = dialog.result.birth_date
            person.death_date = dialog.result.death_date
            person.gender = dialog.result.gender
            person.notes = dialog.result.notes
            
            self.db_session.commit()
            self._load_people()
    
    def _delete_person(self) -> None:
        """Удалить человека"""
        person = self._get_selected_person()
        if not person:
            messagebox.showwarning("Внимание", "Выберите человека для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", 
                               f"Удалить {person.first_name} {person.last_name}?"):
            # Удалить все связи через CASCADE
            self.db_session.delete(person)
            self.db_session.commit()
            self._load_people()
    
    def _manage_relationships(self) -> None:
        """Управление связями"""
        person = self._get_selected_person()
        if not person:
            messagebox.showwarning("Внимание", "Выберите человека")
            return
        
        dialog = RelationshipDialog(self.root, person, self.db_session)
        self._load_people()
        self._show_person_info()
    
    def _show_person_info(self) -> None:
        """Показать информацию о выбранном человеке"""
        person = self._get_selected_person()
        if not person:
            self.info_label.config(text="Выберите человека")
            return
        
        stmt = select(Relationship).where(Relationship.person_id == person.id)
        relationships = self.db_session.execute(stmt).scalars().all()
        
        rel_text: list[str] = []
        for rel in relationships:
            stmt = select(Person).where(Person.id == rel.related_person_id)
            related = self.db_session.execute(stmt).scalar_one_or_none()
            if related:
                rel_text.append(
                    f"{rel.relationship_type}: {related.first_name} {related.last_name}"
                )
        
        info = f"{person.first_name} {person.last_name}\n"
        info += f"Дата рождения: {person.birth_date or '-'}\n"
        info += f"Пол: {person.gender}\n"
        if rel_text:
            info += "\nСвязи:\n" + "\n".join(rel_text)
        
        self.info_label.config(text=info)
    
    def on_closing(self) -> None:
        """Закрытие приложения"""
        self.db_session.close()
        self.root.destroy()


class PersonDialog(tk.Toplevel):
    """Диалог добавления/редактирования человека"""
    
    def __init__(self, parent: tk.Tk, title: str, person: Person | None = None) -> None:
        super().__init__(parent)
        self.title(title)
        self.geometry("400x350")
        self.result: PersonData | None = None
        
        self._create_widgets(person)
    
    def _create_widgets(self, person: Person | None) -> None:
        # Поля
        ttk.Label(self, text="Имя:").pack(pady=5)
        self.first_name_var = tk.StringVar(
            value=person.first_name if person else ""
        )
        ttk.Entry(self, textvariable=self.first_name_var, width=30).pack()
        
        ttk.Label(self, text="Фамилия:").pack(pady=5)
        self.last_name_var = tk.StringVar(
            value=person.last_name if person else ""
        )
        ttk.Entry(self, textvariable=self.last_name_var, width=30).pack()
        
        ttk.Label(self, text="Дата рождения (YYYY-MM-DD):").pack(pady=5)
        birth_date_str = ''
        if person and person.birth_date:
            birth_date_str = person.birth_date.strftime('%Y-%m-%d')
        self.birth_date_var = tk.StringVar(value=birth_date_str)
        ttk.Entry(self, textvariable=self.birth_date_var, width=30).pack()
        
        ttk.Label(self, text="Дата смерти (опционально):").pack(pady=5)
        death_date_str = ''
        if person and person.death_date:
            death_date_str = person.death_date.strftime('%Y-%m-%d')
        self.death_date_var = tk.StringVar(value=death_date_str)
        ttk.Entry(self, textvariable=self.death_date_var, width=30).pack()
        
        ttk.Label(self, text="Пол (M/F):").pack(pady=5)
        self.gender_var = tk.StringVar(value=person.gender if person else "M")
        ttk.Entry(self, textvariable=self.gender_var, width=10).pack()
        
        ttk.Label(self, text="Примечания:").pack(pady=5)
        self.notes_var = tk.StringVar(value=person.notes if person else "")
        ttk.Entry(self, textvariable=self.notes_var, width=30).pack()
        
        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=10)
    
    def _on_ok(self) -> None:
        first_name = self.first_name_var.get().strip()
        last_name = self.last_name_var.get().strip()
        
        if not first_name or not last_name:
            messagebox.showerror("Ошибка", "Имя и фамилия обязательны")
            return
        
        # Парсинг дат
        birth_date = self._parse_date(self.birth_date_var.get())
        death_date = self._parse_date(self.death_date_var.get())
        
        self.result = PersonData(
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            death_date=death_date,
            gender=self.gender_var.get().upper() or 'M',
            notes=self.notes_var.get().strip() or None
        )
        self.destroy()
    
    @staticmethod
    def _parse_date(date_str: str) -> date | None:
        """Парсинг даты в формате YYYY-MM-DD"""
        if not date_str.strip():
            return None
        try:
            return date.fromisoformat(date_str.strip())
        except ValueError:
            return None


class RelationshipDialog(tk.Toplevel):
    """Диалог управления связями"""
    
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
    # Инициализировать БД
    init_db()
    
    # Запустить приложение
    root = tk.Tk()
    app = GenealogyApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
```

### main.py

```python
"""Точка входа в приложение"""

from gui import main

if __name__ == "__main__":
    main()
```

### requirements.txt

```
SQLAlchemy>=2.0.0
```

### main.py

```python
from gui import main

if __name__ == "__main__":
    main()
```

### requirements.txt

```
SQLAlchemy>=2.0.0
```

---

## Запуск проекта

```bash
pip install -r requirements.txt
python main.py
```

---

## Ключевые отличия от старого стиля

### 1. Модели данных (SQLAlchemy 2.0)

**Старый стиль:**
```python
class Person(Base):
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100))
```

**Новый стиль:**
```python
class Person(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
```

Используются type hints и `Mapped` для лучшей поддержки IDE и статической типизации.

### 2. Запросы (Core API вместо query())

**Старый стиль:**
```python
people = session.query(Person).filter(Person.id == 1).all()
```

**Новый стиль:**
```python
from sqlalchemy import select

stmt = select(Person).where(Person.id == 1)
people = session.execute(stmt).scalars().all()
```

`select()` — это более явный и предсказуемый API, близкий к SQL.

### 3. Типизация и dataclasses

- Все методы имеют type hints
- `PersonData` — dataclass для передачи данных
- Улучшена подсказка в IDE и проверка типов (mypy/pyright)

### 4. Декораторы и аннотации

- `__future__` аннотации для forward references
- `TYPE_CHECKING` для избежания циклических импортов

---

## Что можно улучшить

1. **Валидация данных** — использовать Pydantic для строгой валидации
2. **Миграции БД** — добавить Alembic для управления схемой
3. **Поиск** — добавить поиск по людям
4. **Экспорт/импорт** — JSON/CSV экспорт данных
5. **Фотографии** — хранить пути к фото
6. **Тесты** — покрыть unit-тестами логику

---

## Итог

Проект использует современные практики SQLAlchemy 2.0+ с type hints, декларативными моделями и явным Core API для запросов. Код готов к развитию и поддерживает статическую типизацию.
