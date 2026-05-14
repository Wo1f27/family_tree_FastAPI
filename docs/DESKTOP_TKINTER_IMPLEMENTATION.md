# Desktop приложение на Tkinter

## Структура Desktop модуля

```
desktop/
├── __init__.py
├── main.py                          # Точка входа
├── app.py                           # Основное приложение
├── views/
│   ├── __init__.py
│   ├── login_view.py               # Окно входа
│   ├── register_view.py            # Окно регистрации
│   ├── main_window.py              # Главное окно
│   ├── person_form.py              # Форма персоны
│   └── family_tree_view.py         # Визуализация дерева
├── controllers/
│   ├── __init__.py
│   ├── auth_controller.py          # Контроллер аутентификации
│   ├── person_controller.py        # Контроллер персон
│   └── tree_controller.py          # Контроллер дерева
├── widgets/
│   ├── __init__.py
│   ├── person_card.py              # Карточка персоны
│   └── relationship_editor.py      # Редактор связей
└── utils/
    ├── __init__.py
    └── dialogs.py                  # Вспомогательные диалоги
```

---

## Точка входа

### `desktop/main.py`

```python
import sys
from desktop.app import FamilyTreeApp


def main():
    """Точка входа Desktop приложения"""
    app = FamilyTreeApp()
    app.run()


if __name__ == "__main__":
    sys.exit(main())
```

---

## Основное приложение

### `desktop/app.py`

```python
import tkinter as tk
from sqlalchemy.orm import Session
from core.infrastructure.database.config import get_sync_session, init_db
from desktop.views.main_window import MainWindow


class FamilyTreeApp:
    """Основной класс приложения"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Family Tree")
        self.root.geometry("1200x800")
        
        # Инициализация БД
        init_db()
        
        # Сессия БД (хранится в приложении)
        self.db_session: Session = next(get_sync_session())
        
        # Главное окно
        self.main_window = MainWindow(self.root, self.db_session)
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()
        self.db_session.close()


if __name__ == "__main__":
    app = FamilyTreeApp()
    app.run()
```

---

## Окно входа

### `desktop/views/login_view.py`

```python
import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.orm import Session

from core.infrastructure.database.repositories.sqlite_user_repository import SQLiteUserRepositoryImpl
from core.application.use_cases.user.create_user import CreateUserUseCase
from core.application.dto.user_dto import CreateUserDTO
from core.infrastructure.auth.password_service import verify_password


class LoginView:
    """Окно входа в систему"""

    def __init__(self, parent: tk.Frame, on_login_success, db_session: Session):
        self.parent = parent
        self.on_login_success = on_login_success
        self.db_session = db_session
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        # Заголовок
        title_label = ttk.Label(
            self.parent,
            text="Family Tree - Вход",
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=40)
        
        # Фрейм формы
        form_frame = ttk.Frame(self.parent, padding=20)
        form_frame.pack()
        
        # Email
        ttk.Label(form_frame, text="Email:").grid(row=0, column=0, sticky="w", pady=5)
        self.email_entry = ttk.Entry(form_frame, width=30)
        self.email_entry.grid(row=0, column=1, pady=5, padx=10)
        
        # Пароль
        ttk.Label(form_frame, text="Пароль:").grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(form_frame, show="*", width=30)
        self.password_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Кнопки
        button_frame = ttk.Frame(self.parent, padding=20)
        button_frame.pack()
        
        ttk.Button(
            button_frame,
            text="Войти",
            command=self._on_login
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            button_frame,
            text="Регистрация",
            command=self._on_register
        ).grid(row=0, column=1, padx=5)
    
    def _on_login(self):
        """Обработка входа"""
        email = self.email_entry.get()
        password = self.password_entry.get()
        
        if not email or not password:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        
        try:
            repo = SQLiteUserRepositoryImpl(self.db_session)
            user = repo.get_by_email(email)
            
            if user and verify_password(password, user.password_hash):
                self.on_login_success(user)
            else:
                messagebox.showerror("Ошибка", "Неверный email или пароль")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def _on_register(self):
        """Открытие окна регистрации"""
        from desktop.views.register_view import RegisterView
        register_window = tk.Toplevel(self.parent)
        register_view = RegisterView(register_window, self.db_session, self._on_register_success)
    
    def _on_register_success(self, user):
        """Успешная регистрация"""
        messagebox.showinfo("Успех", f"Пользователь {user.username} создан")
        self.on_login_success(user)
```

