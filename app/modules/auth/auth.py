from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
import bcrypt

from app.modules.users.models.users import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def validate_user(db: Session, username: str, password: str) -> dict | HTTPException:
    user = db.query(User).filter_by(username=username).first()
    hashed_password = hash_password(password)
    if user and verify_password(user.password, hashed_password):
        return {'success': True}
    return {'success': False}
