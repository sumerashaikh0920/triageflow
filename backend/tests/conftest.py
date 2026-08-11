"""
Shared pytest fixtures.

Tests run against an in-memory SQLite database (fast, no external services
required) instead of the production PostgreSQL database. The app's models
use cross-compatible SQLAlchemy types, so behavior matches Postgres for
everything exercised here. Set TEST_DATABASE_URL to point at a real Postgres
instance if you want to run the suite against Postgres instead.
"""
import os

os.environ.setdefault("DATABASE_URL", os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
os.environ.setdefault("JWT_SECRET", "test-secret")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.core.constants import RoleEnum
from app.models.team import Team
from app.models.user import User
from app.security import hash_password

TEST_DB_URL = os.environ["DATABASE_URL"]

engine_kwargs = {}
if TEST_DB_URL.startswith("sqlite"):
    engine_kwargs = {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}

engine = create_engine(TEST_DB_URL, **engine_kwargs)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def _fresh_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


DEMO_PASSWORD = "Password123!"


@pytest.fixture
def make_user(db_session):
    """Factory fixture: make_user(role=RoleEnum.agent) -> User"""

    def _make(role: RoleEnum = RoleEnum.agent, email: str | None = None, team: Team | None = None):
        email = email or f"{role.value}@example.com"
        user = User(
            email=email,
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name=f"Test {role.value.title()}",
            role=role,
            team_id=team.id if team else None,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture
def make_team(db_session):
    def _make(name: str = "Technical Support"):
        team = Team(name=name, description="test team")
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)
        return team

    return _make


@pytest.fixture
def auth_headers(client):
    """Factory fixture: auth_headers(user) -> {"Authorization": "Bearer ..."}"""

    def _headers(user):
        r = client.post("/auth/login", json={"email": user.email, "password": DEMO_PASSWORD})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _headers
