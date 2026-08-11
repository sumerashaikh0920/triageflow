"""Training entry points.

Two paths:
  * `train_baseline()`      — fast TF-IDF + LogisticRegression, always available,
                               used by default and whenever data is small.
  * `train_transformer()`   — fine-tunes a MultiTaskTicketClassifier with
                               Hugging Face Transformers + PyTorch. Meant for
                               when enough labeled/corrected data has
                               accumulated to be worth the extra compute.

Both write a self-contained artifact directory under `models/<version>/`
and return metadata used to register the model in the DB-backed registry.

Run directly for a local CLI training run:
    python -m app.training.train --mode baseline
    python -m app.training.train --mode transformer --epochs 3
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

from app.config import settings
from app.labels import LABEL_FIELDS
from app.training.dataset import DatasetSplit, load_dataset, split_dataset, validate_labels
from app.training.sklearn_baseline import train_sklearn_baseline
from app.training.transformer_model import (
    LabelEncoderSet,
    MultiTaskTicketClassifier,
    TicketDataset,
)


def make_version(prefix: str) -> str:
    return f"{prefix}-{time.strftime('%Y%m%d-%H%M%S')}"


def train_baseline(
    dataset_path: Path | None = None,
    output_root: Path | None = None,
) -> dict:
    df = load_dataset(dataset_path)
    problems = validate_labels(df)
    if problems:
        raise ValueError(f"Dataset failed validation: {problems}")

    split = split_dataset(df)
    version = make_version("sklearn-baseline")
    output_dir = Path(output_root or settings.model_registry_dir) / version

    meta = train_sklearn_baseline(split.train, output_dir)
    meta.update(
        {
            "version": version,
            "artifact_path": str(output_dir),
            "dataset_start": split.dataset_start.isoformat() if split.dataset_start is not None else None,
            "dataset_end": split.dataset_end.isoformat() if split.dataset_end is not None else None,
            "n_test_examples": len(split.test),
        }
    )
    with open(output_dir / "training_manifest.json", "w") as f:
        json.dump(meta, f, indent=2, default=str)
    return {"meta": meta, "split": split}


def train_transformer(
    dataset_path: Path | None = None,
    output_root: Path | None = None,
    base_model: str | None = None,
    epochs: int = 3,
    batch_size: int = 8,
    lr: float = 2e-5,
    device: str | None = None,
) -> dict:
    base_model = base_model or settings.transformer_base_model
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    df = load_dataset(dataset_path)
    problems = validate_labels(df)
    if problems:
        raise ValueError(f"Dataset failed validation: {problems}")

    split = split_dataset(df)
    encoders = LabelEncoderSet()

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    train_labels = {
        field: [encoders.encode(field, v) for v in split.train[field]] for field in LABEL_FIELDS
    }
    train_dataset = TicketDataset(split.train["text"].tolist(), train_labels, tokenizer)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    model = MultiTaskTicketClassifier(base_model, encoders.num_labels())
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    loss_fn = torch.nn.CrossEntropyLoss()

    model.train()
    history = []
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            logits = model(input_ids=input_ids, attention_mask=attention_mask)

            loss = sum(
                loss_fn(logits[field], batch[f"{field}_label"].to(device))
                for field in LABEL_FIELDS
            )
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg_loss = epoch_loss / max(len(train_loader), 1)
        history.append({"epoch": epoch + 1, "avg_loss": avg_loss})

    version = make_version("transformer")
    output_dir = Path(output_root or settings.model_registry_dir) / version
    output_dir.mkdir(parents=True, exist_ok=True)

    torch.save(model.state_dict(), output_dir / "model.pt")
    tokenizer.save_pretrained(output_dir)
    encoders.save(output_dir / "label_encoders.json")
    with open(output_dir / "config.json", "w") as f:
        json.dump({"base_model": base_model, "model_type": "transformer"}, f, indent=2)

    meta = {
        "version": version,
        "model_type": "transformer",
        "artifact_path": str(output_dir),
        "base_model": base_model,
        "n_training_examples": len(split.train),
        "n_test_examples": len(split.test),
        "epochs": epochs,
        "training_history": history,
        "dataset_start": split.dataset_start.isoformat() if split.dataset_start is not None else None,
        "dataset_end": split.dataset_end.isoformat() if split.dataset_end is not None else None,
    }
    with open(output_dir / "training_manifest.json", "w") as f:
        json.dump(meta, f, indent=2, default=str)
    return {"meta": meta, "split": split}


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Train a TriageFlow ticket classifier.")
    parser.add_argument("--mode", choices=["baseline", "transformer"], default="baseline")
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--epochs", type=int, default=3)
    args = parser.parse_args()

    dataset_path = Path(args.dataset) if args.dataset else None
    if args.mode == "baseline":
        result = train_baseline(dataset_path)
    else:
        result = train_transformer(dataset_path, epochs=args.epochs)

    print(json.dumps(result["meta"], indent=2, default=str))


if __name__ == "__main__":
    _cli()
