"""Page rendering endpoints (Jinja2 templates)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from familytree.api.deps import DBSession
from familytree.core.templates import template_response
from familytree.infrastructure.db.models import Person, Photo

router = APIRouter()


@router.get("/")
def index_page(request: Request, db: DBSession) -> HTMLResponse:
    """Главная страница."""
    from sqlalchemy import select
    from sqlalchemy.exc import OperationalError
    
    stmt = select(Person).order_by(Person.last_name, Person.first_name)
    persons = list(db.scalars(stmt).all())
    
    # Загружаем фото для каждой персоны (если таблица photos существует)
    photos_cache: dict[int, list] = {}
    try:
        for person in persons:
            stmt_photos = select(Photo).where(Photo.person_id == person.id).order_by(Photo.sort_order, Photo.id)
            photos_cache[person.id] = list(db.scalars(stmt_photos).all())
    except OperationalError:
        # Таблица photos ещё не создана
        pass
    
    return template_response("index.html", {"persons": persons, "photos_cache": photos_cache}, request)


@router.get("/surnames")
def surnames_page(request: Request, db: DBSession) -> HTMLResponse:
    """Список фамилий из БД."""
    from sqlalchemy import select
    stmt = select(Person.last_name).distinct().order_by(Person.last_name)
    surnames = list(db.scalars(stmt).all())

    return template_response("surnames.html", {"surnames": surnames}, request)


@router.get("/family/{surname}")
def family_page(surname: str, request: Request, db: DBSession) -> HTMLResponse:
    """Страница семьи по фамилии."""
    from sqlalchemy import select
    from sqlalchemy.exc import OperationalError
    
    stmt = select(Person).where(Person.last_name == surname).order_by(Person.first_name)
    persons = list(db.scalars(stmt).all())

    # Загружаем фото для каждой персоны (если таблица photos существует)
    photos_cache: dict[int, list] = {}
    try:
        for person in persons:
            stmt_photos = select(Photo).where(Photo.person_id == person.id).order_by(Photo.sort_order, Photo.id)
            photos_cache[person.id] = list(db.scalars(stmt_photos).all())
    except OperationalError:
        # Таблица photos ещё не создана
        pass

    return template_response("family.html", {"surname": surname, "persons": persons, "photos_cache": photos_cache}, request)


@router.get("/gallery")
def gallery_page(request: Request, db: DBSession) -> HTMLResponse:
    """Галерея фотографий из БД."""
    from sqlalchemy import select
    from sqlalchemy.exc import OperationalError
    
    try:
        stmt = select(Photo).order_by(Photo.created_at.desc())
        photos = list(db.scalars(stmt).all())
    except OperationalError:
        # Таблица photos ещё не создана
        photos = []

    return template_response("gallery.html", {"photos": photos}, request)


@router.get("/archive")
def archive_page(request: Request, db: DBSession) -> HTMLResponse:
    """Страница документов и архивных записей."""
    from sqlalchemy import select
    stmt = (
        select(Person)
        .where(Person.archive_records.isnot(None))
        .order_by(Person.last_name)
    )
    documents = list(db.scalars(stmt).all())

    return template_response("archive.html", {"documents": documents}, request)


@router.get("/about")
def about_page(request: Request) -> HTMLResponse:
    """Страница «О проекте»."""
    return template_response("about.html", {}, request)
