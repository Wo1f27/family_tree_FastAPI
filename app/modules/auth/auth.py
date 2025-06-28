from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.modules.users.models.users import User


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def validate_user(db: Session, username: str, password: str) -> dict | HTTPException:
    user = db.query(User).filter_by(username=username).first()
    if user:
        return {'success': verify_password(password, str(user.password)), 'user': user}
    return {'success': False}
