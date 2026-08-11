"""
Stubbed ML prediction service.

This sits behind a small interface (`BasePredictor`) so that a real ML/NLP
service (e.g. the sibling `ml-service/` in this repo) can be wired in later
without changing any router or schema code. Swap `MockPredictor` for a real
implementation (e.g. one that calls out to `ml-service` over HTTP/gRPC) and
everything else keeps working.
"""
import hashlib
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from app.core.constants import SentimentEnum, UrgencyEnum

CATEGORIES = [
    ("billing", "refund_request"),
    ("billing", "invoice_question"),
    ("technical", "login_issue"),
    ("technical", "bug_report"),
    ("technical", "integration_error"),
    ("account", "password_reset"),
    ("account", "profile_update"),
    ("shipping", "delayed_order"),
    ("shipping", "lost_package"),
    ("general", "feedback"),
]

CURRENT_MODEL_VERSION = "triage-mock-v1.0.0"


@dataclass
class PredictionResult:
    category: str
    subcategory: Optional[str]
    urgency: UrgencyEnum
    sentiment: SentimentEnum
    confidence: float
    predicted_team_name: Optional[str]
    model_version: str
    explanation: str
    keywords: list[str] = field(default_factory=list)


class BasePredictor(ABC):
    @abstractmethod
    def predict(self, subject: str, description: str) -> PredictionResult:
        ...


class MockPredictor(BasePredictor):
    """Deterministic-ish mock predictor: uses simple keyword heuristics plus a
    seeded random component (seeded from the text) so results are stable for
    the same input but still look varied across tickets."""

    URGENT_WORDS = {"urgent", "asap", "immediately", "critical", "down", "outage", "broken", "emergency"}
    NEGATIVE_WORDS = {"angry", "furious", "terrible", "worst", "unacceptable", "frustrated", "disappointed"}
    POSITIVE_WORDS = {"thanks", "great", "awesome", "love", "appreciate", "happy"}

    def predict(self, subject: str, description: str) -> PredictionResult:
        text = f"{subject} {description}".lower()
        seed = int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)

        category, subcategory = rng.choice(CATEGORIES)

        urgent_hits = sum(1 for w in self.URGENT_WORDS if w in text)
        if urgent_hits >= 2:
            urgency = UrgencyEnum.critical
        elif urgent_hits == 1:
            urgency = UrgencyEnum.high
        else:
            urgency = rng.choices(
                [UrgencyEnum.low, UrgencyEnum.medium, UrgencyEnum.high],
                weights=[0.35, 0.45, 0.2],
            )[0]

        neg_hits = sum(1 for w in self.NEGATIVE_WORDS if w in text)
        pos_hits = sum(1 for w in self.POSITIVE_WORDS if w in text)
        if neg_hits > pos_hits:
            sentiment = SentimentEnum.negative
        elif pos_hits > neg_hits:
            sentiment = SentimentEnum.positive
        else:
            sentiment = SentimentEnum.neutral

        confidence = round(rng.uniform(0.62, 0.98), 3)

        team_map = {
            "billing": "Billing Support",
            "technical": "Technical Support",
            "account": "Account Management",
            "shipping": "Logistics",
            "general": "General Support",
        }
        predicted_team_name = team_map.get(category)

        matched_keywords = [w for w in (self.URGENT_WORDS | self.NEGATIVE_WORDS | self.POSITIVE_WORDS) if w in text]

        explanation = (
            f"Classified as '{category}/{subcategory}' based on keyword and pattern similarity to "
            f"historical tickets. Urgency '{urgency.value}' driven by {urgent_hits} urgency signal(s) "
            f"detected in the text. Sentiment '{sentiment.value}' inferred from tone indicators."
        )

        return PredictionResult(
            category=category,
            subcategory=subcategory,
            urgency=urgency,
            sentiment=sentiment,
            confidence=confidence,
            predicted_team_name=predicted_team_name,
            model_version=CURRENT_MODEL_VERSION,
            explanation=explanation,
            keywords=matched_keywords,
        )


def get_predictor() -> BasePredictor:
    """Factory used by services/routers, so the concrete implementation can be
    swapped centrally (e.g. via a setting) later."""
    return MockPredictor()
