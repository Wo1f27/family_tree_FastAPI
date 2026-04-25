# 7. Визуализация дерева — Desktop (Tkinter)

---

### MVP-DESK-01 — Точка входа desktop: main.py, app.py, инициализация БД

```python path=desktop/main.py
import sys
from core.infrastructure.database.config import init_db
from desktop.app import DesktopApp


def main():
    init_db()  # Создать таблицы SQLite
    app = DesktopApp()
    app.run()


if __name__ == "__main__":
    main()
```

```python path=desktop/app.py
import tkinter as tk
from desktop.views.login_view import LoginView


class DesktopApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Family Tree")
        self.root.geometry("1024x768")
        self.current_user = None
        self.current_token = None

    def run(self):
        self.show_login()
        self.root.mainloop()

    def show_login(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        LoginView(self.root, self).pack(fill=tk.BOTH, expand=True)

    def show_main(self):
        from desktop.views.main_view import MainView
        for widget in self.root.winfo_children():
            widget.destroy()
        MainView(self.root, self).pack(fill=tk.BOTH, expand=True)
```

---

### MVP-DESK-02 — Экран входа: форма email + пароль, кнопка «Войти» / «Регистрация»

```python path=desktop/views/login_view.py
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Frame, Label, Entry, Button


class LoginView(Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        Label(self, text="Email").grid(row=0, column=0, padx=5, pady=5)
        self.email_entry = Entry(self, width=30)
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)

        Label(self, text="Пароль").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = Entry(self, show="*", width=30)
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        Button(self, text="Войти", command=self.login).grid(row=2, column=0, pady=10)
        Button(self, text="Регистрация", command=self.show_register).grid(row=2, column=1, pady=10)

    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        if not email or not password:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        try:
            from core.application.dto.auth_dto import LoginDTO
            from core.application.use_cases.user.login_user import LoginUseCase
            from core.infrastructure.database.config import SyncSessionLocal
            from core.infrastructure.database.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository

            db = SyncSessionLocal()
            user_repo = SQLAlchemyUserRepository(db)
            use_case = LoginUseCase(user_repo)
            result = use_case.execute(LoginDTO(email=email, password=password))
            self.app.current_token = result.access_token
            # Получить пользователя
            from core.infrastructure.auth.jwt_service import get_user_id_from_token
            user_id = get_user_id_from_token(result.access_token)
            self.app.current_user = user_repo.get_by_id(user_id)
            db.close()
            self.app.show_main()
        except ValueError as e:
            messagebox.showerror("Ошибка входа", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def show_register(self):
        from desktop.views.register_view import RegisterView
        for widget in self.app.root.winfo_children():
            widget.destroy()
        RegisterView(self.app.root, self.app).pack(fill=tk.BOTH, expand=True)
```

---

### MVP-DESK-03 — Экран регистрации

```python path=desktop/views/register_view.py
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Frame, Label, Entry, Button


class RegisterView(Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        Label(self, text="Username").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = Entry(self, width=30)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        Label(self, text="Email").grid(row=1, column=0, padx=5, pady=5)
        self.email_entry = Entry(self, width=30)
        self.email_entry.grid(row=1, column=1, padx=5, pady=5)

        Label(self, text="Пароль").grid(row=2, column=0, padx=5, pady=5)
        self.password_entry = Entry(self, show="*", width=30)
        self.password_entry.grid(row=2, column=1, padx=5, pady=5)

        Label(self, text="Подтверждение").grid(row=3, column=0, padx=5, pady=5)
        self.confirm_entry = Entry(self, show="*", width=30)
        self.confirm_entry.grid(row=3, column=1, padx=5, pady=5)

        Button(self, text="Зарегистрироваться", command=self.register).grid(row=4, column=0, pady=10)
        Button(self, text="Назад", command=self.back).grid(row=4, column=1, pady=10)

    def register(self):
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        if password != confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return
        try:
            from core.application.dto.user_dto import CreateUserDTO
            from core.application.use_cases.user.create_user import CreateUserUseCase
            from core.infrastructure.database.config import SyncSessionLocal
            from core.infrastructure.database.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository

            db = SyncSessionLocal()
            user_repo = SQLAlchemyUserRepository(db)
            use_case = CreateUserUseCase(user_repo)
            dto = CreateUserDTO(
                username=self.username_entry.get(),
                email=self.email_entry.get(),
                password=password,
            )
            use_case.execute(dto)
            db.close()
            messagebox.showinfo("Успех", "Регистрация успешна! Войдите в аккаунт.")
            self.back()
        except ValueError as e:
            messagebox.showerror("Ошибка регистрации", str(e))

    def back(self):
        self.app.show_login()
```

