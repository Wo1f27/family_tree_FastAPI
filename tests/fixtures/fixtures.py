import pytest
from datetime import date, datetime, UTC
from unittest.mock import Mock

from core.domain.entities import User, Person
from core.domain.entities import Gender, RelationshipType


@pytest.fixture
def mock_user_repo():
    return Mock()

@pytest.fixture
def mock_person_repo():
    return Mock()

@pytest.fixture
def mock_relationship_repo():
    return Mock()

@pytest.fixture
def sample_user():
    return User(
        id=1,
        username='testuser',
        password_hash='hashed_password',
        email='test@test.com',
        is_active=True
    )

@pytest.fixture
def sample_person():
    return Person(
        id=1,
        owner_id=1,
        first_name='Test',
        last_name='User',
        middle_name='TestMega',
        gender=Gender.MALE,
        biography='TEtwtst',
        date_birth=date(1990, 1, 1),
        date_death=date(2020, 1, 1)
    )
