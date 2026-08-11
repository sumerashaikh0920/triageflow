"""Role-based access control tests: agent / team_lead / admin permission boundaries."""
from app.core.constants import RoleEnum


def test_agent_cannot_create_team(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_roles1@example.com")
    headers = auth_headers(agent)
    r = client.post("/teams", json={"name": "New Team"}, headers=headers)
    assert r.status_code == 403


def test_admin_can_create_team(client, make_user, auth_headers):
    admin = make_user(RoleEnum.admin, email="admin_roles1@example.com")
    headers = auth_headers(admin)
    r = client.post("/teams", json={"name": "Admin Created Team"}, headers=headers)
    assert r.status_code == 201
    assert r.json()["name"] == "Admin Created Team"


def test_team_lead_can_create_routing_rule(client, make_user, make_team, auth_headers):
    team = make_team("Billing Support")
    lead = make_user(RoleEnum.team_lead, email="lead_roles1@example.com", team=team)
    headers = auth_headers(lead)
    r = client.post(
        "/routing/rules",
        json={"name": "Route billing", "condition": {"category": "billing"}, "target_team_id": team.id},
        headers=headers,
    )
    assert r.status_code == 201


def test_agent_cannot_create_routing_rule(client, make_user, make_team, auth_headers):
    team = make_team("Billing Support 2")
    agent = make_user(RoleEnum.agent, email="agent_roles2@example.com", team=team)
    headers = auth_headers(agent)
    r = client.post(
        "/routing/rules",
        json={"name": "Route billing", "condition": {"category": "billing"}, "target_team_id": team.id},
        headers=headers,
    )
    assert r.status_code == 403


def test_only_admin_can_update_user(client, make_user, auth_headers):
    lead = make_user(RoleEnum.team_lead, email="lead_roles2@example.com")
    target = make_user(RoleEnum.agent, email="target_agent@example.com")
    headers = auth_headers(lead)
    r = client.patch(f"/users/{target.id}", json={"full_name": "Changed Name"}, headers=headers)
    assert r.status_code == 403


def test_admin_can_update_user(client, make_user, auth_headers):
    admin = make_user(RoleEnum.admin, email="admin_roles2@example.com")
    target = make_user(RoleEnum.agent, email="target_agent2@example.com")
    headers = auth_headers(admin)
    r = client.patch(f"/users/{target.id}", json={"full_name": "Changed Name"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["full_name"] == "Changed Name"


def test_agent_and_lead_cannot_list_users(client, make_user, auth_headers):
    agent = make_user(RoleEnum.agent, email="agent_roles3@example.com")
    headers = auth_headers(agent)
    r = client.get("/users", headers=headers)
    assert r.status_code == 403


def test_team_lead_can_list_users(client, make_user, auth_headers):
    lead = make_user(RoleEnum.team_lead, email="lead_roles3@example.com")
    headers = auth_headers(lead)
    r = client.get("/users", headers=headers)
    assert r.status_code == 200


def test_only_admin_can_access_settings(client, make_user, auth_headers):
    lead = make_user(RoleEnum.team_lead, email="lead_roles4@example.com")
    headers = auth_headers(lead)
    r = client.get("/settings", headers=headers)
    assert r.status_code == 403

    admin = make_user(RoleEnum.admin, email="admin_roles3@example.com")
    admin_headers = auth_headers(admin)
    r = client.get("/settings", headers=admin_headers)
    assert r.status_code == 200
