from sqlalchemy.orm import Session, joinedload

from app.modules.person_card.models.person_card import Person, PersonKinship
from app.enums import enums
from app.modules.person_card.entities.person_cards import (
    PersonCardBaseSchema,
    PersonCardCreateSchema,
    PersonCardUpdateSchema,
    PersonCardResponseSchema,
    PersonCardWithKinshipResponseSchema,
    KinshipCreateSchema,
    KinshipUpdateSchema
)


def get_person_card_by_id(person_id: int, db: Session) -> Person | None:
    person_card = db.query(Person).filter(Person.id == person_id).one_or_none()
    return person_card


def create_person_card(person_data: PersonCardCreateSchema, db: Session) -> Person:
    new_person = Person(
        first_name=person_data.first_name,
        last_name=person_data.last_name,
        patronymic=person_data.patronymic,
        date_of_birth=person_data.date_of_birth,
        date_of_death=person_data.date_of_death,
        gender=person_data.gender,
        avatar=person_data.avatar
    )
    db.add(new_person)
    db.commit()
    db.refresh(new_person)
    return new_person


def update_person_card_by_id(person_data: PersonCardUpdateSchema, db: Session) -> Person | None:
    person_card = get_person_card_by_id(person_data.id, db)
    if not person_card:
        return None
    for key, value in person_data.dict(exclude_unset=True).items():
        setattr(person_card, key, value)
    db.commit()
    db.refresh(person_card)
    return person_card


def delete_person_card_by_id(person_id: int, db: Session) -> dict:
    person_card = get_person_card_by_id(person_id, db)
    if not person_card:
        return {'success': False, 'detail': 'Карточка не найдена'}
    db.delete(person_card)
    db.commit()
    return {'success': True, 'detail': f'Карточка с ID {person_id} удалена'}


def get_person_card_with_kinship(person_id: int, db: Session) -> Person | None:
    person = db.query(Person).options(joinedload(Person.kinship_as_root)).filter(Person.id == person_id).first()
    if person:
        related_persons = []
        for kinship in person.kinship_as_root:
            related_person = db.query(Person).filter(Person.id == kinship.person_id).one_or_none()
            if related_person:
                related_persons.append(related_person)
        person.kinship_persons = related_persons
    return person


def create_kinship(kinship_data: KinshipCreateSchema, db: Session) -> PersonKinship:
    new_kinship = PersonKinship(
        user_id=kinship_data.user_id,
        root_id=kinship_data.root_id,
        person_id=kinship_data.person_id,
        kinship=kinship_data.kinship
    )
    db.add(new_kinship)
    db.commit()
    db.refresh(new_kinship)
    return new_kinship

