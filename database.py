from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

engine = create_engine(
    f'sqlite:///{DATA_DIR}/genealogy.db',
    echo=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass


# def get_db() -> SessionLocal:
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

def init_db():
    Base.metadata.create_all(engine)
