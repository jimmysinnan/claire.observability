import os
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

# CLAIRE_DB_PATH permet de pointer vers un volume persistant (ex: /data/claire.db sur Railway)
_db_path = os.getenv("CLAIRE_DB_PATH", "./claire.db")
engine = create_engine(f"sqlite:///{_db_path}", connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