---

### MVP-DESK-04 — Главное окно: меню, toolbar, таблица персон (Treeview)

```python path=desktop/views/main_view.py
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Frame, Treeview, Button, Menubutton, Menu
from core.application.use_cases.person.get_all_persons import GetAllPersonsUseCase
from core.infrastructure.database.config import SyncSessionLocal
from core.infrastructure.database.repositories.sqlalchemy_person_repository import SQLAlchemyPersonRepository


class MainView(Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # Toolbar
        toolbar = Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        Button(toolbar, text="Добавить персону", command=self.add_person).pack(side=tk.LEFT, padx=2)
        Button(toolbar, text="Редактировать", command=self.edit_person).pack(side=tk.LEFT, padx=2)
        Button(toolbar, text="Удалить", command=self.delete_person).pack(side=tk.LEFT, padx=2)
        Button(toolbar, text="Дерево", command=self.show_tree).pack(side=tk.LEFT, padx=2)
        Button(toolbar, text="Сменить пароль", command=self.change_password).pack(side=tk.LEFT, padx=2)
        Button(toolbar, text="Выход", command=self.logout).pack(side=tk.RIGHT, padx=2)

        # Treeview таблица персон
        columns = ("id", "name", "birth", "death", "gender")
        self.tree = Treeview(self, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="ФИО")
        self.tree.heading("birth", text="Дата рождения")
        self.tree.heading("death", text="Дата смерти")
        self.tree.heading("gender", text="Пол")
        self.tree.column("id", width=50)
        self.tree.column("name", width=250)
        self.tree.column("birth", width=120)
        self.tree.column("death", width=120)
        self.tree.column("gender", width=80)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<Double-1>", lambda e: self.edit_person())
        self.load_persons()

    def load_persons(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        db = SyncSessionLocal()
        try:
            person_repo = SQLAlchemyPersonRepository(db)
            use_case = GetAllPersonsUseCase(person_repo)
            persons = use_case.execute(self.app.current_user.id)
            for p in persons:
                self.tree.insert("", tk.END, values=(
                    p.id, p.full_name,
                    p.date_birth or "", p.date_death or "",
                    p.gender.value if p.gender else "",
                ))
        finally:
            db.close()

    def add_person(self):
        from desktop.views.person_form_view import PersonFormView
        PersonFormView(self.app.root, self.app, person=None, on_save=self.load_persons)

    def edit_person(self):
        selected = self.tree.selection()
        if not selected:
            return
        person_id = int(self.tree.item(selected[0])["values"][0])
        from desktop.views.person_form_view import PersonFormView
        PersonFormView(self.app.root, self.app, person_id=person_id, on_save=self.load_persons)

    def delete_person(self):
        selected = self.tree.selection()
        if not selected:
            return
        person_id = int(self.tree.item(selected[0])["values"][0])
        if not messagebox.askyesno("Удаление", "Удалить персону и все её связи?"):
            return
        try:
            from core.application.use_cases.person.delete_person import DeletePersonUseCase
            from core.infrastructure.database.repositories.sqlalchemy_relationship_repository import SQLAlchemyRelationshipRepository
            db = SyncSessionLocal()
            person_repo = SQLAlchemyPersonRepository(db)
            rel_repo = SQLAlchemyRelationshipRepository(db)
            use_case = DeletePersonUseCase(person_repo, rel_repo)
            use_case.execute(person_id, self.app.current_user.id)
            db.close()
            self.load_persons()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))

    def show_tree(self):
        from desktop.views.tree_canvas import TreeCanvasView
        for widget in self.app.root.winfo_children():
            widget.destroy()
        TreeCanvasView(self.app.root, self.app).pack(fill=tk.BOTH, expand=True)

    def change_password(self):
        from desktop.views.change_password_view import ChangePasswordView
        ChangePasswordView(self.app.root, self.app)

    def logout(self):
        self.app.current_user = None
        self.app.current_token = None
        self.app.show_login()
```

