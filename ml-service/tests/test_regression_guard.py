"""Tests for the "never auto-deploy a regressed model" safeguard.

The guard is enforced at the registry layer itself (not just the
retraining pipeline), so these tests call `model_registry` directly to
prove the safeguard can't be bypassed by skipping the pipeline.
"""
from __future__ import annotations

import pytest

from app.registry import model_registry


def _metrics(weighted_f1: float) -> dict:
    return {"overall": {"category_weighted_f1": weighted_f1, "primary_metric": "category_weighted_f1"}}


def test_compare_metrics_flags_regression():
    active_metrics = _metrics(0.90)
    candidate_metrics = _metrics(0.70)
    assert model_registry.compare_metrics(candidate_metrics, active_metrics, tolerance=0.01) is True


def test_compare_metrics_allows_improvement_or_parity():
    active_metrics = _metrics(0.80)
    better = _metrics(0.85)
    same = _metrics(0.80)
    assert model_registry.compare_metrics(better, active_metrics, tolerance=0.01) is False
    assert model_registry.compare_metrics(same, active_metrics, tolerance=0.01) is False


def test_compare_metrics_respects_tolerance_band():
    active_metrics = _metrics(0.80)
    slightly_worse = _metrics(0.795)  # within 0.01 tolerance
    assert model_registry.compare_metrics(slightly_worse, active_metrics, tolerance=0.01) is False

    meaningfully_worse = _metrics(0.75)
    assert model_registry.compare_metrics(meaningfully_worse, active_metrics, tolerance=0.01) is True


def test_regressed_candidate_cannot_be_approved(db_session):
    entry = model_registry.register_candidate(
        db_session,
        version="candidate-bad-v1",
        model_type="sklearn_baseline",
        artifact_path="/tmp/does-not-matter",
        metrics=_metrics(0.60),
        regressed_vs_active=True,
        compared_against_version="active-v1",
    )
    assert entry.regressed_vs_active is True

    with pytest.raises(model_registry.RegressedModelDeploymentError):
        model_registry.approve(db_session, "candidate-bad-v1")


def test_regressed_candidate_cannot_be_activated_even_if_forced_approved(db_session):
    """Even if someone manually flips approval_status in the DB (bypassing
    the approve() guard), activate() itself must still refuse."""
    entry = model_registry.register_candidate(
        db_session,
        version="candidate-bad-v2",
        model_type="sklearn_baseline",
        artifact_path="/tmp/does-not-matter",
        metrics=_metrics(0.55),
        regressed_vs_active=True,
        compared_against_version="active-v1",
    )
    entry.approval_status = "approved"  # simulate a bypassed/corrupted state
    db_session.commit()

    with pytest.raises(model_registry.RegressedModelDeploymentError):
        model_registry.activate(db_session, "candidate-bad-v2")


def test_non_regressed_candidate_can_be_approved_and_activated(db_session):
    entry = model_registry.register_candidate(
        db_session,
        version="candidate-good-v1",
        model_type="sklearn_baseline",
        artifact_path="/tmp/does-not-matter",
        metrics=_metrics(0.92),
        regressed_vs_active=False,
    )
    model_registry.approve(db_session, "candidate-good-v1")
    activated = model_registry.activate(db_session, "candidate-good-v1")

    assert activated.is_active is True
    assert activated.deployment_status == "active"


def test_activate_requires_approval_first(db_session):
    model_registry.register_candidate(
        db_session,
        version="candidate-unapproved-v1",
        model_type="sklearn_baseline",
        artifact_path="/tmp/does-not-matter",
        metrics=_metrics(0.92),
        regressed_vs_active=False,
    )
    with pytest.raises(model_registry.ModelNotApprovedError):
        model_registry.activate(db_session, "candidate-unapproved-v1")


def test_activating_new_model_retires_previous_and_rollback_restores_it(db_session):
    v1 = model_registry.register_candidate(
        db_session, version="v1", model_type="sklearn_baseline",
        artifact_path="/tmp/v1", metrics=_metrics(0.85),
    )
    model_registry.approve(db_session, v1.version)
    model_registry.activate(db_session, v1.version)

    v2 = model_registry.register_candidate(
        db_session, version="v2", model_type="sklearn_baseline",
        artifact_path="/tmp/v2", metrics=_metrics(0.90),
    )
    model_registry.approve(db_session, v2.version)
    model_registry.activate(db_session, v2.version)

    v1_reloaded = model_registry.get_by_version(db_session, "v1")
    assert v1_reloaded.is_active is False
    assert v1_reloaded.deployment_status == "retired"

    active = model_registry.get_active(db_session)
    assert active.version == "v2"

    # Rollback restores v1 without needing to retrain or re-approve it.
    rolled_back = model_registry.rollback(db_session, "v1")
    assert rolled_back.is_active is True
    assert rolled_back.deployment_status == "active"

    v2_reloaded = model_registry.get_by_version(db_session, "v2")
    assert v2_reloaded.is_active is False
    assert v2_reloaded.deployment_status == "retired"
