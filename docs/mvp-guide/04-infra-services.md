# 4. Инфраструктурные сервисы

---

### MVP-INFRA-08 — JWT-сервис: генерация, валидация, refresh

```python path=core/infrastructure/auth/jwt_service.py
from datetime import datetime, timedelta, UTC
from typing import Optional
from jose import JWTError, jwt
from core.infrastructure.config.settings import Settings

_settings = Settings()

ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or ACCESS_TOKEN_EXPIRE)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, _settings.SECRET_KEY, algorithm=_settings.ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or REFRESH_TOKEN_EXPIRE)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, _settings.SECRET_KEY, algorithm=_settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Декодирует токен, поднимает JWTError при невалидном/истёкшем"""
    return jwt.decode(token, _settings.SECRET_KEY, algorithms=[_settings.ALGORITHM])


def get_user_id_from_token(token: str) -> int:
    """Извлекает user_id (sub) из токена"""
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise JWTError("Отсутствует subject в токене")
    return int(user_id)
```

---

### MVP-INFRA-09 — Email-сервис: отправка писем (SMTP) + заглушка для dev

```python path=core/infrastructure/services/email_service.py
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class IEmailService(ABC):
    @abstractmethod
    def send_reset_email(self, to_email: str, token: str) -> None:
        pass


class SMTPEmailService(IEmailService):
    """Реальная отправка через SMTP"""
    def __init__(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str):
        self._host = smtp_host
        self._port = smtp_port
        self._user = smtp_user
        self._password = smtp_password

    def send_reset_email(self, to_email: str, token: str) -> None:
        import smtplib
        from email.mime.text import MIMEText
        msg = MIMEText(f"Токен сброса пароля: {token}")
        msg["Subject"] = "Сброс пароля — Family Tree"
        msg["From"] = self._user
        msg["To"] = to_email
        with smtplib.SMTP(self._host, self._port) as server:
            server.starttls()
            server.login(self._user, self._password)
            server.send_message(msg)


class DevEmailService(IEmailService):
    """Заглушка для dev — логирует токен в консоль"""
    def send_reset_email(self, to_email: str, token: str) -> None:
        logger.info(f"[DEV EMAIL] To: {to_email}, Reset token: {token}")
        print(f"🔑 Токен сброса для {to_email}: {token}")
```

```python path=core/infrastructure/services/token_store.py
"""Простое in-memory хранилище токенов сброса пароля (для MVP)"""
from datetime import datetime, timedelta, UTC
from typing import Optional


class ResetTokenStore:
    def __init__(self):
        self._store: dict[str, tuple[int, datetime]] = {}

    def save(self, token: str, user_id: int, ttl_minutes: int = 30) -> None:
        expires = datetime.now(UTC) + timedelta(minutes=ttl_minutes)
        self._store[token] = (user_id, expires)

    def validate_token(self, token: str) -> Optional[int]:
        data = self._store.get(token)
        if not data:
            return None
        user_id, expires = data
        if datetime.now(UTC) > expires:
            del self._store[token]
            return None
        return user_id

    def invalidate_token(self, token: str) -> None:
        self._store.pop(token, None)
```
