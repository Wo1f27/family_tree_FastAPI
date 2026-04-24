from core.domain.entities import User
from core.domain.repositories import UserRepository
from core.application.dto import UpdateUserDTO


class UpdateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    def execute(self, dto: UpdateUserDTO, user_id: int) -> User:
        if dto.email is None:
            raise ValueError('Email не может быть пустым')

        user = self._user_repo.get_by_id(user_id)
        if not user:
            raise ValueError('Пользователь с таким Id не найден')

        existing_email = self._user_repo.get_by_email(dto.email)
        if existing_email and existing_email.id != user.id:
            raise ValueError('Пользователь с таким email уже существует')

        user.email = dto.email

        return self._user_repo.update(user)
