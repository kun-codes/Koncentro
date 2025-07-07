from contextlib import contextmanager

from sqlalchemy.orm import sessionmaker

from models.db_tables import engine


@contextmanager
def get_session(is_read_only: bool = False):
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