---

### MVP-DESK-05 — Форма персоны: создание/редактирование

```python path=desktop/views/person_form_view.py
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Frame, Label, Entry, Button, Combobox
from core.domain.entities import Gender


class PersonFormView:
    def __init__(self, parent, app, person=None, person_id=None, on_save=None):
        self.app = app
        self.on_save = on_save
        self.person_id = person_id

        self.window = tk.Toplevel(parent)
        self.window.title("Редактирование персоны" if person_id else "Новая персона")
        self.window.geometry("400x500")

        frame = Frame(self.window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        Label(frame, text="Имя").grid(row=0, column=0, sticky=tk.W)
        self.first_name = Entry(frame, width=30)
        self.first_name.grid(row=0, column=1)

        Label(frame, text="Фамилия").grid(row=1, column=0, sticky=tk.W)
        self.last_name = Entry(frame, width=30)
        self.last_name.grid(row=1, column=1)

        Label(frame, text="Отчество").grid(row=2, column=0, sticky=tk.W)
        self.middle_name = Entry(frame, width=30)
        self.middle_name.grid(row=2, column=1)

        Label(frame, text="Дата рождения").grid(row=3, column=0, sticky=tk.W)
        self.date_birth = Entry(frame, width=30)
        self.date_birth.grid(row=3, column=1)

        Label(frame, text="Дата смерти").grid(row=4, column=0, sticky=tk.W)
        self.date_death = Entry(frame, width=30)
        self.date_death.grid(row=4, column=1)

        Label(frame, text="Пол").grid(row=5, column=0, sticky=tk.W)
        self.gender = Combobox(frame, values=["male", "female", "other"], width=27)
        self.gender.grid(row=5, column=1)

        Label(frame, text="Биография").grid(row=6, column=0, sticky=tk.W)
        self.biography = tk.Text(frame, width=30, height=5)
        self.biography.grid(row=6, column=1)

        Button(frame, text="Сохранить", command=self.save).grid(row=7, column=0, columnspan=2, pady=10)

        # Если редактирование — загрузить данные
        if person_id:
            self._load_person(person_id)

    def _load_person(self, person_id):
        from core.application.use_cases.person.get_person import GetPersonUseCase
        from core.infrastructure.database.config import SyncSessionLocal
        from core.infrastructure.database.repositories.sqlalchemy_person_repository import SQLAlchemyPersonRepository
        db = SyncSessionLocal()
        person_repo = SQLAlchemyPersonRepository(db)
        person = GetPersonUseCase(person_repo).execute(person_id, self.app.current_user.id)
        db.close()
        if person:
            self.first_name.insert(0, person.first_name)
            self.last_name.insert(0, person.last_name)
            if person.middle_name:
                self.middle_name.insert(0, person.middle_name)
            if person.date_birth:
                self.date_birth.insert(0, str(person.date_birth))
            if person.date_death:
                self.date_death.insert(0, str(person.date_death))
            if person.gender:
                self.gender.set(person.gender.value)
            if person.biography:
                self.biography.insert("1.0", person.biography)

    def save(self):
        try:
            from core.application.dto.person_dto import CreatePersonDTO, UpdatePersonDTO
            from core.application.use_cases.person.create_person import CreatePersonUseCase
            from core.application.use_cases.person.update_person import UpdatePersonUseCase
            from core.infrastructure.database.config import SyncSessionLocal
            from core.infrastructure.database.repositories.sqlalchemy_person_repository import SQLAlchemyPersonRepository
            from core.infrastructure.database.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository

            db = SyncSessionLocal()
            person_repo = SQLAlchemyPersonRepository(db)
            user_repo = SQLAlchemyUserRepository(db)

            if self.person_id:
                dto = UpdatePersonDTO(
                    id=self.person_id,
                    first_name=self.first_name.get() or None,
                    last_name=self.last_name.get() or None,
                    middle_name=self.middle_name.get() or None,
                    date_birth=self.date_birth.get() or None,
                    date_death=self.date_death.get() or None,
                    gender=self.gender.get() or None,
                    biography=self.biography.get("1.0", tk.END).strip() or None,
                )
                use_case = UpdatePersonUseCase(person_repo)
                use_case.execute(dto, self.app.current_user.id)
            else:
                dto = CreatePersonDTO(
                    first_name=self.first_name.get(),
                    last_name=self.last_name.get(),
                    middle_name=self.middle_name.get() or None,
                    date_birth=self.date_birth.get() or None,
                    date_death=self.date_death.get() or None,
                    gender=self.gender.get() or None,
                    biography=self.biography.get("1.0", tk.END).strip() or None,
                )
                use_case = CreatePersonUseCase(person_repo, user_repo)
                use_case.execute(dto, self.app.current_user.id)

            db.close()
            self.window.destroy()
            if self.on_save:
                self.on_save()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
```

