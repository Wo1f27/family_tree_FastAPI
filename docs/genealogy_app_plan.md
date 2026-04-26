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
)

# Создаем сессию для работы с БД
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Базовый класс для моделей (SQLAlchemy 2.0 стиль)"""
    pass


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
import threading
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

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
requests>=2.31.0
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

---

## Система автообновления через GitHub Releases

### Архитектура обновления

Приложение проверяет наличие новых версий при запуске и предлагает пользователю обновиться.

**Ключевое правило:** База данных и пользовательские файлы **никогда** не удаляются при обновлении.

### 1. Структура проекта для обновлений

```
genealogy_app/
├── app/                          # Папка приложения (удаляется при переустановке)
│   ├── main.py
│   ├── gui.py
│   ├── database.py
│   ├── models.py
│   ├── config.py                 # Конфиг с путями и версией
│   ├── updater.py                # Модуль автообновления
│   └── version.txt               # Текущая версия (например, "1.0.0")
├── data/                         # Папка данных (сохраняется при обновлениях)
│   └── genealogy.db              # База данных пользователя
├── dist/                         # Папка для сборки установщика
│   └── genealogy_app_setup.exe
├── setup.iss                     # Конфигурация Inno Setup
└── requirements.txt
```

### 2. Конфигурация путей (config.py)

```python
"""Конфигурация приложения и путей"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def get_app_dir() -> Path:
    """
    Папка с программными файлами.
    При обновлении эта папка удаляется и создаётся заново.
    """
    if getattr(sys, 'frozen', False):
        # Запуск скомпилированного .exe
        return Path(sys.executable).parent
    # Запуск из исходного кода
    return Path(__file__).parent


def get_data_dir() -> Path:
    """
    Папка с данными пользователя.
    Сохраняется между обновлениями.
    """
    if os.name == 'nt':  # Windows
        data_path = Path(os.environ['APPDATA']) / 'GenealogyApp'
    else:  # Linux/macOS
        data_path = Path.home() / '.local' / 'share' / 'GenealogyApp'
    
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


def get_db_path() -> Path:
    """Путь к базе данных"""
    return get_data_dir() / 'genealogy.db'


def get_version() -> str:
    """Получить текущую версию приложения"""
    version_file = get_app_dir() / 'version.txt'
    if version_file.exists():
        return version_file.read_text().strip()
    return '0.0.0'


