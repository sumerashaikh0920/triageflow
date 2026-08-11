"""
Seed the database with demo accounts, teams, and sample tickets.

Run with:  python -m app.seed
(or automatically inside the Docker entrypoint / via `make seed`)
"""
import random

from app.core.constants import ChannelEnum, RoleEnum, TicketStatus
from app.database import Base, SessionLocal, engine
from app.models.integration import Integration
from app.core.constants import IntegrationStatus, IntegrationType
from app.models.model_version import ModelVersion
from app.models.team import Team
from app.models.user import User
from app.security import hash_password
from app.services.ticket_service import create_ticket_with_prediction

DEMO_PASSWORD = "Password123!"

SAMPLE_TICKETS = [
    ("Refund not received after 2 weeks", "I requested a refund on my last order and it still hasn't shown up. This is unacceptable.", "Maria Chen", "maria.chen@example.com"),
    ("Cannot log into my account", "I keep getting an 'invalid password' error even after resetting it. Urgent, I need access today.", "Devon Lewis", "devon.lewis@example.com"),
    ("Integration webhook failing", "Our webhook integration has been returning 500 errors since this morning, the whole system is down.", "Priya Nair", "priya.nair@example.com"),
    ("Question about my invoice", "Could you clarify the extra line item on my March invoice? Thanks for your help.", "Tom Baker", "tom.baker@example.com"),
    ("Package arrived damaged", "The box was crushed and the item inside is broken. Very disappointed with this shipment.", "Aisha Rahman", "aisha.rahman@example.com"),
    ("Feature request: dark mode", "Would love to see a dark mode option in the app, great product overall!", "Sam Okafor", "sam.okafor@example.com"),
    ("Password reset email not arriving", "I've requested the reset email three times, nothing in my inbox or spam.", "Lena Fischer", "lena.fischer@example.com"),
    ("Order stuck in transit for 10 days", "Tracking hasn't updated in over a week. Where is my package?", "Carlos Mendez", "carlos.mendez@example.com"),
    ("Update billing address", "I need to change the billing address on file for my account.", "Grace Kim", "grace.kim@example.com"),
    ("App crashes on checkout", "The app crashes every time I try to check out, this is critical and blocking all my orders.", "Noah Peterson", "noah.peterson@example.com"),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Database already seeded, skipping.")
            return

        # Teams
        team_names = ["Billing Support", "Technical Support", "Account Management", "Logistics", "General Support"]
        teams = {}
        for name in team_names:
            team = Team(name=name, description=f"{name} team")
            db.add(team)
            teams[name] = team
        db.flush()

        # Demo users, one per role
        demo_users = [
            User(
                email="admin@triageflow.dev",
                hashed_password=hash_password(DEMO_PASSWORD),
                full_name="Ava Administrator",
                role=RoleEnum.admin,
                team_id=None,
            ),
            User(
                email="lead@triageflow.dev",
                hashed_password=hash_password(DEMO_PASSWORD),
                full_name="Liam Teamlead",
                role=RoleEnum.team_lead,
                team_id=teams["Technical Support"].id,
            ),
            User(
                email="agent@triageflow.dev",
                hashed_password=hash_password(DEMO_PASSWORD),
                full_name="Aria Agent",
                role=RoleEnum.agent,
                team_id=teams["Technical Support"].id,
            ),
        ]
        for u in demo_users:
            db.add(u)
        db.flush()

        # Model version
        db.add(ModelVersion(
            version="triage-mock-v1.0.0",
            description="Deterministic mock classifier used until the real ML service is connected.",
            accuracy=0.87,
            is_active=True,
        ))

        # Integrations
        db.add_all([
            Integration(name="Support Inbox", type=IntegrationType.email, status=IntegrationStatus.connected, config={"address": "support@triageflow.dev"}),
            Integration(name="Team Slack", type=IntegrationType.slack, status=IntegrationStatus.connected, config={"channel": "#support-alerts"}),
            Integration(name="Salesforce CRM", type=IntegrationType.crm, status=IntegrationStatus.disconnected, config={}),
            Integration(name="Website Chat Widget", type=IntegrationType.chat_widget, status=IntegrationStatus.connected, config={}),
        ])
        db.commit()

        # Sample tickets (routed through the real create-ticket + mock ML path)
        for subject, description, name, email in SAMPLE_TICKETS:
            ticket = create_ticket_with_prediction(db, {
                "subject": subject,
                "description": description,
                "requester_name": name,
                "requester_email": email,
                "channel": random.choice(list(ChannelEnum)),
            })
            # Randomly assign some tickets to the demo agent for realism
            if random.random() < 0.4:
                ticket.assigned_to_id = demo_users[2].id
                ticket.status = random.choice([TicketStatus.open, TicketStatus.in_progress])
                db.add(ticket)
        db.commit()

        print("Seed complete.")
        print(f"  Admin:      admin@triageflow.dev / {DEMO_PASSWORD}")
        print(f"  Team Lead:  lead@triageflow.dev / {DEMO_PASSWORD}")
        print(f"  Agent:      agent@triageflow.dev / {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
