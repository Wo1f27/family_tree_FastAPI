from datetime import datetime, date
from sqlalchemy import (
    Integer,
    Boolean,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum as SQLAlchemyEnum,
    text
)
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ....db.config import Base
from ....enums import enums


class Person(Base):
    __tablename__ = 'person_cards'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    patronymic: Mapped[str] = mapped_column(String, nullable=True)
    date_of_birth: Mapped[date] = mapped_column(DateTime, nullable=True)
    date_of_death: Mapped[date] = mapped_column(DateTime, nullable=True)
    gender: Mapped[int] = mapped_column(
        PgEnum(enums.GenderEnum,
               name='gender_enum_type',
               create_type=False),
        nullable=False,
        default=enums.GenderEnum.MALE
    )
    avatar: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())

    extend_existing = True

    kinship_as_root = relationship(
        'PersonKinship',
        back_populates='root_person',
        foreign_keys='[PersonKinship.root_id]'
    )
    kinship_as_person = relationship(
        'PersonKinship',
        back_populates='person',
        foreign_keys='[PersonKinship.person_id]'
    )


class PersonKinship(Base):
    __tablename__ = 'persons_kinship'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='NO ACTION'),
        nullable=False
    )
    root_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('person_cards.id', ondelete='CASCADE'),
        nullable=False
    )
    person_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('person_cards.id', ondelete='CASCADE'),
        nullable=False
    )
    kinship: Mapped[int] = mapped_column(
        PgEnum(enums.KinshipEnum,
               name='kinship_enum_type',
               create_type=False),
        nullable=False,
        default=enums.KinshipEnum.FATHER
    )

    extend_existing = True

    root_person = relationship(
        'Person',
        back_populates='kinship_as_root',
        foreign_keys=[root_id]
    )
    person = relationship(
        'Person',
        back_populates='kinship_as_person',
        foreign_keys=[person_id]
    )
