from sqlalchemy import Enum as SQLAlchemyEnum
from enum import Enum


class GenderEnum(Enum):
    MALE = 1
    FEMALE = 2


class KinshipEnum(Enum):
    MOTHER = 1
    FATHER = 2
    BROTHER = 3
    SISTER = 4
    SON = 5
    DAUGHTER = 6


kinship_enum_type = SQLAlchemyEnum(KinshipEnum, name='kinship_enum')
gender_enum_type = SQLAlchemyEnum(GenderEnum, name='gender_enum')
