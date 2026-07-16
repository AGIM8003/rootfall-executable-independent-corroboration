"""ROOTFALLEngine — usable research library API. Author: Haxhijaha, Agim ORCID 0009-0002-3234-7765."""
from __future__ import annotations

from .core import (
    DecisionPath,
    DecisionScenario,
    EvidenceRoot,
    ablate_root,
    generate_rootfall_certificate,
    run_ablation_battery,
)
from .types import AttestationReport
from .validators import require_nonempty, require_roots


class ROOTFALLEngine:
    """Independent corroboration checker with root ablation.

    Usage:
        engine = ROOTFALLEngine(decision="APPROVE")
        engine.add_root("R1", source_type="filing", description="10-K")
        engine.add_path("P1", label="path1", root_ids=["R1"], conclusion="APPROVE")
        report = engine.attest()
    """

    def __init__(self, decision: str = "DECIDE", scenario_id: str = "user_scenario") -> None:
        self._scenario = DecisionScenario(
            scenario_id=require_nonempty("scenario_id", scenario_id),
            description="library scenario",
            decision=require_nonempty("decision", decision),
            action_digest=decision.lower().replace(" ", "_"),
        )

    def add_root(
        self,
        root_id: str,
        *,
        source_type: str = "evidence",
        description: str = "",
        reliability: float = 0.7,
    ) -> None:
        root_id = require_nonempty("root_id", root_id)
        if root_id in self._scenario.roots:
            raise ValueError(f"duplicate root: {root_id}")
        if not 0.0 <= reliability <= 1.0:
            raise ValueError("reliability must be in [0,1]")
        self._scenario.roots[root_id] = EvidenceRoot(
            root_id, source_type, description or root_id, reliability
        )

    def add_path(
        self,
        path_id: str,
        *,
        label: str = "",
        root_ids: list[str],
        conclusion: str | None = None,
        intermediate_steps: list[str] | None = None,
    ) -> None:
        path_id = require_nonempty("path_id", path_id)
        if any(p.path_id == path_id for p in self._scenario.paths):
            raise ValueError(f"duplicate path: {path_id}")
        root_ids = require_roots(root_ids)
        unknown = [r for r in root_ids if r not in self._scenario.roots]
        if unknown:
            raise ValueError(f"unknown roots (add_root first): {unknown}")
        self._scenario.paths.append(
            DecisionPath(
                path_id=path_id,
                label=label or path_id,
                root_ids=root_ids,
                intermediate_steps=intermediate_steps or ["collect", "infer", "conclude"],
                conclusion=conclusion or self._scenario.decision,
            )
        )

    def independence_score(self) -> float:
        return self._scenario.compute_independence_score()

    def detect_false_plurality(self) -> list[dict]:
        return self._scenario.detect_hidden_shared_roots()

    def ablate(self, root_id: str) -> dict:
        root_id = require_nonempty("root_id", root_id)
        if root_id not in self._scenario.all_root_ids():
            raise ValueError(f"root not used in any path: {root_id}")
        return ablate_root(self._scenario, root_id)

    def attest(self) -> AttestationReport:
        if not self._scenario.paths:
            return AttestationReport(
                verdict="PASS",
                independence_score=1.0,
                false_plurality_detected=False,
                hidden_shared_roots=[],
                ablation_results=[],
                corroboration_count=0,
                verdict_reason="empty scenario — no paths to evaluate",
                certificate={"verdict": "PASS", "empty": True},
            )
        ablation = run_ablation_battery(self._scenario)
        cert = generate_rootfall_certificate(self._scenario, ablation)
        return AttestationReport(
            verdict=cert["verdict"],
            independence_score=cert["independence_score"],
            false_plurality_detected=cert["false_plurality_detected"],
            hidden_shared_roots=cert["hidden_shared_roots"],
            ablation_results=ablation,
            corroboration_count=cert["corroboration_count"],
            verdict_reason=cert["verdict_reason"],
            certificate=cert,
        )

    @property
    def scenario(self) -> DecisionScenario:
        return self._scenario
