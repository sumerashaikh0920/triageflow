"""Adapts `MultiTaskTicketClassifier` to the same `.predict(text) ->
{field: (label, confidence)}` interface used by the sklearn baseline, so
`evaluate.py` and the live `predictor.py` can treat both model types
uniformly.
"""
from __future__ import annotations

from pathlib import Path

import torch
import torch.nn.functional as F

from app.labels import LABEL_FIELDS
from app.training.transformer_model import load_transformer_predictor


class TransformerPredictorAdapter:
    def __init__(self, artifact_dir: Path, device: str = "cpu"):
        self.device = device
        self.model, self.tokenizer, self.encoders, self.cfg = load_transformer_predictor(
            artifact_dir, device=device
        )

    @torch.no_grad()
    def predict(self, text: str) -> dict[str, tuple[str, float]]:
        encoding = self.tokenizer(
            text, truncation=True, padding="max_length", max_length=256, return_tensors="pt"
        )
        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        logits = self.model(input_ids=input_ids, attention_mask=attention_mask)

        result = {}
        for field in LABEL_FIELDS:
            probs = F.softmax(logits[field][0], dim=-1)
            best_idx = int(torch.argmax(probs).item())
            label = self.encoders.decode(field, best_idx)
            confidence = float(probs[best_idx].item())
            result[field] = (label, confidence)
        return result
