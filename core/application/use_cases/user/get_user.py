from core.domain.entities import User
from core.domain.repositories import UserRepository


class GetUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    def execute(self, user_id: int) -> User:
        return self._user_repo.get_by_id(user_id)
