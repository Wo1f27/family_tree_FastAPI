from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


DATABASE_URL = "postgresql+psycopg2://postgres:1234@localhost:5432/family_tree"

engine = create_engine(DATABASE_URL)
session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = session_local()
    try:
        yield db
    finally:
        db.close()
