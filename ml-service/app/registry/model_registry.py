"""Model registry.

Rollback-compatible design:
  - Every trained model (baseline or transformer) gets a row the moment
    it's trained, with `approval_status='pending'`, `deployment_status='staged'`.
  - A human (or an automated gate, for the sklearn "bootstrap" model only)
    must call `approve()` before `activate()` is allowed.
  - `activate(version)` deactivates whatever is currently active
    (demoting it to `deployment_status='retired'`, NOT deleting it) and
    activates the requested version.
  - `rollback(version)` is just `activate()` on an older, still-approved
    version — because retired models are never deleted, rollback is always
    possible as long as the artifact directory still exists on disk.
  - Regression guard: `register_candidate(..., regressed_vs_active=True)`
    permanently blocks that row from ever being activated, enforced in
    `activate()` itself (not just at pipeline level) so the safeguard can't
    be bypassed by calling activate() directly.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models_db import ModelRegistryEntry


class ModelAlreadyActiveError(Exception):
    pass


class RegressedModelDeploymentError(Exception):
    """Raised if code attempts to activate a model flagged as regressed."""


class ModelNotApprovedError(Exception):
    pass


def register_candidate(
    db: Session,
    *,
    version: str,
    model_type: str,
    artifact_path: str,
    metrics: dict,
    dataset_start: Optional[dt.datetime] = None,
    dataset_end: Optional[dt.datetime] = None,
    dataset_version: Optional[str] = None,
    n_training_examples: Optional[int] = None,
    regressed_vs_active: bool = False,
    compared_against_version: Optional[str] = None,
    notes: Optional[str] = None,
) -> ModelRegistryEntry:
    entry = ModelRegistryEntry(
        version=version,
        model_type=model_type,
        artifact_path=artifact_path,
        metrics=metrics,
        dataset_start=dataset_start,
        dataset_end=dataset_end,
        dataset_version=dataset_version,
        n_training_examples=n_training_examples,
        approval_status="pending",
        deployment_status="staged",
        is_active=False,
        regressed_vs_active=regressed_vs_active,
        compared_against_version=compared_against_version,
        notes=notes,
        trained_at=dt.datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def approve(db: Session, version: str, approver: Optional[str] = None) -> ModelRegistryEntry:
    entry = get_by_version(db, version)
    if entry.regressed_vs_active:
        raise RegressedModelDeploymentError(
            f"Model {version} regressed against the active model and cannot be approved for deployment."
        )
    entry.approval_status = "approved"
    if approver:
        entry.notes = (entry.notes or "") + f"\nApproved by {approver}."
    db.commit()
    db.refresh(entry)
    return entry


def reject(db: Session, version: str, reason: Optional[str] = None) -> ModelRegistryEntry:
    entry = get_by_version(db, version)
    entry.approval_status = "rejected"
    if reason:
        entry.notes = (entry.notes or "") + f"\nRejected: {reason}"
    db.commit()
    db.refresh(entry)
    return entry


def activate(db: Session, version: str) -> ModelRegistryEntry:
    """Deploy/activate an approved, non-regressed model. Demotes the
    previously active model (if any) to 'retired' rather than deleting it,
    which is what makes rollback always possible."""
    entry = get_by_version(db, version)

    if entry.regressed_vs_active:
        raise RegressedModelDeploymentError(
            f"Refusing to activate {version}: flagged as a regression vs. the model it was compared against."
        )
    if entry.approval_status != "approved":
        raise ModelNotApprovedError(
            f"Model {version} has approval_status='{entry.approval_status}', must be 'approved' to activate."
        )

    current_active = get_active(db)
    if current_active and current_active.version == version:
        raise ModelAlreadyActiveError(f"{version} is already the active model.")

    if current_active:
        current_active.is_active = False
        current_active.deployment_status = "retired"

    entry.is_active = True
    entry.deployment_status = "active"
    db.commit()
    db.refresh(entry)
    return entry


def rollback(db: Session, version: str) -> ModelRegistryEntry:
    """Reactivate a previously-retired (but still approved) model version."""
    entry = activate(db, version)
    entry.deployment_status = "active"
    entry.notes = (entry.notes or "") + "\nReactivated via rollback."
    db.commit()
    db.refresh(entry)
    return entry


def get_by_version(db: Session, version: str) -> ModelRegistryEntry:
    entry = db.execute(
        select(ModelRegistryEntry).where(ModelRegistryEntry.version == version)
    ).scalar_one_or_none()
    if entry is None:
        raise ValueError(f"No registry entry for version '{version}'")
    return entry


def get_active(db: Session) -> Optional[ModelRegistryEntry]:
    return db.execute(
        select(ModelRegistryEntry).where(ModelRegistryEntry.is_active.is_(True))
    ).scalar_one_or_none()


def list_models(db: Session, limit: int = 50) -> list[ModelRegistryEntry]:
    return list(
        db.execute(
            select(ModelRegistryEntry).order_by(ModelRegistryEntry.created_at.desc()).limit(limit)
        ).scalars()
    )


def compare_metrics(candidate_metrics: dict, active_metrics: Optional[dict], tolerance: float) -> bool:
    """Return True if the candidate REGRESSED relative to the active model
    on the primary headline metric (category weighted F1), beyond the
    configured tolerance. If there is no active model yet, nothing to
    regress against."""
    if not active_metrics:
        return False
    candidate_score = candidate_metrics.get("overall", {}).get("category_weighted_f1")
    active_score = active_metrics.get("overall", {}).get("category_weighted_f1")
    if candidate_score is None or active_score is None:
        # Can't compare -> be conservative and treat as non-regressed but
        # flag via caller-side notes; missing metrics shouldn't silently
        # block deployment of an otherwise-fine model.
        return False
    return candidate_score < (active_score - tolerance)
