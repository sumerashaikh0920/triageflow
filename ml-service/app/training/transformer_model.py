"""Multi-task transformer classifier.

A single pretrained encoder (default: distilbert-base-uncased) with four
independent linear classification heads — one per label field. This keeps
training/inference to a single forward pass per ticket instead of four
separate transformer models, while still letting each task have its own
label space and loss term.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import torch
from torch import nn
from torch.utils.data import Dataset
from transformers import AutoModel, AutoTokenizer

from app.labels import LABEL_FIELDS, LABEL_SPACE


class TicketDataset(Dataset):
    def __init__(self, texts: list[str], labels: dict[str, list[int]], tokenizer, max_length: int = 256):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict:
        encoding = self.tokenizer(
            self.texts[idx],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in encoding.items()}
        for field in LABEL_FIELDS:
            item[f"{field}_label"] = torch.tensor(self.labels[field][idx], dtype=torch.long)
        return item


class MultiTaskTicketClassifier(nn.Module):
    def __init__(self, base_model: str, num_labels: dict[str, int], dropout: float = 0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model)
        hidden_size = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.heads = nn.ModuleDict(
            {field: nn.Linear(hidden_size, n) for field, n in num_labels.items()}
        )

    def forward(self, input_ids, attention_mask, **kwargs):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        # Mean-pool over tokens (robust across encoder architectures, avoids
        # relying on a model-specific pooler head).
        last_hidden = outputs.last_hidden_state
        mask = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
        pooled = (last_hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
        pooled = self.dropout(pooled)
        return {field: head(pooled) for field, head in self.heads.items()}


class LabelEncoderSet:
    """Simple label<->id mapping per field, serializable to JSON so the
    artifact is self-contained (no sklearn LabelEncoder pickling needed)."""

    def __init__(self, label_to_id: Optional[dict[str, dict[str, int]]] = None):
        self.label_to_id = label_to_id or {
            field: {label: i for i, label in enumerate(LABEL_SPACE[field])}
            for field in LABEL_FIELDS
        }
        self.id_to_label = {
            field: {i: label for label, i in mapping.items()}
            for field, mapping in self.label_to_id.items()
        }

    def encode(self, field: str, label: str) -> int:
        return self.label_to_id[field][label]

    def decode(self, field: str, idx: int) -> str:
        return self.id_to_label[field][idx]

    def num_labels(self) -> dict[str, int]:
        return {field: len(mapping) for field, mapping in self.label_to_id.items()}

    def save(self, path: Path) -> None:
        with open(path, "w") as f:
            json.dump(self.label_to_id, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "LabelEncoderSet":
        with open(path, "r") as f:
            label_to_id = json.load(f)
        return cls(label_to_id)


def load_transformer_predictor(artifact_dir: Path, device: str = "cpu"):
    """Load a fine-tuned MultiTaskTicketClassifier + tokenizer + label
    encoders from an artifact directory produced by `train.py`."""
    artifact_dir = Path(artifact_dir)
    with open(artifact_dir / "config.json") as f:
        cfg = json.load(f)

    encoders = LabelEncoderSet.load(artifact_dir / "label_encoders.json")
    model = MultiTaskTicketClassifier(cfg["base_model"], encoders.num_labels())
    state_dict = torch.load(artifact_dir / "model.pt", map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(artifact_dir)
    return model, tokenizer, encoders, cfg
