"""TriageFlow backend entrypoint: FastAPI app, middleware, routers, exception handlers."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.exceptions import AppError, app_error_handler
from app.routers import (
    auth,
    dashboard,
    feedback,
    health,
    integrations,
    model_metrics,
    routing,
    settings_router,
    sla,
    teams,
    tickets,
    users,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered customer support ticket triage backend.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(tickets.router)
app.include_router(feedback.router)
app.include_router(dashboard.router)
app.include_router(routing.router)
app.include_router(sla.router)
app.include_router(model_metrics.router)
app.include_router(integrations.router)
app.include_router(settings_router.router)


@app.get("/")
def root():
    return {"service": settings.PROJECT_NAME, "status": "running", "docs": "/docs"}
