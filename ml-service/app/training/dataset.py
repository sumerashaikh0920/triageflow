"""Dataset loading / preparation shared by sklearn baseline training,
transformer fine-tuning, and evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
from sklearn.model_selection import train_test_split

from app.config import settings
from app.labels import LABEL_FIELDS

REQUIRED_COLUMNS = ["ticket_id", "subject", "body", "category", "subcategory",
                    "urgency", "sentiment", "created_at"]


@dataclass
class DatasetSplit:
    train: pd.DataFrame
    test: pd.DataFrame
    dataset_start: Optional[pd.Timestamp]
    dataset_end: Optional[pd.Timestamp]
    n_total: int


def load_dataset(path: Optional[Path] = None) -> pd.DataFrame:
    """Load and lightly validate a labeled ticket dataset (CSV)."""
    path = path or settings.example_dataset_path
    df = pd.read_csv(path)

    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Dataset {path} is missing required columns: {missing}")

    df = df.dropna(subset=["subject", "body"] + LABEL_FIELDS).reset_index(drop=True)
    df["text"] = (df["subject"].astype(str) + ". " + df["body"].astype(str)).str.strip()
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df


def validate_labels(df: pd.DataFrame) -> list[str]:
    """Return a list of validation problems (empty list == valid)."""
    from app.labels import LABEL_SPACE

    problems: list[str] = []
    for field in LABEL_FIELDS:
        if field not in df.columns:
            problems.append(f"missing label column: {field}")
            continue
        valid = set(LABEL_SPACE[field])
        bad_values = set(df[field].dropna().unique()) - valid
        if bad_values:
            problems.append(f"invalid values for '{field}': {sorted(bad_values)}")
    if df[["text"] + LABEL_FIELDS].isnull().any().any():
        problems.append("dataset contains null text or label values")
    return problems


def split_dataset(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> DatasetSplit:
    n_total = len(df)
    if n_total < 10:
        # Too small to hold out a meaningful test set (e.g. tiny example
        # dataset / early bootstrap) — evaluate on the full set instead of
        # crashing, and note this clearly in eval reports.
        return DatasetSplit(
            train=df, test=df,
            dataset_start=df["created_at"].min() if "created_at" in df else None,
            dataset_end=df["created_at"].max() if "created_at" in df else None,
            n_total=n_total,
        )

    # Stratify on category (the coarsest label) when every class has >= 2
    # examples; otherwise fall back to a plain random split.
    stratify = None
    counts = df["category"].value_counts()
    if (counts >= 2).all():
        stratify = df["category"]

    train_df, test_df = train_test_split(
        df, test_size=test_size, random_state=random_state, stratify=stratify
    )
    return DatasetSplit(
        train=train_df.reset_index(drop=True),
        test=test_df.reset_index(drop=True),
        dataset_start=df["created_at"].min() if "created_at" in df else None,
        dataset_end=df["created_at"].max() if "created_at" in df else None,
        n_total=n_total,
    )