---

### MVP-DESK-06 — Удаление персоны: подтверждение + каскадное удаление связей

Уже реализовано в `MainView.delete_person()` выше (messagebox.askyesno + DeletePersonUseCase).

---

### MVP-DESK-07 — Панель связей: добавление/удаление связей для выбранной персоны

```python path=desktop/views/relationship_panel.py
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Frame, Label, Combobox, Button, Treeview
from core.domain.entities import RelationshipType


class RelationshipPanel(Frame):
    def __init__(self, parent, app, person_id: int):
        super().__init__(parent)
        self.app = app
        self.person_id = person_id

        # Выбор второй персоны
        Label(self, text="Связь с:").grid(row=0, column=0)
        self.person_combo = Combobox(self, width=30)
        self.person_combo.grid(row=0, column=1)
        self._load_persons()

        # Тип связи
        Label(self, text="Тип:").grid(row=1, column=0)
        self.type_combo = Combobox(self, values=[t.value for t in RelationshipType], width=27)
        self.type_combo.grid(row=1, column=1)

        Button(self, text="Добавить связь", command=self.add_relationship).grid(row=2, column=0, columnspan=2, pady=5)

        # Список существующих связей
        self.tree = Treeview(self, columns=("id", "person", "type"), show="headings", height=5)
        self.tree.heading("id", text="ID")
        self.tree.heading("person", text="Персона")
        self.tree.heading("type", text="Тип")
        self.tree.grid(row=3, column=0, columnspan=2, pady=5)

        Button(self, text="Удалить связь", command=self.delete_relationship).grid(row=4, column=0, columnspan=2)
        self.load_relationships()

    def _load_persons(self):
        from core.application.use_cases.person.get_all_persons import GetAllPersonsUseCase
        from core.infrastructure.database.config import SyncSessionLocal
        from core.infrastructure.database.repositories.sqlalchemy_person_repository import SQLAlchemyPersonRepository
        db = SyncSessionLocal()
        person_repo = SQLAlchemyPersonRepository(db)
        persons = GetAllPersonsUseCase(person_repo).execute(self.app.current_user.id)
        db.close()
        self._persons = [p for p in persons if p.id != self.person_id]
        self.person_combo["values"] = [f"{p.id}: {p.full_name}" for p in self._persons]

    def load_relationships(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        from core.application.use_cases.relationship.get_relationships import GetRelationshipsUseCase
        from core.infrastructure.database.config import SyncSessionLocal
        from core.infrastructure.database.repositories.sqlalchemy_relationship_repository import SQLAlchemyRelationshipRepository
        db = SyncSessionLocal()
        rel_repo = SQLAlchemyRelationshipRepository(db)
        rels = GetRelationshipsUseCase(rel_repo).execute(self.person_id)
        db.close()
        for r in rels:
            other_id = r.person_2 if r.person_1 == self.person_id else r.person_1
            self.tree.insert("", tk.END, values=(r.id, other_id, r.relationship_type.value))

    def add_relationship(self):
        selection = self.person_combo.get()
        if not selection:
            messagebox.showerror("Ошибка", "Выберите персону")
            return
        rel_type = self.type_combo.get()
        if not rel_type:
            messagebox.showerror("Ошибка", "Выберите тип связи")
            return
        try:
            other_id = int(selection.split(":")[0])
            from core.application.dto.relationship_dto import CreateRelationshipDTO
            from core.application.use_cases.relationship.create_relationship import CreateRelationshipUseCase
            from core.infrastructure.database.config import SyncSessionLocal
            from core.infrastructure.database.repositories.sqlalchemy_person_repository import SQLAlchemyPersonRepository
            from core.infrastructure.database.repositories.sqlalchemy_relationship_repository import SQLAlchemyRelationshipRepository
            db = SyncSessionLocal()
            person_repo = SQLAlchemyPersonRepository(db)
            rel_repo = SQLAlchemyRelationshipRepository(db)
            dto = CreateRelationshipDTO(person_1=self.person_id, person_2=other_id, relationship_type=rel_type)
            CreateRelationshipUseCase(person_repo, rel_repo).execute(dto, self.app.current_user.id)
            db.close()
            self.load_relationships()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))

    def delete_relationship(self):
        selected = self.tree.selection()
        if not selected:
            return
        rel_id = int(self.tree.item(selected[0])["values"][0])
        try:
            from core.application.use_cases.relationship.delete_relationship import DeleteRelationshipUseCase
            from core.infrastructure.database.config import SyncSessionLocal
            from core.infrastructure.database.repositories.sqlalchemy_person_repository import SQLAlchemyPersonRepository
            from core.infrastructure.database.repositories.sqlalchemy_relationship_repository import SQLAlchemyRelationshipRepository
            db = SyncSessionLocal()
            person_repo = SQLAlchemyPersonRepository(db)
            rel_repo = SQLAlchemyRelationshipRepository(db)
            DeleteRelationshipUseCase(rel_repo, person_repo).execute(rel_id, self.app.current_user.id)
            db.close()
            self.load_relationships()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
```

