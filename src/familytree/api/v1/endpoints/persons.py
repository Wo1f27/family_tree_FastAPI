"""REST API endpoints for Person CRUD."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from familytree.api.deps import get_db_session
from familytree.infrastructure.db.repositories.person_repo import PersonRepository
from familytree.schemas.person import PersonCreate, PersonResponse, PersonUpdate

router = APIRouter(prefix="/api/v1/persons", tags=["persons"])


def get_person_repo(db: Session = Depends(get_db_session)) -> PersonRepository:
    return PersonRepository(db)


@router.get("/", response_model=list[PersonResponse])
def list_persons(repo: PersonRepository = Depends(get_person_repo)) -> list[PersonResponse]:
    """Получить список всех персон."""
    return repo.get_all()


@router.get("/{person_id}", response_model=PersonResponse)
def get_person(person_id: int, repo: PersonRepository = Depends(get_person_repo)) -> PersonResponse:
    """Получить персону по ID."""
    person = repo.get_by_id(person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Персона не найдена")
    return person


@router.post("/", response_model=PersonResponse, status_code=201)
def create_person(
    data: PersonCreate,
    repo: PersonRepository = Depends(get_person_repo),
) -> PersonResponse:
    """Создать новую персону."""
    return repo.create(data)


@router.put("/{person_id}", response_model=PersonResponse)
def update_person(
    person_id: int,
    data: PersonUpdate,
    repo: PersonRepository = Depends(get_person_repo),
) -> PersonResponse:
    """Обновить персону."""
    person = repo.update(person_id, data)
    if person is None:
        raise HTTPException(status_code=404, detail="Персона не найдена")
    return person


@router.delete("/{person_id}", status_code=204)
def delete_person(
    person_id: int,
    repo: PersonRepository = Depends(get_person_repo),
) -> None:
    """Удалить персону."""
    if not repo.delete(person_id):
        raise HTTPException(status_code=404, detail="Персона не найдена")
