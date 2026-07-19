"""ROOTFALL core primitives. Author: Haxhijaha, Agim ORCID 0009-0002-3234-7765."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class EvidenceRoot:
    """Traceable root origin of evidence."""

    root_id: str
    source_type: str
    description: str
    reliability: float  # 0.0 – 1.0


@dataclass
class DecisionPath:
    """One independent route from evidence roots to a conclusion."""

    path_id: str
    label: str
    root_ids: list[str]
    intermediate_steps: list[str]
    conclusion: str

    def shares_root_with(self, other: DecisionPath) -> set[str]:
        return set(self.root_ids) & set(other.root_ids)


@dataclass
class DecisionScenario:
    """A set of paths converging on a single decision."""

    scenario_id: str
    description: str
    decision: str
    # Aligned with rootfall_gate.DecisionScenario (benchmark / gateway compatibility)
    action_digest: str = ""
    paths: list[DecisionPath] = field(default_factory=list)
    roots: dict[str, EvidenceRoot] = field(default_factory=dict)

    def all_root_ids(self) -> set[str]:
        ids: set[str] = set()
        for path in self.paths:
            ids.update(path.root_ids)
        return ids

    def corroboration_count(self) -> int:
        return len(self.paths)

    def compute_independence_score(self) -> float:
        """
        Independence score: 1.0 = fully independent roots per path,
        0.0 = all paths share a single root.
        """
        if len(self.paths) < 2:
            return 1.0

        n = len(self.paths)
        total_pairs = n * (n - 1) / 2
        shared_pairs = 0

        for i in range(n):
            for j in range(i + 1, n):
                if self.paths[i].shares_root_with(self.paths[j]):
                    shared_pairs += 1

        independence = 1.0 - (shared_pairs / total_pairs)
        return round(independence, 4)

    def detect_hidden_shared_roots(self) -> list[dict[str, Any]]:
        """Find roots shared across paths that appear independent."""
        root_usage: dict[str, list[str]] = {}
        for path in self.paths:
            for rid in path.root_ids:
                root_usage.setdefault(rid, []).append(path.path_id)

        hidden = []
        for rid, path_ids in root_usage.items():
            if len(path_ids) > 1:
                hidden.append({
                    "root_id": rid,
                    "shared_by_paths": path_ids,
                    "root_description": self.roots[rid].description
                    if rid in self.roots else "unknown",
                })
        return hidden


# ---------------------------------------------------------------------------
# Root ablation engine
# ---------------------------------------------------------------------------

def ablate_root(
    scenario: DecisionScenario, root_id: str
) -> dict[str, Any]:
    """
    Remove one root and check which paths can still reach the same
    conclusion independently.
    """
    affected_paths: list[str] = []
    surviving_paths: list[str] = []

    for path in scenario.paths:
        if root_id in path.root_ids:
            affected_paths.append(path.path_id)
        else:
            surviving_paths.append(path.path_id)

    # A path with ablated root cannot reach conclusion
    surviving_conclusions = set()
    for path in scenario.paths:
        if path.path_id in surviving_paths:
            surviving_conclusions.add(path.conclusion)

    decision_survives = (
        scenario.decision in surviving_conclusions
        and len(surviving_paths) > 0
    )

    # Independence among survivors
    surviving_independence = 0.0
    if len(surviving_paths) >= 2:
        survivor_paths = [p for p in scenario.paths if p.path_id in surviving_paths]
        temp = DecisionScenario(
            scenario_id="temp",
            description="",
            decision=scenario.decision,
            paths=survivor_paths,
            roots=scenario.roots,
        )
        surviving_independence = temp.compute_independence_score()

    return {
        "ablated_root": root_id,
        "affected_paths": affected_paths,
        "surviving_paths": surviving_paths,
        "decision_survives": decision_survives,
        "surviving_independence": surviving_independence,
        "remaining_corroboration": len(surviving_paths),
    }


def run_ablation_battery(scenario: DecisionScenario) -> list[dict[str, Any]]:
    """Run ablation for every root in the scenario."""
    results = []
    for root_id in sorted(scenario.all_root_ids()):
        results.append(ablate_root(scenario, root_id))
    return results


def generate_rootfall_certificate(
    scenario: DecisionScenario,
    ablation_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate a structured ROOTFALL Certificate."""
    independence = scenario.compute_independence_score()
    hidden_shared = scenario.detect_hidden_shared_roots()

    # PASS criteria: independence >= 0.67 (at most 1 shared pair in 3 paths)
    # AND ablation of any single root leaves >= 2 surviving independent paths
    min_survivors = min(r["remaining_corroboration"] for r in ablation_results)
    all_survive = all(r["decision_survives"] for r in ablation_results)
    no_hidden_roots = len(hidden_shared) == 0

    # For false plurality: hidden shared roots OR low independence
    false_plurality_detected = not no_hidden_roots or independence < 0.67

    if false_plurality_detected:
        verdict = "FAIL"
        verdict_reason = (
            "False plurality detected: paths share hidden common root(s)"
            if not no_hidden_roots
            else "Independence score below threshold"
        )
    elif all_survive and min_survivors >= 2:
        verdict = "PASS"
        verdict_reason = (
            "Truly independent corroboration: ablation of any single root "
            "leaves >= 2 independent surviving paths"
        )
    else:
        verdict = "FAIL"
        verdict_reason = (
            "Ablation fragility: removing one root collapses corroboration"
        )

    return {
        "certificate_type": "ROOTFALL",
        "scenario_id": scenario.scenario_id,
        "decision": scenario.decision,
        "corroboration_count": scenario.corroboration_count(),
        "independence_score": independence,
        "hidden_shared_roots": hidden_shared,
        "ablation_results": ablation_results,
        "min_survivors_after_ablation": min_survivors,
        "all_decisions_survive_ablation": all_survive,
        "false_plurality_detected": false_plurality_detected,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
    }