---

### MVP-DESK-08 — Визуализация дерева на Canvas: отрисовка узлов и связей

```python path=desktop/views/tree_canvas.py
import tkinter as tk
from tkinter.ttk import Frame, Button
from core.application.use_cases.tree.get_tree_data import GetTreeDataUseCase
from core.infrastructure.database.config import SyncSessionLocal
from core.infrastructure.database.repositories.sqlalchemy_person_repository import SQLAlchemyPersonRepository
from core.infrastructure.database.repositories.sqlalchemy_relationship_repository import SQLAlchemyRelationshipRepository


class TreeCanvasView(Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.positions = {}  # person_id → (x, y)
        self.node_ids = {}   # person_id → canvas item id
        self._zoom = 1.0
        self._drag_start = None

        # Toolbar
        toolbar = Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        Button(toolbar, text="← Назад", command=self.back).pack(side=tk.LEFT)
        Button(toolbar, text="Обновить", command=self.render_tree).pack(side=tk.LEFT, padx=5)
        Button(toolbar, text="+ Увеличить", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        Button(toolbar, text="- Уменьшить", command=self.zoom_out).pack(side=tk.LEFT, padx=2)

        # Canvas
        self.canvas = tk.Canvas(self, bg="white", width=900, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Навигация (MVP-DESK-09)
        self.canvas.bind("<MouseWheel>", self.zoom)                     # Windows/macOS
        self.canvas.bind("<Button-4>", self.zoom)                       # Linux scroll up
        self.canvas.bind("<Button-5>", self.zoom)                       # Linux scroll down
        self.canvas.bind("<ButtonPress-2>", self.start_drag)            # Middle mouse
        self.canvas.bind("<B2-Motion>", self.do_drag)
        self.canvas.bind("<ButtonPress-3>", self.start_drag)            # Right mouse (alt)
        self.canvas.bind("<B3-Motion>", self.do_drag)

        # Клик по узлу (MVP-DESK-10)
        self.canvas.bind("<Double-Button-1>", self.on_node_click)

        self.render_tree()

    def render_tree(self):
        self.canvas.delete("all")
        self.positions = {}
        self.node_ids = {}

        db = SyncSessionLocal()
        person_repo = SQLAlchemyPersonRepository(db)
        rel_repo = SQLAlchemyRelationshipRepository(db)
        use_case = GetTreeDataUseCase(person_repo, rel_repo)
        tree_data = use_case.execute(self.app.current_user.id)
        db.close()

        nodes = tree_data["nodes"]
        edges = tree_data["edges"]

        if not nodes:
            self.canvas.create_text(450, 300, text="Нет данных для отображения", font=("Arial", 14))
            return

        # Раскладка по поколениям
        gen_groups = {}
        for n in nodes:
            gen = n["generation"]
            gen_groups.setdefault(gen, []).append(n)

        # Вычислить позиции узлов
        node_width = 160
        node_height = 60
        vertical_gap = 100
        canvas_width = self.canvas.winfo_width() or 900

        for gen, group_nodes in sorted(gen_groups.items()):
            y = 50 + gen * (node_height + vertical_gap)
            total_width = len(group_nodes) * (node_width + 40)
            start_x = max(20, (canvas_width - total_width) // 2)

            for i, n in enumerate(group_nodes):
                x = start_x + i * (node_width + 40)
                self.positions[n["id"]] = (x, y)

                # Цвет узла по полу
                if n["gender"] == "male":
                    fill_color = "#ADD8E6"
                elif n["gender"] == "female":
                    fill_color = "#FFB6C1"
                else:
                    fill_color = "#D3D3D3"

                # Пунктирная рамка для умерших
                outline_dash = (4, 4) if not n["is_alive"] else ()
                outline_color = "#808080" if not n["is_alive"] else "#333"

                # Рисуем узел
                rect = self.canvas.create_rectangle(
                    x, y, x + node_width, y + node_height,
                    fill=fill_color, outline=outline_color, width=2, dash=outline_dash,
                )
                text = self.canvas.create_text(
                    x + node_width // 2, y + node_height // 2,
                    text=n["label"], font=("Arial", 10), width=node_width - 10,
                )
                self.node_ids[n["id"]] = (rect, text)

        # Рисуем связи
        for e in edges:
            from_pos = self.positions.get(e["from"])
            to_pos = self.positions.get(e["to"])
            if not from_pos or not to_pos:
                continue

            x1 = from_pos[0] + node_width // 2
            y1 = from_pos[1] + node_height
            x2 = to_pos[0] + node_width // 2
            y2 = to_pos[1]

            # Стиль линии по типу связи
            if e["type"] == "spouse":
                line_color = "#e91e63"
                line_dash = ()
            elif e["type"] == "sibling":
                line_color = "#666"
                line_dash = (6, 3)
            else:
                line_color = "#666"
                line_dash = ()

            # Стрелка для родительских связей
            arrow = tk.LAST if e["type"] == "parent" else None

            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=line_color, width=2, dash=line_dash, arrow=arrow,
            )

    # --- Навигация (MVP-DESK-09) ---

    def zoom(self, event):
        """Зум колёсиком мыши"""
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self._zoom *= 1.1
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            self._zoom /= 1.1
        self._zoom = max(0.3, min(3.0, self._zoom))
        self.canvas.scale("all", event.x, event.y, self._zoom, self._zoom)

    def zoom_in(self):
        """Кнопка увеличения"""
        self._zoom *= 1.2
        self._zoom = min(3.0, self._zoom)
        cx = self.canvas.winfo_width() // 2
        cy = self.canvas.winfo_height() // 2
        self.canvas.scale("all", cx, cy, 1.2, 1.2)

    def zoom_out(self):
        """Кнопка уменьшения"""
        self._zoom /= 1.2
        self._zoom = max(0.3, self._zoom)
        cx = self.canvas.winfo_width() // 2
        cy = self.canvas.winfo_height() // 2
        self.canvas.scale("all", cx, cy, 1 / 1.2, 1 / 1.2)

    def start_drag(self, event):
        """Начало перетаскивания холста"""
        self._drag_start = (event.x, event.y)

    def do_drag(self, event):
        """Перетаскивание холста"""
        if self._drag_start:
            dx = event.x - self._drag_start[0]
            dy = event.y - self._drag_start[1]
            self.canvas.move("all", dx, dy)
            self._drag_start = (event.x, event.y)

    # --- Клик по узлу (MVP-DESK-10) ---

    def on_node_click(self, event):
        """Двойной клик по узлу → карточка персоны"""
        # Найти узел под курсором
        clicked_items = self.canvas.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)

        # Определить person_id по кликнутому прямоугольнику
        for person_id, (rect, text) in self.node_ids.items():
            if rect in clicked_items or text in clicked_items:
                self._show_person_detail(person_id)
                return

    def _show_person_detail(self, person_id):
        """Показать карточку персоны"""
        from core.application.use_cases.person.get_person import GetPersonUseCase
        from core.infrastructure.database.config import SyncSessionLocal
        from core.infrastructure.database.repositories.sqlalchemy_person_repository import SQLAlchemyPersonRepository

        db = SyncSessionLocal()
        person_repo = SQLAlchemyPersonRepository(db)
        person = GetPersonUseCase(person_repo).execute(person_id, self.app.current_user.id)
        db.close()

        if not person:
            return

        # Модальное окно с данными персоны
        detail = tk.Toplevel(self.app.root)
        detail.title(person.full_name)
        detail.geometry("350x300")

        tk.Label(detail, text=person.full_name, font=("Arial", 14, "bold")).pack(pady=10)

        info_frame = tk.Frame(detail)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        row = 0
        if person.date_birth:
            tk.Label(info_frame, text="Дата рождения:").grid(row=row, column=0, sticky=tk.W)
            tk.Label(info_frame, text=str(person.date_birth)).grid(row=row, column=1, sticky=tk.W)
            row += 1
        if person.date_death:
            tk.Label(info_frame, text="Дата смерти:").grid(row=row, column=0, sticky=tk.W)
            tk.Label(info_frame, text=str(person.date_death)).grid(row=row, column=1, sticky=tk.W)
            row += 1
        if person.gender:
            tk.Label(info_frame, text="Пол:").grid(row=row, column=0, sticky=tk.W)
            gender_label = {"male": "Мужской", "female": "Женский", "other": "Другой"}.get(
                person.gender.value, person.gender.value
            )
            tk.Label(info_frame, text=gender_label).grid(row=row, column=1, sticky=tk.W)
            row += 1
        if person.biography:
            tk.Label(info_frame, text="Биография:").grid(row=row, column=0, sticky=tk.NW)
            bio_text = tk.Text(info_frame, width=30, height=5, wrap=tk.WORD)
            bio_text.insert("1.0", person.biography)
            bio_text.config(state=tk.DISABLED)
            bio_text.grid(row=row, column=1, sticky=tk.W)

        tk.Button(detail, text="Закрыть", command=detail.destroy).pack(pady=10)

    def back(self):
        """Вернуться к главному экрану"""
        self.app.show_main()
```

---

### MVP-DESK-09 — Навигация: зум, перетаскивание холста

Уже реализовано в `TreeCanvasView` выше:
- Зум колёсиком мыши (`<MouseWheel>`, `<Button-4>`, `<Button-5>`) + кнопки «+» / «−»
- Перетаскивание средней/правой кнопкой мыши (`<ButtonPress-2>`, `<B2-Motion>`, `<ButtonPress-3>`, `<B3-Motion>`)

---

### MVP-DESK-10 — Клик по узлу → карточка персоны

Уже реализовано в `TreeCanvasView` выше:
- Двойной клик левой кнопкой (`<Double-Button-1>`) → `_show_person_detail()`
- Модальное окно `Toplevel` с ФИО, датами, полом, биографией
