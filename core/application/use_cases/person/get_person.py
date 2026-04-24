from core.domain.entities import Person
from core.domain.repositories import PersonRepository


class GetPersonUseCase:
    def __init__(self, person_repo: PersonRepository):
        self._person_repo = person_repo

    def execute(self, person_id: int, user_id: int) -> Person:
        person = self._person_repo.get_by_id_and_owner_id(person_id, user_id)
        if not person:
            raise ValueError('Карточка не найдена')
        return person
