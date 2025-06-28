from datetime import datetime
from sqlalchemy.orm import Session

from ..models.person_card import  Person, PersonKinship
from ..entities.person_cards import (
    PersonCardBaseSchema,
    PersonCardCreateSchema,
    PersonCardUpdateSchema,
    PersonCardResponseSchema
)
from ..repository import person_card


def get_person_card(person_id: int, db: Session) -> dict:
    pass


def create_person_card(person_data: PersonCardCreateSchema, db: Session) -> dict:
    pass


def update_person_card(person_data: PersonCardUpdateSchema, db: Session) -> dict:
    pass


def delete_person_card(person_id: int, db: Session) -> dict:
    pass


def add_kinship_to_person(person_data, db: Session) -> dict:
    pass