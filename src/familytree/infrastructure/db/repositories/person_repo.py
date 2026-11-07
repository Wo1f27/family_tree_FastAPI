"""Person repository — CRUD operations on Person model."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from familytree.infrastructure.db.models import Person
from familytree.schemas.person import PersonCreate, PersonUpdate


class PersonRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list[Person]:
        stmt = select(Person).order_by(Person.last_name, Person.first_name)
        return list(self.session.scalars(stmt).all())

    def get_by_id(self, person_id: int) -> Person | None:
        return self.session.get(Person, person_id)

    def get_by_surname(self, surname: str) -> list[Person]:
        stmt = (
            select(Person)
            .where(Person.last_name == surname)
            .order_by(Person.first_name)
        )
        return list(self.session.scalars(stmt).all())

    def get_surnames(self) -> list[str]:
        stmt = select(Person.last_name).distinct().order_by(Person.last_name)
        return list(self.session.scalars(stmt).all())

    def search(self, query: str) -> list[Person]:
        pattern = f"%{query}%"
        stmt = (
            select(Person)
            .where(
                Person.last_name.ilike(pattern)
                | Person.first_name.ilike(pattern)
                | Person.middle_name.ilike(pattern)
            )
            .order_by(Person.last_name, Person.first_name)
        )
        return list(self.session.scalars(stmt).all())

    def create(self, data: PersonCreate) -> Person:
        person = Person(**data.model_dump())
        self.session.add(person)
        self.session.commit()
        self.session.refresh(person)
        return person

    def update(self, person_id: int, data: PersonUpdate) -> Person | None:
        person = self.session.get(Person, person_id)
        if person is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(person, field, value)
        self.session.commit()
        self.session.refresh(person)
        return person

    def delete(self, person_id: int) -> bool:
        person = self.session.get(Person, person_id)
        if person is None:
            return False
        self.session.delete(person)
        self.session.commit()
        return True
