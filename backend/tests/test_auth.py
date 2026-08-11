"""Authentication tests: login, invalid credentials, tokens, /me, refresh."""
from app.core.constants import RoleEnum


def test_login_success(client, make_user):
    user = make_user(RoleEnum.agent, email="agent1@example.com")
    r = client.post("/auth/login", json={"email": user.email, "password": "Password123!"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["user"]["email"] == user.email
    assert body["user"]["role"] == "agent"


def test_login_wrong_password(client, make_user):
    user = make_user(RoleEnum.agent, email="agent2@example.com")
    r = client.post("/auth/login", json={"email": user.email, "password": "WrongPassword!"})
    assert r.status_code == 401


def test_login_unknown_email(client):
    r = client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert r.status_code == 401


def test_login_inactive_user(client, make_user, db_session):
    user = make_user(RoleEnum.agent, email="inactive@example.com")
    user.is_active = False
    db_session.add(user)
    db_session.commit()

    r = client.post("/auth/login", json={"email": user.email, "password": "Password123!"})
    assert r.status_code == 401


def test_me_requires_token(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_returns_current_user(client, make_user, auth_headers):
    user = make_user(RoleEnum.team_lead, email="lead1@example.com")
    headers = auth_headers(user)
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == user.email


def test_refresh_token_flow(client, make_user):
    user = make_user(RoleEnum.agent, email="agent3@example.com")
    login = client.post("/auth/login", json={"email": user.email, "password": "Password123!"})
    refresh_token = login.json()["refresh_token"]

    r = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_refresh_with_access_token_fails(client, make_user):
    """An access token should not work as a refresh token."""
    user = make_user(RoleEnum.agent, email="agent4@example.com")
    login = client.post("/auth/login", json={"email": user.email, "password": "Password123!"})
    access_token = login.json()["access_token"]

    r = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert r.status_code == 401


def test_invalid_token_rejected(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401
