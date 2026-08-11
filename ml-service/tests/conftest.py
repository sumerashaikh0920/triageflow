"""Shared pytest fixtures.

Each test gets an isolated, on-disk-temp SQLite database and a fresh
model-registry/models directory so tests never depend on shared state or
a real Postgres instance — this keeps `pytest` runnable with zero external
setup, mirroring the "runs locally without expensive infra" requirement
for the service itself.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_env(tmp_path, monkeypatch):
    """Point the whole app at a scratch SQLite DB + scratch model dir for
    the duration of one test, then reload modules that cache settings."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("MODEL_REGISTRY_DIR", str(tmp_path / "models"))
    monkeypatch.setenv("RETRAIN_MIN_APPROVED_CORRECTIONS", "3")
    monkeypatch.setenv("RETRAIN_WEEKLY_ENABLED", "false")

    # Purge cached app modules so they pick up the new env on next import.
    for mod_name in list(sys.modules):
        if mod_name == "app" or mod_name.startswith("app."):
            del sys.modules[mod_name]

    import app.config as config_module
    importlib.reload(config_module)

    yield config_module.settings


@pytest.fixture()
def db_session(tmp_env):
    from app.db import init_db, session_scope

    init_db()
    with session_scope() as db:
        yield db


@pytest.fixture()
def client(tmp_env):
    from fastapi.testclient import TestClient

    import app.main as main_module
    importlib.reload(main_module)

    with TestClient(main_module.app) as c:
        yield c
