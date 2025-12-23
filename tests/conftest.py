import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is importable so `import api` works
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.db.base_model import Base


@pytest.fixture(scope="session")
def engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    # Create all tables
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def db_session(engine):
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
