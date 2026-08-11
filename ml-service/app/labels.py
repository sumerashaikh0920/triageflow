"""Shared label taxonomy.

Keeping this in one place means the heuristic fallback, the sklearn
baseline, the fine-tuned transformer, and the routing engine can never
silently drift apart on what a valid label looks like.
"""
from __future__ import annotations

CATEGORIES = [
    "billing",
    "technical",
    "account",
    "feature_request",
    "general",
]

# Subcategories are modeled as their own flat label space (prefixed by
# category) rather than a nested per-category classifier — this keeps the
# training code identical across all four tasks while still letting the
# API return a category-consistent subcategory.
SUBCATEGORIES = [
    "billing_refund",
    "billing_invoice",
    "billing_subscription",
    "technical_bug",
    "technical_outage",
    "technical_integration",
    "account_login",
    "account_permissions",
    "account_deletion",
    "feature_request_new",
    "feature_request_enhancement",
    "general_question",
    "general_feedback",
]

# Maps each subcategory to its parent category — used for consistency
# checks and for the heuristic fallback.
SUBCATEGORY_TO_CATEGORY = {
    "billing_refund": "billing",
    "billing_invoice": "billing",
    "billing_subscription": "billing",
    "technical_bug": "technical",
    "technical_outage": "technical",
    "technical_integration": "technical",
    "account_login": "account",
    "account_permissions": "account",
    "account_deletion": "account",
    "feature_request_new": "feature_request",
    "feature_request_enhancement": "feature_request",
    "general_question": "general",
    "general_feedback": "general",
}

URGENCY_LEVELS = ["low", "medium", "high", "critical"]

SENTIMENTS = ["negative", "neutral", "positive"]

LABEL_FIELDS = ["category", "subcategory", "urgency", "sentiment"]

LABEL_SPACE = {
    "category": CATEGORIES,
    "subcategory": SUBCATEGORIES,
    "urgency": URGENCY_LEVELS,
    "sentiment": SENTIMENTS,
}


def default_subcategory_for(category: str) -> str:
    """Fallback subcategory when a model predicts a category but the
    conditional subcategory doesn't line up (keeps API responses valid)."""
    for sub, cat in SUBCATEGORY_TO_CATEGORY.items():
        if cat == category:
            return sub
    return SUBCATEGORIES[0]
