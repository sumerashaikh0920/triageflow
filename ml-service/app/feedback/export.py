"""Export approved, validated corrections into a versioned training
dataset snapshot that can be merged with (or replace) the base example
dataset for the next training run.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.labels import LABEL_SPACE
from app.models_db import TicketFeedback


class DatasetValidationError(Exception):
    pass


def _validate_row(row: TicketFeedback) -> list[str]:
    problems = []
    if not row.ticket_text or not row.ticket_text.strip():
        problems.append(f"feedback id={row.id}: empty ticket_text")

    field_map = {
        "category": row.effective_label("category"),
        "subcategory": row.effective_label("subcategory"),
        "urgency": row.effective_label("urgency"),
        "sentiment": row.effective_label("sentiment"),
    }
    for field, value in field_map.items():
        if value not in LABEL_SPACE[field]:
            problems.append(f"feedback id={row.id}: invalid {field}='{value}'")
    return problems


def validate_approved_feedback(db: Session) -> tuple[list[TicketFeedback], list[str]]:
    """Return (valid_rows, problems) for all approved, not-yet-exported
    feedback rows."""
    rows = list(
        db.execute(
            select(TicketFeedback).where(
                TicketFeedback.review_status == "approved",
                TicketFeedback.exported_in_dataset_version.is_(None),
            )
        ).scalars()
    )

    valid_rows: list[TicketFeedback] = []
    all_problems: list[str] = []
    for row in rows:
        problems = _validate_row(row)
        if problems:
            all_problems.extend(problems)
        else:
            valid_rows.append(row)
    return valid_rows, all_problems


def export_approved_feedback(
    db: Session,
    base_dataset_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> dict:
    """Validate approved corrections, snapshot them (merged with the base
    dataset) into a new versioned CSV, and mark the exported rows so they
    aren't exported twice. Returns a manifest dict."""
    valid_rows, problems = validate_approved_feedback(db)
    if not valid_rows:
        return {
            "dataset_version": None,
            "n_examples": 0,
            "n_from_feedback": 0,
            "problems": problems,
            "message": "No new approved corrections to export.",
        }

    dataset_version = f"feedback-v{dt.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    output_dir = Path(output_dir or settings.feedback_export_dir) / dataset_version
    output_dir.mkdir(parents=True, exist_ok=True)

    feedback_records = []
    for row in valid_rows:
        feedback_records.append(
            {
                "ticket_id": row.ticket_id,
                "subject": row.ticket_text.split(".")[0][:120],
                "body": row.ticket_text,
                "category": row.effective_label("category"),
                "subcategory": row.effective_label("subcategory"),
                "urgency": row.effective_label("urgency"),
                "sentiment": row.effective_label("sentiment"),
                "created_at": row.created_at,
            }
        )
    feedback_df = pd.DataFrame(feedback_records)

    base_path = Path(base_dataset_path or settings.example_dataset_path)
    if base_path.exists():
        base_df = pd.read_csv(base_path)
        merged_df = pd.concat([base_df, feedback_df], ignore_index=True)
    else:
        merged_df = feedback_df

    merged_df = merged_df.drop_duplicates(subset=["ticket_id"], keep="last")
    dataset_csv_path = output_dir / "dataset.csv"
    merged_df.to_csv(dataset_csv_path, index=False)

    for row in valid_rows:
        row.exported_in_dataset_version = dataset_version
    db.commit()

    manifest = {
        "dataset_version": dataset_version,
        "dataset_path": str(dataset_csv_path),
        "n_examples": len(merged_df),
        "n_from_feedback": len(valid_rows),
        "n_from_base": len(merged_df) - len(valid_rows),
        "dataset_start": str(pd.to_datetime(merged_df["created_at"], errors="coerce").min()),
        "dataset_end": str(pd.to_datetime(merged_df["created_at"], errors="coerce").max()),
        "problems_skipped": problems,
        "exported_at": dt.datetime.utcnow().isoformat(),
    }
    with open(output_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    return manifest
