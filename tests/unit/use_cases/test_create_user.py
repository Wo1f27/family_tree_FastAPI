import pytest
from unittest.mock import Mock, call

from core.application.use_cases.user import CreateUserUseCase
from core.application.dto import CreateUserDTO
from core.domain.entities import User
from datetime import datetime, UTC


class TestCreateUserUseCase:

    def test_create_user_success(self, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.get_by_username.return_value = None

        created_user = User(
            id=1,
            username='newuser',
            email='newuser@test.com',
            password_hash='hashed_password',
            is_active=True
        )

        mock_user_repo.create.return_value = created_user

        use_case = CreateUserUseCase(mock_user_repo)
        dto = CreateUserDTO(
            username='newuser',
            password='password',
            email='newuser@test.com'
        )

        result = use_case.execute(dto)

        assert result.id == 1
        assert result.username == 'newuser'
        assert result.email == 'newuser@test.com'
        mock_user_repo.get_by_email.assert_called_once_with('newuser@test.com')
        mock_user_repo.get_by_username.assert_called_once_with('newuser')
        mock_user_repo.create.assert_called_once()

    def test_create_user_email_exists(self, mock_user_repo):
        existing_user = User(
            id=1,
            username='existinguser',
            email='existinguser@test.com',
            password_hash='hashed_password',
            is_active=True
        )
        mock_user_repo.get_by_email.return_value = existing_user

        use_case = CreateUserUseCase(mock_user_repo)
        dto = CreateUserDTO(
            username = 'newuser',
            password = 'password',
            email='existinguser@test.com'
        )

        with pytest.raises(ValueError, match='email уже существует'):
            use_case.execute(dto)

    def test_create_user_username_exists(self, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.get_by_username.return_value = Mock(id=1)

        use_case = CreateUserUseCase(mock_user_repo)
        dto = CreateUserDTO(
            username='existinguser',
            password='password',
            email='newuser@test.com'
        )

        with pytest.raises(ValueError, match='username уже существует'):
            use_case.execute(dto)
