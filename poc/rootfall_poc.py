#!/usr/bin/env python3
"""
ROOTFALL Proof-of-Concept: Independent Corroboration with Root Ablation

Author: Agim Haxhijaha, ORCID 0009-0002-3234-7765

DISCLAIMER: PoC only — not production, not peer reviewed.
Library API: `from rootfall import ROOTFALLEngine`
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rootfall import (
    DecisionPath,
    DecisionScenario,
    EvidenceRoot,
    ablate_root,
    generate_rootfall_certificate,
    run_ablation_battery,
)

# ---------------------------------------------------------------------------
# Scenario builders
# ---------------------------------------------------------------------------

def build_pass_scenario() -> DecisionScenario:
    """
    PASS case: 3 truly independent paths with distinct roots.
    Decision: 'System is safe to operate'.
    """
    scenario = DecisionScenario(
        scenario_id="PASS_independent_corroboration",
        description="Three paths with fully independent evidence roots",
        decision="System is safe to operate",
    )

    scenario.roots = {
        "R1_sensor_array": EvidenceRoot(
            "R1_sensor_array", "physical_sensor",
            "Primary temperature sensor array reading", 0.95,
        ),
        "R2_manual_inspection": EvidenceRoot(
            "R2_manual_inspection", "human_observation",
            "Certified inspector visual check", 0.90,
        ),
        "R3_satellite_telemetry": EvidenceRoot(
            "R3_satellite_telemetry", "remote_telemetry",
            "Independent satellite thermal imaging", 0.88,
        ),
    }

    scenario.paths = [
        DecisionPath(
            path_id="PATH_A",
            label="Sensor analytics route",
            root_ids=["R1_sensor_array"],
            intermediate_steps=[
                "Aggregate 24h sensor readings",
                "Apply threshold model",
                "No anomaly detected",
            ],
            conclusion="System is safe to operate",
        ),
        DecisionPath(
            path_id="PATH_B",
            label="Human inspection route",
            root_ids=["R2_manual_inspection"],
            intermediate_steps=[
                "Inspector reviews physical state",
                "Checks safety interlocks",
                "No defects found",
            ],
            conclusion="System is safe to operate",
        ),
        DecisionPath(
            path_id="PATH_C",
            label="Satellite corroboration route",
            root_ids=["R3_satellite_telemetry"],
            intermediate_steps=[
                "Download thermal imagery",
                "Compare against baseline",
                "Thermal profile nominal",
            ],
            conclusion="System is safe to operate",
        ),
    ]

    return scenario


def build_fail_scenario() -> DecisionScenario:
    """
    FAIL case: 3 paths appear independent but secretly share R_SHARED.
    Ablation of R_SHARED collapses all paths.
    """
    scenario = DecisionScenario(
        scenario_id="FAIL_false_plurality",
        description="Three paths that secretly share a common evidence root",
        decision="Drug compound X is effective",
    )

    scenario.roots = {
        "R_SHARED_database": EvidenceRoot(
            "R_SHARED_database", "shared_database",
            "Central clinical trial database (single source)", 0.70,
        ),
        "R2_lab_assay": EvidenceRoot(
            "R2_lab_assay", "laboratory",
            "In-vitro assay results", 0.85,
        ),
        "R3_peer_review": EvidenceRoot(
            "R3_peer_review", "publication",
            "Peer-reviewed meta-analysis", 0.80,
        ),
    }

    # PATH_A and PATH_B both secretly depend on R_SHARED_database
    # PATH_C uses R3 which itself was derived from R_SHARED
    scenario.paths = [
        DecisionPath(
            path_id="PATH_ALPHA",
            label="Clinical endpoint route (appears independent)",
            root_ids=["R_SHARED_database"],
            intermediate_steps=[
                "Query trial database for endpoint data",
                "Statistical analysis shows significance",
            ],
            conclusion="Drug compound X is effective",
        ),
        DecisionPath(
            path_id="PATH_BETA",
            label="Lab confirmation route (appears independent)",
            root_ids=["R_SHARED_database", "R2_lab_assay"],
            intermediate_steps=[
                "Cross-reference lab assay with trial data",
                "Results align with database entries",
            ],
            conclusion="Drug compound X is effective",
        ),
        DecisionPath(
            path_id="PATH_GAMMA",
            label="Literature meta-analysis route (appears independent)",
            root_ids=["R3_peer_review"],
            intermediate_steps=[
                "Meta-analysis cites trial database as primary source",
                "Published conclusion: effective",
            ],
            conclusion="Drug compound X is effective",
        ),
    ]

    return scenario


# ---------------------------------------------------------------------------
# Main demonstration
# ---------------------------------------------------------------------------

def run_scenario_demo(scenario: DecisionScenario) -> dict[str, Any]:
    """Run full ROOTFALL analysis on one scenario."""
    print(f"\n{'-' * 70}")
    print(f"Scenario: {scenario.scenario_id}")
    print(f"Description: {scenario.description}")
    print(f"Decision: {scenario.decision}")
    print(f"Paths: {len(scenario.paths)}")
    print(f"Roots: {len(scenario.roots)}")
    print(f"{'-' * 70}")

    for path in scenario.paths:
        print(f"\n  {path.path_id} ({path.label})")
        print(f"    Roots: {path.root_ids}")
        for step in path.intermediate_steps:
            print(f"    -> {step}")
        print(f"    Conclusion: {path.conclusion}")

    print(f"\n  Independence score: {scenario.compute_independence_score()}")

    hidden = scenario.detect_hidden_shared_roots()
    if hidden:
        print("  Hidden shared roots detected:")
        for h in hidden:
            print(f"    ! {h['root_id']} shared by {h['shared_by_paths']}")

    print("\n  Ablation tests:")
    ablation_results = run_ablation_battery(scenario)
    for result in ablation_results:
        status = "SURVIVES" if result["decision_survives"] else "COLLAPSES"
        print(
            f"    Ablate {result['ablated_root']}: "
            f"{status} ({result['remaining_corroboration']} paths remain)"
        )

    certificate = generate_rootfall_certificate(scenario, ablation_results)

    print(f"\n  VERDICT: {certificate['verdict']}")
    print(f"  Reason: {certificate['verdict_reason']}")

    return certificate


def main() -> int:
    timestamp = datetime.now(timezone.utc).isoformat()

    print("=" * 70)
    print("ROOTFALL PoC: Independent Corroboration with Root Ablation")
    print(f"Author: Agim Haxhijaha (ORCID 0009-0002-3234-7765)")
    print(f"Timestamp: {timestamp}")
    print("=" * 70)

    pass_scenario = build_pass_scenario()
    fail_scenario = build_fail_scenario()

    pass_cert = run_scenario_demo(pass_scenario)
    fail_cert = run_scenario_demo(fail_scenario)

    evidence: dict[str, Any] = {
        "framework": "ROOTFALL",
        "author": "Agim Haxhijaha",
        "orcid": "0009-0002-3234-7765",
        "disclaimer": "PoC only — not production, not peer reviewed",
        "timestamp_utc": timestamp,
        "scenarios": {
            "pass_case": pass_cert,
            "fail_case": fail_cert,
        },
        "summary": {
            "pass_verdict": pass_cert["verdict"],
            "fail_verdict": fail_cert["verdict"],
            "pass_independence": pass_cert["independence_score"],
            "fail_independence": fail_cert["independence_score"],
            "false_plurality_exposed": fail_cert["false_plurality_detected"],
            "demonstration_success": (
                pass_cert["verdict"] == "PASS"
                and fail_cert["verdict"] == "FAIL"
                and fail_cert["false_plurality_detected"]
            ),
        },
    }

    print("\n" + "=" * 70)
    print("ROOTFALL CERTIFICATES")
    print("=" * 70)
    print(json.dumps(
        {"pass": pass_cert, "fail": fail_cert},
        indent=2,
        ensure_ascii=False,
    ))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  PASS case verdict     : {pass_cert['verdict']}")
    print(f"  PASS independence     : {pass_cert['independence_score']}")
    print(f"  FAIL case verdict     : {fail_cert['verdict']}")
    print(f"  FAIL independence     : {fail_cert['independence_score']}")
    print(f"  False plurality found : {fail_cert['false_plurality_detected']}")
    print(f"  Demonstration success : {evidence['summary']['demonstration_success']}")

    output_path = Path(__file__).resolve().parent / "rootfall_evidence.json"
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(evidence, fh, indent=2, ensure_ascii=False)

    print(f"\nEvidence written to: {output_path}")
    return 0 if evidence["summary"]["demonstration_success"] else 1


if __name__ == "__main__":
    sys.exit(main())

