"""Shared test fixtures.

Uses an in-memory SQLite DB for speed + isolation. Models use the generic
SQLAlchemy JSON type which SQLite supports via json1.
"""
import os

# Set env BEFORE importing app modules so Settings picks it up.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("API_KEY", "test-api-key")
# Loose limits so tests don't accidentally hit 429 unless they're testing it.
os.environ.setdefault("RATE_LIMIT_PUBLIC", "1000/minute")
os.environ.setdefault("RATE_LIMIT_PLAYER_LOOKUP", "1000/minute")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base


@pytest.fixture
def db_engine():
    """Fresh in-memory SQLite engine per test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Sessionmaker bound to the ephemeral engine."""
    SessionLocal = sessionmaker(db_engine, class_=Session, expire_on_commit=False)
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client(db_engine):
    """FastAPI TestClient with get_session overridden to use the test engine."""
    # Import here so module-level os.environ is already set.
    from app.main import app
    from app.db import get_session as real_get_session

    SessionLocal = sessionmaker(db_engine, class_=Session, expire_on_commit=False)

    def _override_session():
        with SessionLocal() as s:
            yield s

    app.dependency_overrides[real_get_session] = _override_session
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
