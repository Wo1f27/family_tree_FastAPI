from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


engine = create_engine(
    'sqlite:///genealogy.db',
    echo=True,
    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass


def get_db() -> SessionLocal:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(engine)
