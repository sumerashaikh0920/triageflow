"""Tests for the human-feedback loop: ingestion, review, and export into a
versioned training dataset."""
from __future__ import annotations

import pandas as pd


def _make_feedback(db, ticket_id="T-1", corrected_category="billing", review_status=None):
    from app.feedback.ingest import record_feedback, review_feedback

    row = record_feedback(
        db,
        ticket_id=ticket_id,
        ticket_text="My invoice looks wrong, please check the charges on my account.",
        original_category="technical",
        original_subcategory="technical_bug",
        original_urgency="low",
        original_sentiment="neutral",
        original_confidence=0.55,
        model_version="test-model-v1",
        corrected_category=corrected_category,
        corrected_subcategory="billing_invoice",
        corrected_urgency=None,
        corrected_sentiment=None,
        feedback_source="agent",
    )
    if review_status:
        row = review_feedback(db, row.id, review_status, reviewer="agent_smith")
    return row


def test_record_and_list_feedback(db_session):
    from app.feedback.ingest import list_feedback

    _make_feedback(db_session, ticket_id="T-1")
    _make_feedback(db_session, ticket_id="T-2")

    all_rows = list_feedback(db_session)
    assert len(all_rows) == 2
    assert {r.ticket_id for r in all_rows} == {"T-1", "T-2"}


def test_review_feedback_updates_status(db_session):
    row = _make_feedback(db_session, ticket_id="T-3")
    assert row.review_status == "pending"

    from app.feedback.ingest import review_feedback
    reviewed = review_feedback(db_session, row.id, "approved", reviewer="qa1")
    assert reviewed.review_status == "approved"
    assert reviewed.reviewer == "qa1"
    assert reviewed.reviewed_at is not None


def test_effective_label_prefers_correction(db_session):
    row = _make_feedback(db_session, ticket_id="T-4", corrected_category="billing")
    assert row.effective_label("category") == "billing"
    # No correction was given for urgency -> falls back to original prediction.
    assert row.effective_label("urgency") == "low"


def test_count_approved_unexported(db_session):
    from app.feedback.ingest import count_approved_unexported

    _make_feedback(db_session, ticket_id="T-5", review_status="approved")
    _make_feedback(db_session, ticket_id="T-6", review_status="approved")
    _make_feedback(db_session, ticket_id="T-7", review_status="pending")

    assert count_approved_unexported(db_session) == 2


def test_export_creates_versioned_dataset(db_session, tmp_env, tmp_path):
    from app.feedback.export import export_approved_feedback

    _make_feedback(db_session, ticket_id="T-8", corrected_category="billing", review_status="approved")
    _make_feedback(db_session, ticket_id="T-9", corrected_category="account", review_status="approved")

    manifest = export_approved_feedback(
        db_session,
        base_dataset_path=tmp_env.example_dataset_path,
        output_dir=tmp_path / "exports",
    )

    assert manifest["n_from_feedback"] == 2
    assert manifest["dataset_version"] is not None
    assert manifest["dataset_version"].startswith("feedback-v")

    dataset = pd.read_csv(manifest["dataset_path"])
    assert "T-8" in dataset["ticket_id"].values
    assert "T-9" in dataset["ticket_id"].values

    # Exported rows are marked so a second export run doesn't duplicate them.
    from app.feedback.ingest import count_approved_unexported
    assert count_approved_unexported(db_session) == 0


def test_export_skips_invalid_labels(db_session, tmp_env, tmp_path):
    from app.feedback.ingest import record_feedback, review_feedback
    from app.feedback.export import export_approved_feedback

    row = record_feedback(
        db_session,
        ticket_id="T-BAD",
        ticket_text="Some ticket text",
        original_category="technical",
        original_subcategory="technical_bug",
        original_urgency="low",
        original_sentiment="neutral",
        original_confidence=0.5,
        model_version="test-model-v1",
        corrected_category="not_a_real_category",
    )
    review_feedback(db_session, row.id, "approved")

    manifest = export_approved_feedback(
        db_session, base_dataset_path=tmp_env.example_dataset_path, output_dir=tmp_path / "exports2"
    )
    assert manifest["n_examples"] == 0
    assert any("not_a_real_category" in p for p in manifest["problems"])