---

## Окно регистрации

### `desktop/views/register_view.py`

```python
import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.orm import Session

from core.infrastructure.database.repositories.sqlite_user_repository import SQLiteUserRepositoryImpl
from core.application.use_cases.user.create_user import CreateUserUseCase
from core.application.dto.user_dto import CreateUserDTO


class RegisterView:
    """Окно регистрации"""

    def __init__(self, parent: tk.Toplevel, db_session: Session, on_register_success):
        self.parent = parent
        self.db_session = db_session
        self.on_register_success = on_register_success
        self.parent.title("Регистрация")
        self.parent.geometry("400x300")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        # Email
        ttk.Label(self.parent, text="Email:").grid(row=0, column=0, sticky="w", pady=5, padx=20)
        self.email_entry = ttk.Entry(self.parent, width=30)
        self.email_entry.grid(row=0, column=1, pady=5, padx=10)
        
        # Username
        ttk.Label(self.parent, text="Имя пользователя:").grid(row=1, column=0, sticky="w", pady=5, padx=20)
        self.username_entry = ttk.Entry(self.parent, width=30)
        self.username_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Пароль
        ttk.Label(self.parent, text="Пароль:").grid(row=2, column=0, sticky="w", pady=5, padx=20)
        self.password_entry = ttk.Entry(self.parent, show="*", width=30)
        self.password_entry.grid(row=2, column=1, pady=5, padx=10)
        
        # Подтверждение пароля
        ttk.Label(self.parent, text="Повторите пароль:").grid(row=3, column=0, sticky="w", pady=5, padx=20)
        self.password_confirm_entry = ttk.Entry(self.parent, show="*", width=30)
        self.password_confirm_entry.grid(row=3, column=1, pady=5, padx=10)
        
        # Кнопки
        button_frame = ttk.Frame(self.parent, padding=20)
        button_frame.grid(row=4, column=0, columnspan=2)
        
        ttk.Button(
            button_frame,
            text="Зарегистрироваться",
            command=self._on_register
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            button_frame,
            text="Отмена",
            command=self.parent.destroy
        ).grid(row=0, column=1, padx=5)
    
    def _on_register(self):
        """Обработка регистрации"""
        email = self.email_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        password_confirm = self.password_confirm_entry.get()
        
        if not email or not username or not password:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        
        if password != password_confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return
        
        try:
            repo = SQLiteUserRepositoryImpl(self.db_session)
            use_case = CreateUserUseCase(repo)
            
            dto = CreateUserDTO(
                email=email,
                username=username,
                password=password
            )
            
            user = use_case.execute(dto)
            self.on_register_success(user)
            self.parent.destroy()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
```

---

## Главное окно

### `desktop/views/main_window.py`

