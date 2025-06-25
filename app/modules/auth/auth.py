from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import bcrypt
from sqlalchemy.util import deprecated

from app.modules.users.models.users import User


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def validate_user(db: Session, username: str, password: str) -> dict | HTTPException:
    user = db.query(User).filter_by(username=username).first()
    hashed_password = hash_password(password)
    if user and verify_password(user.password, hashed_password):
        return {'success': True, 'user': user}
    return {'success': False}
