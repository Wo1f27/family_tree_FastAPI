from passlib.context import CryptContext

from app.modules.users.models.users import User


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


if __name__ == '__main__':
    pwd = 'test21'
    hash_pwd = hash_password(pwd)
    print(hash_pwd)
    print(verify_password(pwd, hash_pwd))