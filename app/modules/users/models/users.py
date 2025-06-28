from datetime import datetime
from sqlalchemy import (
    Integer,
    Boolean,
    String,
    DateTime,
    ForeignKey,
    Enum as SQLAlchemyEnum,
    text
)
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column
from ....db.config import Base
from ....enums import enums


class User(Base):

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str]
    password: Mapped[str] = mapped_column(String, unique=True)
    create_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text('true'))

    is_user: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)
    is_superadmin: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)

    extend_existing = True


class Profile(Base):

    __tablename__ = 'profiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    date_of_birth: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    email: Mapped[str]
    mobile_phone: Mapped[str]
    gender: Mapped[int] = mapped_column(
        PgEnum(enums.GenderEnum,
               name='gender_enum_type',
               create_type=False),
        nullable=False,
        default=enums.GenderEnum.MALE
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    avatar: Mapped[str] = mapped_column(String(250), nullable=True)

    extend_existing = True