```python
import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.orm import Session

from desktop.views.person_form import PersonForm


class MainWindow:
    """Главное окно приложения"""

    def __init__(self, parent: tk.Tk, db_session: Session):
        self.parent = parent
        self.db_session = db_session
        self.current_user = None
        
        self._create_menu()
        self._create_main_layout()
    
    def _create_menu(self):
        """Создание меню"""
        menubar = tk.Menu(self.parent)
        self.parent.config(menu=menubar)
        
        # Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Выход", command=self.parent.quit)
        
        # Персона
        person_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Персона", menu=person_menu)
        person_menu.add_command(label="Добавить персону", command=self._add_person)
        person_menu.add_command(label="Редактировать", command=self._edit_person)
        person_menu.add_separator()
        person_menu.add_command(label="Удалить", command=self._delete_person)
        
        # Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._show_about)
    
    def _create_main_layout(self):
        """Создание основного макета"""
        # Панель инструментов
        toolbar = ttk.Frame(self.parent, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(toolbar, text="Добавить", command=self._add_person).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Редактировать", command=self._edit_person).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Удалить", command=self._delete_person).pack(side=tk.LEFT, padx=2)
        
        # Поиск
        search_frame = ttk.Frame(toolbar, padding=(10, 0, 0, 0))
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.RIGHT)
        self.search_entry = ttk.Entry(search_frame, width=20)
        self.search_entry.pack(side=tk.RIGHT, padx=5)
        self.search_entry.bind("<KeyRelease>", self._on_search)
        
        # Таблица персон
        content_frame = ttk.Frame(self.parent, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("id", "first_name", "last_name", "birth_date", "age")
        self.tree = ttk.Treeview(content_frame, columns=columns, show="headings")
        
        self.tree.heading("#0", text="ФИО")
        self.tree.heading("id", text="ID")
        self.tree.heading("first_name", text="Имя")
        self.tree.heading("last_name", text="Фамилия")
        self.tree.heading("birth_date", text="Дата рождения")
        self.tree.heading("age", text="Возраст")
        
        self.tree.column("#0", width=200)
        self.tree.column("id", width=50)
        self.tree.column("first_name", width=150)
        self.tree.column("last_name", width=150)
        self.tree.column("birth_date", width=120)
        self.tree.column("age", width=60)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.tree.bind("<Double-1>", lambda e: self._edit_person())
        self.tree.bind("<Button-3>", self._show_context_menu)
        
        # Загрузка данных
        self._load_persons()
    
    def _load_persons(self):
        """Загрузка списка персон"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        from core.infrastructure.database.repositories.sqlite_person_repository import SQLitePersonRepositoryImpl
        repo = SQLitePersonRepositoryImpl(self.db_session)
        persons = repo.get_all()
        
        for person in persons:
            self.tree.insert(
                "", tk.END,
                values=(person.id, person.first_name, person.last_name, person.date_of_birth, person.age),
                text=person.full_name
            )
    
    def _add_person(self):
        """Добавление персоны"""
        form = PersonForm(self.parent, self.db_session, on_save=self._on_person_saved)
        form.show()
    
    def _edit_person(self):
        """Редактирование персоны"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите персону")
            return
        
        item = self.tree.item(selection[0])
        person_id = item["values"][0]
        
        from core.infrastructure.database.repositories.sqlite_person_repository import SQLitePersonRepositoryImpl
        repo = SQLitePersonRepositoryImpl(self.db_session)
        person = repo.get_by_id(person_id)
        
        if person:
            form = PersonForm(self.parent, self.db_session, on_save=self._on_person_saved, person=person)
            form.show()
    
    def _delete_person(self):
        """Удаление персоны"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите персону")
            return
        
        if not messagebox.askyesno("Подтверждение", "Удалить эту персону?"):
            return
        
        item = self.tree.item(selection[0])
        person_id = item["values"][0]
        
        from core.infrastructure.database.repositories.sqlite_person_repository import SQLitePersonRepositoryImpl
        repo = SQLitePersonRepositoryImpl(self.db_session)
        
        if repo.delete(person_id):
            self._load_persons()
            messagebox.showinfo("Успех", "Персона удалена")
    
    def _on_person_saved(self):
        """Обработка сохранения персоны"""
        self._load_persons()
    
    def _on_search(self, event):
        """Обработка поиска"""
        query = self.search_entry.get()
        from core.infrastructure.database.repositories.sqlite_person_repository import SQLitePersonRepositoryImpl
        repo = SQLitePersonRepositoryImpl(self.db_session)
        
        # Очистка
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        persons = repo.search(query) if query else repo.get_all()
        
        for person in persons:
            self.tree.insert(
                "", tk.END,
                values=(person.id, person.first_name, person.last_name, person.date_of_birth, person.age),
                text=person.full_name
            )
    
    def _show_context_menu(self, event):
        """Контекстное меню"""
        menu = tk.Menu(self.parent, tearoff=0)
        menu.add_command(label="Редактировать", command=self._edit_person)
        menu.add_command(label="Удалить", command=self._delete_person)
        menu.tk_popup(event.x_root, event.y_root)
    
    def _show_about(self):
        """О программе"""
        messagebox.showinfo("О программе", "Family Tree v1.0\nПриложение для генеалогических деревьев")
```

---

## Форма персоны

### `desktop/views/person_form.py`

