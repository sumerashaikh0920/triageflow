"""Feedback API tests: correct-category, mark-urgency, accept-prediction."""
from app.core.constants import RoleEnum


def _create_ticket(client, headers):
    r = client.post(
        "/tickets",
        json={
            "subject": "App keeps logging me out",
            "description": "Every few minutes I get logged out of the dashboard.",
            "requester_name": "Alex Rivera",
            "requester_email": "alex.rivera@example.com",
            "channel": "chat",
        },
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


def test_correct_category(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_f1@example.com")
    headers = auth_headers(agent)
    ticket = _create_ticket(client, headers)

    r = client.post(
        "/feedback/correct-category",
        json={"ticket_id": ticket["id"], "corrected_category": "technical", "notes": "Actually a login bug"},
        headers=headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["corrected_category"] == "technical"
    assert body["accepted"] is False

    # ticket's category should now reflect the correction
    r2 = client.get(f"/tickets/{ticket['id']}", headers=headers)
    assert r2.json()["category"] == "technical"


def test_mark_urgency(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_f2@example.com")
    headers = auth_headers(agent)
    ticket = _create_ticket(client, headers)

    r = client.post(
        "/feedback/mark-urgency",
        json={"ticket_id": ticket["id"], "corrected_urgency": "critical"},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["corrected_urgency"] == "critical"

    r2 = client.get(f"/tickets/{ticket['id']}", headers=headers)
    assert r2.json()["urgency"] == "critical"


def test_accept_prediction(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_f3@example.com")
    headers = auth_headers(agent)
    ticket = _create_ticket(client, headers)

    r = client.post(
        "/feedback/accept-prediction",
        json={"ticket_id": ticket["id"], "notes": "Looks right"},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["accepted"] is True


def test_feedback_requires_valid_ticket(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_f4@example.com")
    headers = auth_headers(agent)

    r = client.post(
        "/feedback/correct-category",
        json={"ticket_id": "bogus-id", "corrected_category": "technical"},
        headers=headers,
    )
    assert r.status_code == 404


def test_mark_urgency_invalid_value_rejected(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_f5@example.com")
    headers = auth_headers(agent)
    ticket = _create_ticket(client, headers)

    r = client.post(
        "/feedback/mark-urgency",
        json={"ticket_id": ticket["id"], "corrected_urgency": "super_urgent"},
        headers=headers,
    )
    assert r.status_code == 422


def test_feedback_appears_in_list(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_f6@example.com")
    headers = auth_headers(agent)
    ticket = _create_ticket(client, headers)

    client.post(
        "/feedback/accept-prediction", json={"ticket_id": ticket["id"]}, headers=headers
    )
    r = client.get("/feedback", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_feedback_requires_auth(client):
    r = client.post("/feedback/accept-prediction", json={"ticket_id": "abc"})
    assert r.status_code == 401
