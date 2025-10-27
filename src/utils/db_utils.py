from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy.orm import Session, sessionmaker

from models.dbTables import engine


@contextmanager
def get_session(is_read_only: bool = False) -> Generator[Session, Any, None]:
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        if not is_read_only:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
