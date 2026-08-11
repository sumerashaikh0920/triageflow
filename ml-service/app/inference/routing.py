"""Configurable routing engine.

Loads rules from a YAML file (see routing_rules.yaml) so ops/product teams
can change team assignment logic without a code change or model redeploy.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from app.config import settings


@dataclass
class RoutingDecision:
    team: str
    reason: str


class RoutingEngine:
    def __init__(self, rules_path: Optional[Path] = None) -> None:
        self.rules_path = rules_path or settings.routing_rules_path
        self._default_team = "general_support"
        self._rules: list[dict] = []
        self.reload()

    def reload(self) -> None:
        if not Path(self.rules_path).exists():
            # Safe built-in fallback so the service never hard-fails on a
            # missing/misconfigured rules file.
            self._default_team = "general_support"
            self._rules = []
            return
        with open(self.rules_path, "r") as f:
            config = yaml.safe_load(f) or {}
        self._default_team = config.get("default_team", "general_support")
        self._rules = config.get("rules", [])

    def route(self, category: str, urgency: str) -> RoutingDecision:
        exact_match = None
        category_default = None

        for rule in self._rules:
            if rule.get("category") != category:
                continue
            rule_urgency = rule.get("urgency", "*")
            if rule_urgency == urgency:
                exact_match = rule
                break
            if rule_urgency == "*" and category_default is None:
                category_default = rule

        if exact_match:
            return RoutingDecision(
                team=exact_match["team"],
                reason=f"Matched rule category='{category}' urgency='{urgency}'.",
            )
        if category_default:
            return RoutingDecision(
                team=category_default["team"],
                reason=f"Matched category default for '{category}' (urgency-agnostic).",
            )
        return RoutingDecision(
            team=self._default_team,
            reason="No matching rule; used global default team.",
        )


# Module-level singleton used by the API. `reload()` can be called to
# pick up rule-file edits without a restart if desired.
routing_engine = RoutingEngine()
