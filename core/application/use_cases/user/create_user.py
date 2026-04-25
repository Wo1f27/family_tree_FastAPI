from core.domain.entities import User
from core.domain.repositories import UserRepository
from core.application.dto import CreateUserDTO
from core.infrastructure.auth.password_service import hash_password


class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    def execute(self, dto: CreateUserDTO) -> User:
        existing_email = self._user_repo.get_by_email(dto.email)
        if existing_email:
            raise ValueError("Пользователь с таким email уже существует")

        existing_username = self._user_repo.get_by_username(dto.username)
        if existing_username:
            raise ValueError("Пользователь с таким username уже существует")

        hashed_password = hash_password(dto.password)

        user = User(
            id=None,
            email=dto.email,
            username=dto.username,
            password_hash=hashed_password,
        )

        return self._user_repo.create(user)
