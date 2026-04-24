from core.domain.entities import Person
from core.domain.repositories import PersonRepository, UserRepository
from core.application.dto import CreatePersonDTO


class CreatePersonUseCase:
    def __init__(self, person_repo: PersonRepository, user_repo: UserRepository):
        self._person_repo = person_repo
        self._user_repo = user_repo

    def execute(self, dto: CreatePersonDTO, user_id: int) -> Person:
        user = self._user_repo.get_by_id(user_id)
        if not user:
            raise ValueError('Пользователь не найден')
        person = Person(
            id=None,
            owner_id=user_id,
            first_name=dto.first_name,
            last_name=dto.last_name,
            middle_name=dto.middle_name,
            date_birth=dto.date_birth,
            date_death=dto.date_death,
            gender=dto.gender,
            biography=dto.biography
        )

        return self._person_repo.create(person)
