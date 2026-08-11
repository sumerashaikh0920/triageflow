"""Zero-dependency keyword heuristic classifier.

This is the last line of defense: if no trained model can be loaded for
any reason (fresh clone with no registry entry, corrupted artifact,
missing torch/sklearn install, etc.) the API still returns a structurally
valid, reasonably sensible prediction instead of a 500 error.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.labels import (
    SENTIMENTS,
    default_subcategory_for,
)

_CATEGORY_KEYWORDS = {
    "billing": ["refund", "invoice", "charge", "charged", "billing", "subscription",
                "payment", "price", "plan", "prorated", "billed"],
    "technical": ["bug", "crash", "crashes", "error", "down", "outage", "500",
                  "integration", "api", "freeze", "freezes", "broken", "glitch"],
    "account": ["password", "login", "log in", "2fa", "two factor", "permission",
                "permissions", "account", "delete my account", "locked out", "access"],
    "feature_request": ["feature", "would love", "would be great", "suggestion",
                         "roadmap", "please add", "idea", "enhancement"],
    "general": ["question", "how do i", "thank you", "thanks", "appreciate", "hours"],
}

_URGENCY_KEYWORDS = {
    "critical": ["urgent", "immediately", "asap", "critical", "down", "outage",
                 "production is completely down", "right now", "every minute"],
    "high": ["locked out", "cannot access", "can't access", "not working",
             "two days", "escalate"],
    "medium": ["issue", "problem", "please", "several"],
}

_NEGATIVE_WORDS = ["unacceptable", "frustrated", "angry", "broken", "terrible",
                    "worst", "hate", "not received", "still have not", "disappointed"]
_POSITIVE_WORDS = ["thank", "thanks", "appreciate", "great", "love", "awesome",
                    "happy", "good job", "well done"]


@dataclass
class HeuristicResult:
    category: str
    subcategory: str
    urgency: str
    sentiment: str
    confidence: dict[str, float]
    reason: str


def _score_keywords(text: str, keyword_map: dict[str, list[str]]) -> tuple[str, float, int]:
    """Return (best_label, confidence, raw_hit_count) via simple keyword hit counting."""
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for label, keywords in keyword_map.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        scores[label] = hits

    best_label = max(scores, key=scores.get)
    best_hits = scores[best_label]
    total_hits = sum(scores.values()) or 1
    # Confidence reflects how dominant the winning label's keyword hits were.
    confidence = 0.35 + 0.55 * (best_hits / total_hits) if best_hits > 0 else 0.3
    confidence = min(confidence, 0.92)
    return best_label, round(confidence, 4), best_hits


def classify(subject: str, body: str) -> HeuristicResult:
    text = f"{subject}. {body}"

    category, cat_conf, cat_hits = _score_keywords(text, _CATEGORY_KEYWORDS)
    if cat_hits == 0:
        category = "general"
        cat_conf = 0.3

    urgency, urg_conf, urg_hits = _score_keywords(text, _URGENCY_KEYWORDS)
    if urg_hits == 0:
        urgency = "low"
        urg_conf = 0.4

    neg_hits = sum(1 for w in _NEGATIVE_WORDS if w in text.lower())
    pos_hits = sum(1 for w in _POSITIVE_WORDS if w in text.lower())
    if neg_hits > pos_hits:
        sentiment, sent_conf = "negative", min(0.4 + 0.1 * neg_hits, 0.9)
    elif pos_hits > neg_hits:
        sentiment, sent_conf = "positive", min(0.4 + 0.1 * pos_hits, 0.9)
    else:
        sentiment, sent_conf = "neutral", 0.5
    assert sentiment in SENTIMENTS

    subcategory = default_subcategory_for(category)
    sub_conf = round(cat_conf * 0.85, 4)

    reason = (
        f"Heuristic fallback: keyword match routed this ticket to category='{category}' "
        f"(from subject/body keywords) with urgency='{urgency}'. No trained model was "
        "available at inference time."
    )

    return HeuristicResult(
        category=category,
        subcategory=subcategory,
        urgency=urgency,
        sentiment=sentiment,
        confidence={
            "category": cat_conf,
            "subcategory": sub_conf,
            "urgency": urg_conf,
            "sentiment": round(sent_conf, 4),
        },
        reason=reason,
    )
