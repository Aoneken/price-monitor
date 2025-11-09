"""Pytest configuration and fixtures for integration tests."""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from webapp.database import Base
from webapp.main import app


@pytest.fixture(scope="function")
def test_client(monkeypatch):
    """Create a test client with a temporary SQLite database."""
    # Create a temporary database file
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db_path = temp_db.name
    temp_db.close()

    # Set testing environment
    monkeypatch.setenv("TESTING", "1")
    # Override database URL to use temporary database
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{temp_db_path}")

    # Create engine and tables
    engine = create_engine(
        f"sqlite:///{temp_db_path}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)

    # Patch SessionLocal to use test database
    from webapp import database

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    original_session_local = database.SessionLocal
    database.SessionLocal = TestSessionLocal

    # Create test client
    with TestClient(app) as client:
        yield client

    # Restore original SessionLocal
    database.SessionLocal = original_session_local

    # Cleanup
    try:
        os.unlink(temp_db_path)
    except Exception:
        pass
