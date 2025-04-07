from datetime import datetime
from sqlalchemy import (
    Integer,
    Boolean,
    String,
    Text,
    DateTime,
    Column,
    ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column
from ....db.config import Base


class User(Base):

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str]
    password: Mapped[str] = mapped_column(String, unique=True)
    create_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default='false')


class Profile(Base):

    __tablename__ = 'profiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    date_of_birth: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    email: Mapped[str]
    mobile_phone: Mapped[str]
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    avatar: Mapped[str]
