from datetime import datetime
from sqlalchemy.orm import Session

from ..models.person_card import Person, PersonKinship
from ..entities.person_cards import (
    PersonCardBaseSchema,
    PersonCardCreateSchema,
    PersonCardUpdateSchema,
    PersonCardResponseSchema,
    PersonCardWithKinshipResponseSchema,
    KinshipCreateSchema,
    KinshipUpdateSchema
)
from ..repository import person_card


def get_person_card(person_id: int, db: Session) -> dict:
    try:
        person = person_card.get_person_card_by_id(person_id, db)
        if isinstance(person.date_of_birth, datetime):
            person.date_of_birth = person.date_of_birth.isoformat()
        if isinstance(person.date_of_death, datetime):
            person.date_of_death = person.date_of_death.isoformat()
        resp_person = PersonCardResponseSchema.model_validate(person)
        resp_person = resp_person.model_dump()
    except Exception as e:
        return {'success': False, 'detail': f'Ошибка при получении карточки: {e}'}
    return {'success': True, 'detail': 'Карточка персоны', 'person': resp_person}


def create_person_card(person_data: PersonCardCreateSchema, db: Session) -> dict:
    try:
        person = person_card.create_person_card(person_data, db)
        if isinstance(person.date_of_birth, datetime):
            person.date_of_birth = person.date_of_birth.isoformat()
        if isinstance(person.date_of_death, datetime):
            person.date_of_death = person.date_of_death.isoformat()
        resp_person = PersonCardResponseSchema.model_validate(person)
        resp_person = resp_person.model_dump()
    except Exception as e:
        return {'success': False, 'detail': f'Ошибка при создании карточки: {e}'}
    return {'success': True, 'detail': 'Профиль создан успешно', 'person': resp_person}


def update_person_card(person_data: PersonCardUpdateSchema, db: Session) -> dict:
    try:
        person = person_card.update_person_card_by_id(person_data, db)
        if person:
            if isinstance(person.date_of_birth, datetime):
                person.date_of_birth = person.date_of_birth.isoformat()
            if isinstance(person.date_of_death, datetime):
                person.date_of_death = person.date_of_death.isoformat()
            resp_person = PersonCardResponseSchema.model_validate(person)
            resp_person = resp_person.model_dump()
    except Exception as e:
        return {'success': False, 'detail': f'Ошибка при изменении карточки: {e}'}
    return {'success': True, 'detail': 'Ккарточка изменена успешно', 'person': resp_person}


def delete_person_card(person_id: int, db: Session) -> dict:
    try:
        del_person = person_card.delete_person_card_by_id(person_id, db)
        if del_person.get('success'):
            return {'success': True, 'detail': 'Карточка удалена успешно'}
        else:
            return {'success': False, 'detail': 'Ошибка при удалении картчоки'}
    except Exception as e:
        return {'success': False, 'detail': f'Ошибка при удалении картчоки: {e}'}


def add_kinship_to_person(person_data: KinshipCreateSchema, db: Session) -> dict:
    try:
        kinship = person_card.create_kinship(person_data, db)
    except Exception as e:
        return {'success': False, 'detail': f'Ошибка при добавлении связи {e}'}
    return {'success': True, 'detail': 'Связи успешно добавлены'}


def get_person_card_with_kinship(person_id, db: Session) -> dict:
    try:
        person = person_card.get_person_card_with_kinship(person_id, db)
        if isinstance(person.date_of_birth, datetime):
            person.date_of_birth = person.date_of_birth.isoformat()
        if isinstance(person.date_of_death, datetime):
            person.date_of_death = person.date_of_death.isoformat()
        resp_person = PersonCardWithKinshipResponseSchema.model_validate(person)
        resp_person = resp_person.model_dump()
    except Exception as e:
        return {'success': False, 'detail': f'Ошибка при получении карточки: {e}'}
    return {'success': True, 'detail': 'Карточка персоны', 'person': resp_person}