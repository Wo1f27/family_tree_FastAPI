from core.domain.entities import Person
from core.domain.repositories import PersonRepository, UserRepository
from core.application.dto import UpdatePersonDTO
from datetime import datetime


class UpdatePersonUseCase:
    def __init__(self, person_repo: PersonRepository, user_repo: UserRepository):
        self._person_repo = person_repo
        self._user_repo = user_repo

    def execute(self, dto: UpdatePersonDTO, user_id: int) -> Person:
        user = self._user_repo.get_by_id(user_id)
        person = self._person_repo.get_by_id_and_owner_id(dto.id, user_id)
        if dto.first_name is not None:
            person.first_name = dto.first_name
        if dto.last_name is not None:
            person.last_name = dto.last_name
        if dto.middle_name is not None:
            person.middle_name = dto.middle_name
        if dto.date_birth is not None:
            person.date_birth = dto.date_birth
        if dto.date_death is not None:
            person.date_death = dto.date_death
        if dto.gender is not None:
            person.gender = dto.gender
        if dto.biography is not None:
            person.biography = dto.biography

        person.updated_at = datetime.now()

        return self._person_repo.update(person)