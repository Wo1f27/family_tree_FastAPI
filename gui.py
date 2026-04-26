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
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('Семейное древо')
        self.root.geometry('1200x800')

        self.db_session = SessionLocal()

    def on_closing(self) -> None:
        self.db_session.close()
        self.root.destroy()



def main() -> None:
    init_db()

    root = tk.Tk()
    app = GenealogyApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

