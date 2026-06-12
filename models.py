from datetime import datetime, date, UTC
from enum import Enum
from sqlalchemy import ForeignKey, Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

class Gender(str, Enum):
    MALE = 'male'
    FEMALE = 'female'
    OTHER = 'other'


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int | None] = mapped_column(default=None)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gender: Mapped[Gender] = mapped_column(String(10), nullable=False)
    date_of_birth: Mapped[date | None]
    date_of_death: Mapped[date | None]
    biography: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))

    relationships: Mapped[list['Relationship']] = relationship(
        back_populates='person',
        foreign_keys='Relationship.person_id',
        cascade='all, delete-orphan'
    )

    related_relationship: Mapped[list['Relationship']] = relationship(
        foreign_keys='Relationship.person_id_related',
        viewonly=True
    )

    phones: Mapped[list['Phone']] = relationship(
        back_populates='person',
        cascade='all, delete-orphan',
        order_by='Phone.id',
    )

    addresses: Mapped[list['Address']] = relationship(
        back_populates='person',
        cascade='all, delete-orphan',
        order_by='Address.id',
    )

    @property
    def gender_enum(self) -> Gender:
        if isinstance(self.gender, str):
            return Gender(self.gender)
        return self.gender


    def __repr__(self):
        return (f'Person(first_name={self.first_name}, last_name={self.last_name}, '
                f'date_of_birth={self.date_of_birth}, date_of_death={self.date_of_death}, '
                f'biography={self.biography})>')


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey('persons.id'), nullable=False)
    person_id_related: Mapped[int] = mapped_column(ForeignKey('persons.id'), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False)

    person: Mapped['Person'] = relationship(
        back_populates='relationships',
        foreign_keys=[person_id]
    )

    def __repr__(self):
        return (f'Relationship(person_id={self.person_id}, person_id_related={self.person_id_related}, '
                f'relationship_type={self.relationship_type})>')


class Phone(Base):
    __tablename__ = 'phones'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey('persons.id', ondelete='CASCADE'), nullable=False)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
    )

    person: Mapped['Person'] = relationship(back_populates='phones')

    def __repr__(self) -> str:
        return f'Phone(person_id={self.person_id}, number={self.number})>'


class Address(Base):
    __tablename__ = 'addresses'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey('persons.id', ondelete='CASCADE'), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
    )

    person: Mapped['Person'] = relationship(back_populates='addresses')

    def __repr__(self) -> str:
        return f'Address(person_id={self.person_id}, address={self.address!r})>'

