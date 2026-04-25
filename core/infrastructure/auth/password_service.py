import bcrypt


def hash_password(password: str) -> str:
    """Хешировать пароль"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Проверить пароль против хеша"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))