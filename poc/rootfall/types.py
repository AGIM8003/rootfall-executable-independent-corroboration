"""ROOTFALL public types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .core import DecisionPath, DecisionScenario, EvidenceRoot


@dataclass
class AttestationReport:
    verdict: str
    independence_score: float
    false_plurality_detected: bool
    hidden_shared_roots: list[dict[str, Any]]
    ablation_results: list[dict[str, Any]]
    corroboration_count: int
    verdict_reason: str
    certificate: dict[str, Any] = field(default_factory=dict)