# GitHub репозиторий для обновлений
GITHUB_REPO = 'your-username/genealogy-app'  # Заменить на свой репозиторий
```

### 3. Модуль обновления (updater.py)

```python
"""Модуль автообновления через GitHub Releases"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

from config import GITHUB_REPO, get_app_dir, get_data_dir, get_version


class Updater:
    """Класс для управления обновлениями"""
    
    def __init__(self) -> None:
        self.current_version = get_version()
        self.app_dir = get_app_dir()
        self.data_dir = get_data_dir()
    
    def check_for_update(self) -> dict | None:
        """
        Проверить наличие новой версии на GitHub.
        
        Возвращает dict с информацией об обновлении или None.
        """
        api_url = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
        
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()
            
            latest_version = release_data['tag_name'].lstrip('v')
            
            # Сравнить версии (простая версия сравнения)
            if self._compare_versions(latest_version, self.current_version) > 0:
                # Найти ассет для текущей платформы
                asset = self._find_asset_for_platform(release_data['assets'])
                if asset:
                    return {
                        'version': latest_version,
                        'name': release_data['name'],
                        'body': release_data['body'],  # Примечания к релизу
                        'download_url': asset['browser_download_url'],
                        'published_at': release_data['published_at']
                    }
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f'Ошибка проверки обновления: {e}')
        
        return None
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        Сравнить две версии (SemVer).
        
        Возвращает:
            1 если v1 > v2
           -1 если v1 < v2
            0 если v1 == v2
        """
        def normalize(v: str) -> list[int]:
            return [int(x) for x in v.split('.')[:3]]  # MAJOR.MINOR.PATCH
        
        n1, n2 = normalize(v1), normalize(v2)
        
        for a, b in zip(n1, n2):
            if a > b:
                return 1
            if a < b:
                return -1
        
        return 0
    
    def _find_asset_for_platform(self, assets: list[dict]) -> dict | None:
        """Найти ассет для текущей операционной системы"""
        system = platform.system().lower()
        arch = platform.machine().lower()
        
        # Приоритет поиска ассетов
        if system == 'windows':
            if 'amd64' in arch or 'x86_64' in arch:
                patterns = ['_windows_x64.exe', '_win64.exe', '_setup.exe']
            else:
                patterns = ['_windows_x86.exe', '_win32.exe']
        elif system == 'linux':
            patterns = ['_linux_x64.deb', '_linux_x64.rpm', '_linux.tar.gz']
        elif system == 'darwin':
            patterns = ['_macos.dmg', '_macos.tar.gz']
        else:
            patterns = []
        
        for asset in assets:
            name = asset['name'].lower()
            for pattern in patterns:
                if pattern in name:
                    return asset
        
        return assets[0] if assets else None  #Fallback на первый ассет
    
    def download_update(self, download_url: str) -> Path:
        """Скачать обновление во временную папку"""
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        temp_dir = Path(tempfile.gettempdir())
        installer_path = temp_dir / 'genealogy_update.exe'
        
        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return installer_path
    
    def apply_update(self, installer_path: Path) -> None:
        """
        Запустить установщик для обновления.
        
        Текущее приложение закроется, установщик запустится с правами администратора.
        """
        # Создаём скрипт для перезапуска после установки
        restart_script = self.app_dir / 'restart_after_update.bat'
        
        script_content = f'''
@echo off
timeout /t 3 /nobreak >nul
start "" "{installer_path}" /SILENT /SUPPRESSMSGBOXES
timeout /t 5 /nobreak >nul
del "%~f0"
        '''
        
        restart_script.write_text(script_content)
        
        # Запускаем скрипт и закрываем приложение
        subprocess.Popen(['cmd', '/c', str(restart_script)], 
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        sys.exit(0)
    
    def update_and_restart(self) -> None:
        """Полный цикл обновления"""
        update_info = self.check_for_update()
        
        if not update_info:
            print('Нет доступных обновлений')
            return
        
        print(f'Найдена новая версия: {update_info["version"]}')
        
        # Скачать
        installer_path = self.download_update(update_info['download_url'])
        print(f'Обновление скачано: {installer_path}')
        
        # Применить
        self.apply_update(installer_path)


def create_backup() -> Path:
    """Создать бэкап базы данных перед обновлением"""
    db_path = get_data_dir() / 'genealogy.db'
    backup_dir = get_data_dir() / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = Path(db_path).stat().st_mtime
    backup_name = f'genealogy_backup_{timestamp}.db'
    backup_path = backup_dir / backup_name
    
    shutil.copy2(db_path, backup_path)
    print(f'Бэкап создан: {backup_path}')
    
    return backup_path
```

### 4. Интеграция в GUI (gui.py)

Добавить кнопку "Проверить обновления" и проверку при запуске:

```python
from updater import Updater, create_backup
import threading

class GenealogyApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        # ... существующий код ...
        
        # Проверить обновление в фоновом потоке
        self._check_update_background()
    
    def _check_update_background(self) -> None:
        """Проверить обновление в отдельном потоке"""
        def check() -> None:
            updater = Updater()
            update_info = updater.check_for_update()
            
            # Вернуться в UI поток для показа сообщения
            self.root.after(0, lambda: self._show_update_notification(update_info))
        
        thread = threading.Thread(target=check, daemon=True)
        thread.start()
    
    def _show_update_notification(self, update_info: dict | None) -> None:
        """Показать уведомление об обновлении"""
        if update_info:
            result = messagebox.askyesno(
                'Доступно обновление',
                f'Найдена новая версия: {update_info["version"]}\n\n'
                f'{update_info["name"]}\n\n'
                f'Установить сейчас?'
            )
            
            if result:
                # Бэкап перед обновлением
                create_backup()
                
                # Запустить обновление
                updater = Updater()
                updater.update_and_restart()
        else:
            print('Приложение актуально')
    
    def _check_updates_manual(self) -> None:
        """Ручная проверка обновлений (для кнопки в меню)"""
        self._check_update_background()
```

### 5. Добавление кнопки в интерфейс

```python
def _create_widgets(self) -> None:
    # Верхняя панель с кнопками
    top_frame = ttk.Frame(self.root, padding=10)
    top_frame.pack(fill=tk.X)
    
    ttk.Button(top_frame, text="Добавить человека", command=self._add_person).pack(side=tk.LEFT, padx=5)
    ttk.Button(top_frame, text="Редактировать", command=self._edit_person).pack(side=tk.LEFT, padx=5)
    ttk.Button(top_frame, text="Удалить", command=self._delete_person).pack(side=tk.LEFT, padx=5)
    ttk.Button(top_frame, text="Связи", command=self._manage_relationships).pack(side=tk.LEFT, padx=5)
    
    # Кнопка проверки обновлений (справа)
    ttk.Button(top_frame, text="Проверить обновления", 
               command=self._check_updates_manual).pack(side=tk.RIGHT, padx=5)
    
    # ... остальной код ...
```

### 6. Создание установщика (Inno Setup)

Файл `setup.iss`:

```ini
; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING .ISS SCRIPT FILES!

#define MyAppName "Genealogy App"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Name"
#define MyAppExeName "main.exe"

[Setup]
AppId={{YOUR-GUID-HERE}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=dist
OutputBaseFilename=genealogy_app_setup_{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

; НЕ удаляем папку с данными при деинсталляции
; Uninstallable=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\\Russian.isl"

[Files]
Source: "app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
```

### 7. GitHub Actions для автоматического создания релизов

Файл `.github/workflows/build.yml`:

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'  # Триггер на теги типа v1.0.0

jobs:
  build-windows:
    runs-on: windows-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller requests
      
      - name: Build executable
        run: |
          pyinstaller --onefile --windowed --name main --icon=icon.ico main.py
      
      - name: Create installer (Inno Setup)
        uses: Minionguyjpro/Inno-Setup-Action@v1.2.2
        with:
          path: setup.iss
      
      - name: Create release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            dist/*.exe
          generate_release_notes: true
```

### 8. Процесс выпуска обновления

1. **Изменить версию** в `app/version.txt`:
   ```
   1.0.0  →  1.1.0
   ```

2. **Создать тег и пушить**:
   ```bash
   git add app/version.txt
   git commit -m "Release v1.1.0"
   git tag v1.1.0
   git push origin main --tags
   ```

3. **GitHub Actions автоматически**:
   - Скомпилирует `.exe`
   - Создаст установщик
   - Опубликует релиз на GitHub

4. **Пользователи получат уведомление** при следующем запуске приложения

---

## Важные замечания

### Защита данных при обновлении

| Что сохраняется | Что удаляется |
|-----------------|---------------|
| `%APPDATA%\GenealogyApp\genealogy.db` | `%PROGRAMFILES%\GenealogyApp\` (папка программы) |
| `%APPDATA%\GenealogyApp\backups\` | Временные файлы приложения |
| Настройки пользователя | Кэш и логи |

### Рекомендации

1. **Всегда создавать бэкап** перед обновлением
2. **Использовать SemVer** (MAJOR.MINOR.PATCH) для версий
3. **Тестировать обновление** на тестовой машине перед релизом
4. **Хранить миграции БД** через Alembic для изменения схемы данных
5. **Добавить откат** — возможность вернуть старую версию

### Безопасность

- Подписывать релизы цифровым сертификатом (для Windows)
- Проверять целостность скачанного файла (хеш-сумма)
- Использовать HTTPS для GitHub API
- Не хранить токены/секреты в коде

---

## Исправления для Python 3.12-3.13

### Что было исправлено

| Проблема | Было | Стало |
|----------|------|-------|
| Дублирование импорта | `import tkinter as tk` дважды | Один импорт |
| Устаревший параметр | `future=True` в `create_engine()` | Удалено (не нужно в SQLAlchemy 2.0+) |
| Некорректный тип возвращаемого | `def get_db() -> SessionLocal:` с `yield` | Удалена функция `get_db()` (не использовалась) |
| Дублирование файлов | `main.py` и `requirements.txt` дважды | Оставлен один экземпляр |
| Missing dependency | Только `SQLAlchemy` | Добавлен `requests>=2.31.0` для updater |

### Совместимость с Python 3.12-3.13

```python
# ✅ Работает в Python 3.10+
from __future__ import annotations  # Для forward references

# ✅ Union types (Python 3.10+)
birth_date: Mapped[date | None]
result: PersonData | None

# ✅ Встроенные типы в аннотациях (Python 3.9+)
rel_text: list[str]
normalize(v: str) -> list[int]

# ✅ TYPE_CHECKING для тяжёлых импортов
if TYPE_CHECKING:
    from collections.abc import Generator
```

### Рекомендации для Python 3.13

1. **Python 3.13** сохраняет совместимость с `|` для union types
2. **SQLAlchemy 2.0.25+** рекомендуется для полной совместимости
3. **mypy 1.8+** лучше поддерживает Python 3.12-3.13
4. **Pydantic V2** для валидации данных (опционально)

### Минимальные версии зависимостей

```txt
# requirements.txt
SQLAlchemy>=2.0.25      # Полная поддержка Python 3.12+
requests>=2.31.0        # Безопасность и совместимость
```

