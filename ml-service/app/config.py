"""
Centralized configuration for the TriageFlow ML service.

All values are overridable via environment variables / .env so the service
can be pointed at the same PostgreSQL instance as the main FastAPI backend
(or a dedicated schema/database) without code changes.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Service ---
    ml_service_env: str = "local"
    log_level: str = "INFO"
    service_name: str = "triageflow-ml"

    # --- Database ---
    # Falls back to a local SQLite file so the whole service can be cloned
    # and run with zero external setup (portfolio-friendly). In real
    # deployments this is set to the shared Postgres backend.
    database_url: str = f"sqlite:///{BASE_DIR / 'triageflow_local.db'}"

    # --- Model registry / artifacts ---
    model_registry_dir: Path = BASE_DIR / "models"
    active_model_env_override: Optional[str] = None

    # --- Data ---
    example_dataset_path: Path = BASE_DIR / "data" / "example_tickets.csv"
    feedback_export_dir: Path = BASE_DIR / "data" / "feedback_exports"

    # --- Retraining triggers ---
    retrain_min_approved_corrections: int = 50
    retrain_weekly_enabled: bool = True
    retrain_weekly_interval_days: int = 7
    retrain_regression_tolerance: float = 0.01  # allowed F1 drop before blocking deploy

    # --- Routing ---
    routing_rules_path: Path = BASE_DIR / "app" / "inference" / "routing_rules.yaml"

    # --- Inference ---
    max_text_length: int = 512
    transformer_base_model: str = "distilbert-base-uncased"


settings = Settings()

# Ensure required directories exist at import time (safe/no-ops if present).
settings.model_registry_dir.mkdir(parents=True, exist_ok=True)
settings.feedback_export_dir.mkdir(parents=True, exist_ok=True)