```python
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from sqlalchemy.orm import Session
from typing import Optional

from core.domain.entities.person import Person
from core.application.dto.person_dto import CreatePersonDTO


class PersonForm:
    """Форма добавления/редактирования персоны"""

    def __init__(
        self,
        parent: tk.Tk,
        db_session: Session,
        on_save=None,
        person: Optional[Person] = None
    ):
        self.parent = parent
        self.db_session = db_session
        self.on_save = on_save
        self.person = person
        
        self.window = tk.Toplevel(parent)
        self.window.title("Редактирование" if person else "Добавление")
        self.window.geometry("500x600")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        row = 0
        
        # Имя
        ttk.Label(self.window, text="Имя:").grid(row=row, column=0, sticky="w", pady=5, padx=20)
        self.first_name_entry = ttk.Entry(self.window, width=40)
        self.first_name_entry.grid(row=row, column=1, pady=5, padx=10)
        if self.person:
            self.first_name_entry.insert(0, self.person.first_name)
        row += 1
        
        # Фамилия
        ttk.Label(self.window, text="Фамилия:").grid(row=row, column=0, sticky="w", pady=5, padx=20)
        self.last_name_entry = ttk.Entry(self.window, width=40)
        self.last_name_entry.grid(row=row, column=1, pady=5, padx=10)
        if self.person:
            self.last_name_entry.insert(0, self.person.last_name)
        row += 1
        
        # Отчество
        ttk.Label(self.window, text="Отчество:").grid(row=row, column=0, sticky="w", pady=5, padx=20)
        self.middle_name_entry = ttk.Entry(self.window, width=40)
        self.middle_name_entry.grid(row=row, column=1, pady=5, padx=10)
        if self.person and self.person.middle_name:
            self.middle_name_entry.insert(0, self.person.middle_name)
        row += 1
        
        # Дата рождения
        ttk.Label(self.window, text="Дата рождения:").grid(row=row, column=0, sticky="w", pady=5, padx=20)
        self.birth_date_entry = ttk.Entry(self.window, width=40)
        self.birth_date_entry.grid(row=row, column=1, pady=5, padx=10)
        if self.person and self.person.date_of_birth:
            self.birth_date_entry.insert(0, self.person.date_of_birth.strftime("%Y-%m-%d"))
        row += 1
        
        # Дата смерти
        ttk.Label(self.window, text="Дата смерти:").grid(row=row, column=0, sticky="w", pady=5, padx=20)
        self.death_date_entry = ttk.Entry(self.window, width=40)
        self.death_date_entry.grid(row=row, column=1, pady=5, padx=10)
        if self.person and self.person.date_of_death:
            self.death_date_entry.insert(0, self.person.date_of_death.strftime("%Y-%m-%d"))
        row += 1
        
        # Пол
        ttk.Label(self.window, text="Пол:").grid(row=row, column=0, sticky="w", pady=5, padx=20)
        self.gender_var = tk.StringVar(value=self.person.gender if self.person else "")
        gender_combo = ttk.Combobox(self.window, textvariable=self.gender_var, values=["male", "female", "other"], width=37)
        gender_combo.grid(row=row, column=1, pady=5, padx=10)
        row += 1
        
        # Биография
        ttk.Label(self.window, text="Биография:").grid(row=row, column=0, sticky="nw", pady=5, padx=20)
        self.biography_text = tk.Text(self.window, width=40, height=5)
        self.biography_text.grid(row=row, column=1, pady=5, padx=10)
        if self.person and self.person.biography:
            self.biography_text.insert("1.0", self.person.biography)
        row += 1
        
        # Кнопки
        button_frame = ttk.Frame(self.window, padding=20)
        button_frame.grid(row=row, column=0, columnspan=2)
        
        ttk.Button(button_frame, text="Сохранить", command=self._on_save).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.window.destroy).grid(row=0, column=1, padx=5)
    
    def _on_save(self):
        """Обработка сохранения"""
        first_name = self.first_name_entry.get().strip()
        last_name = self.last_name_entry.get().strip()
        middle_name = self.middle_name_entry.get().strip() or None
        birth_date_str = self.birth_date_entry.get().strip()
        death_date_str = self.death_date_entry.get().strip()
        gender = self.gender_var.get() or None
        biography = self.biography_text.get("1.0", tk.END).strip() or None
        
        if not first_name or not last_name:
            messagebox.showerror("Ошибка", "Имя и фамилия обязательны")
            return
        
        # Парсинг дат
        birth_date = None
        death_date = None
        
        if birth_date_str:
            try:
                birth_date = date.fromisoformat(birth_date_str)
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректный формат даты рождения")
                return
        
        if death_date_str:
            try:
                death_date = date.fromisoformat(death_date_str)
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректный формат даты смерти")
                return
        
        try:
            from core.infrastructure.database.repositories.sqlite_person_repository import SQLitePersonRepositoryImpl
            repo = SQLitePersonRepositoryImpl(self.db_session)
            
            if self.person:
                # Обновление
                self.person.first_name = first_name
                self.person.last_name = last_name
                self.person.middle_name = middle_name
                self.person.date_of_birth = birth_date
                self.person.date_of_death = death_date
                self.person.gender = gender
                self.person.biography = biography
                repo.update(self.person)
                messagebox.showinfo("Успех", "Персона обновлена")
            else:
                # Создание
                dto = CreatePersonDTO(
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name,
                    date_of_birth=birth_date,
                    date_of_death=death_date,
                    gender=gender,
                    biography=biography
                )
                
                from core.application.use_cases.person.create_person import CreatePersonUseCase
                use_case = CreatePersonUseCase(repo)
                use_case.execute(dto)
                messagebox.showinfo("Успех", "Персона создана")
            
            self.window.destroy()
            if self.on_save:
                self.on_save()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def show(self):
        """Показать форму"""
        self.window.transient(self.parent)
        self.window.grab_set()
        self.window.focus_set()
        self.parent.wait_window(self.window)
```

