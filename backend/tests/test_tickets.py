"""Ticket API tests: creation, ML prediction fields, filtering, pagination, assignment, status, history."""
from app.core.constants import RoleEnum


def _create_ticket(client, headers, subject="Cannot access my dashboard", urgent=False):
    description = "This is an urgent outage, everything is broken and down." if urgent else \
        "I have a general question about my account settings."
    r = client.post(
        "/tickets",
        json={
            "subject": subject,
            "description": description,
            "requester_name": "Jane Doe",
            "requester_email": "jane.doe@example.com",
            "channel": "email",
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_create_ticket_returns_prediction_fields(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_t1@example.com")
    headers = auth_headers(agent)
    ticket = _create_ticket(client, headers)

    prediction = ticket["latest_prediction"]
    assert prediction is not None
    for field in ["category", "urgency", "sentiment", "confidence", "model_version", "explanation", "predicted_at"]:
        assert field in prediction
    assert 0.0 <= prediction["confidence"] <= 1.0


def test_urgent_language_predicts_higher_urgency(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_t2@example.com")
    headers = auth_headers(agent)
    ticket = _create_ticket(client, headers, subject="URGENT: system down, critical outage", urgent=True)
    assert ticket["latest_prediction"]["urgency"] in ("high", "critical")


def test_list_tickets_pagination(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_t3@example.com")
    headers = auth_headers(agent)
    for i in range(5):
        _create_ticket(client, headers, subject=f"Ticket number {i}")

    r = client.get("/tickets?page=1&page_size=2", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["total_pages"] == 3


def test_list_tickets_search_filter(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_t4@example.com")
    headers = auth_headers(agent)
    _create_ticket(client, headers, subject="Billing invoice mismatch")
    _create_ticket(client, headers, subject="Cannot connect to VPN")

    r = client.get("/tickets?search=invoice", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert "invoice" in body["items"][0]["subject"].lower()


def test_get_ticket_detail_not_found(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_t5@example.com")
    headers = auth_headers(agent)
    r = client.get("/tickets/does-not-exist", headers=headers)
    assert r.status_code == 404
    assert "error" in r.json()


def test_assign_ticket(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_t6@example.com")
    headers = auth_headers(agent)
    ticket = _create_ticket(client, headers)

    r = client.post(f"/tickets/{ticket['id']}/assign", json={"assigned_to_id": agent.id}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["assigned_to_id"] == agent.id
    assert body["status"] == "open"  # auto-transitions from 'new'


def test_update_ticket_status(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_t7@example.com")
    headers = auth_headers(agent)
    ticket = _create_ticket(client, headers)

    r = client.post(f"/tickets/{ticket['id']}/status", json={"status": "resolved"}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "resolved"
    assert body["resolved_at"] is not None


def test_invalid_status_rejected(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_t8@example.com")
    headers = auth_headers(agent)
    ticket = _create_ticket(client, headers)

    r = client.post(f"/tickets/{ticket['id']}/status", json={"status": "not_a_real_status"}, headers=headers)
    assert r.status_code == 422


def test_add_message_and_history(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_t9@example.com")
    headers = auth_headers(agent)
    ticket = _create_ticket(client, headers)

    r = client.post(
        f"/tickets/{ticket['id']}/messages",
        json={"sender_type": "agent", "sender_name": "Aria Agent", "body": "Looking into this now."},
        headers=headers,
    )
    assert r.status_code == 201

    r = client.get(f"/tickets/{ticket['id']}/history", headers=headers)
    assert r.status_code == 200
    events = r.json()["events"]
    types = {e["type"] for e in events}
    assert "created" in types
    assert "message" in types
    assert "prediction" in types


def test_ticket_requires_auth(client):
    r = client.get("/tickets")
    assert r.status_code == 401


def test_create_ticket_validation_error(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_t10@example.com")
    headers = auth_headers(agent)
    r = client.post("/tickets", json={"subject": "Missing fields"}, headers=headers)
    assert r.status_code == 422
