import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

# Point the app's default engine at a throwaway SQLite file so importing the app
# and running its startup never reaches for a real Postgres. Tests that touch the
# database use the `db`/`client` fixtures below, which build an isolated in-memory
# engine per test.
_TEST_DB = Path(tempfile.gettempdir()) / "houseflavor_test.db"
_TEST_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import get_db
from app.db.models import Base
from app.main import app


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    def override() -> Iterator[Session]:
        yield db

    # The per-IP limiter is process-local state; isolate it per test so every
    # request in the suite (all from the same test client IP) starts fresh.
    from app.api.routes.auth import ip_limiter

    ip_limiter.reset()
    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()
