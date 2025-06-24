from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_db_url


#DATABASE_URL = "postgresql+psycopg2://postgres:1234@localhost:5432/family_tree"
DATABASE_URL = get_db_url()

engine = create_engine(DATABASE_URL)
session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db: Session = session_local()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def check_db_connection():
    db = next(get_db())
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if result:
            print("Подключение к базе данных успешно!")
        else:
            print("Не удалось подключиться к базе данных.")
    except SQLAlchemyError as e:
        print(f"Ошибка подключения к базе данных: {str(e)}")
    finally:
        db.close()


if __name__ == '__main__':
    check_db_connection()