---

## Контроллер персон

### `desktop/controllers/person_controller.py`

```python
from typing import List, Optional
from sqlalchemy.orm import Session

from core.domain.entities.person import Person
from core.domain.repositories.person_repository import IPersonRepository
from core.application.dto.person_dto import CreatePersonDTO
from core.application.use_cases.person.create_person import CreatePersonUseCase
from core.application.use_cases.person.get_person import GetPersonUseCase


class PersonController:
    """Контроллер для работы с персонами"""

    def __init__(self, db_session: Session, repo: IPersonRepository):
        self.db_session = db_session
        self.repo = repo
        self.create_use_case = CreatePersonUseCase(repo)
        self.get_use_case = GetPersonUseCase(repo)
    
    def create_person(self, dto: CreatePersonDTO) -> Person:
        return self.create_use_case.execute(dto)
    
    def get_person(self, person_id: int) -> Optional[Person]:
        return self.get_use_case.execute(person_id)
    
    def get_all_persons(self) -> List[Person]:
        return self.repo.get_all()
    
    def search_persons(self, query: str) -> List[Person]:
        return self.repo.search(query)
```

---

## Запуск Desktop приложения

```bash
# Установить зависимости
pip install -r requirements/desktop.txt

# Создать .env
cat > .env << EOF
DB_TYPE=sqlite
SQLITE_DB_DIR=~/Documents
SQLITE_DB_NAME=family_tree.db
SECRET_KEY=your-secret-key-here
EOF

# Запустить
python -m desktop.main
```

---

## Особенности Tkinter реализации

| Преимущество | Описание |
|--------------|----------|
| **Стандартная библиотека** | Не требует дополнительных зависимостей |
| **Кроссплатформенность** | Работает на Windows, macOS, Linux |
| **Простота** | Легко освоить базовый GUI |
| **Лёгкость** | Минимальный размер приложения |

| Ограничение | Решение |
|-------------|---------|
| Не современный вид | Использовать ttk themes (ttkthemes) |
| Ограниченная анимация | Для сложной анимации — PyQt/PySide |
| Меньше виджетов | Расширять собственными компонентами |

---

## Альтернативы Tkinter

Если нужен более современный UI:

1. **PyQt6 / PySide6** — нативные нативные виджеты, мощный GUI
2. **CustomTkinter** — современная тема для Tkinter
3. **Flet** — Flutter для Python (веб-технологии)

Пример с CustomTkinter:

```python
# pip install customtkinter
import customtkinter as ctk

app = ctk.CTk()
app.title("Family Tree")
app.geometry("1200x800")

label = ctk.CTkLabel(app, text="Family Tree", font=("Arial", 24))
label.pack(pady=20)

app.mainloop()
```

---

## Заключение

Tkinter подходит для:
- Быстрого прототипирования
- Внутренних инструментов
- Приложений без сложных визуальных эффектов

Для Family Tree с базовым функционалом Tkinter — отличный выбор благодаря простоте и отсутствию внешних зависимостей.
