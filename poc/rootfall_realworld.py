#!/usr/bin/env python3
"""
ROOTFALL Real-World Scenario — False plurality in a credit-risk committee.

Modeled on decisions where 15–20 "independent" analyst paths appear to corroborate
an upgrade/downgrade, but several secretly share a vendor feed / proprietary model
root that humans treat as independent market color.

Author: Agim Haxhijaha, ORCID 0009-0002-3234-7765

DISCLAIMER: Illustrative research fiction. Not alleging misconduct by any named firm.
Not production software.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rootfall_poc import (
    DecisionPath,
    DecisionScenario,
    EvidenceRoot,
    generate_rootfall_certificate,
    run_ablation_battery,
)

AUTHOR = "Agim Haxhijaha"
ORCID = "0009-0002-3234-7765"
OUT = Path(__file__).with_name("rootfall_realworld_evidence.json")


def build_credit_committee_scenario() -> DecisionScenario:
    """
    Decision: Upgrade MidCap Industrials Issuer XYZ to BBB+ (investment grade).
    Surface looks like 16 independent corroborating paths; hidden shared roots
    exist in the vendor pricing feed and the same third-party credit model.
    """
    roots: dict[str, EvidenceRoot] = {
        "ROOT_VENDOR_PRICING_FEED_X": EvidenceRoot(
            "ROOT_VENDOR_PRICING_FEED_X",
            "market_data_vendor",
            "Third-party CDS/bond pricing feed X (licensed terminal)",
            0.72,
        ),
        "ROOT_VENDOR_MODEL_CM_7": EvidenceRoot(
            "ROOT_VENDOR_MODEL_CM_7",
            "credit_model_vendor",
            "Commercial credit model CM-7 scorecard (same calibration)",
            0.68,
        ),
        "ROOT_ISSUER_10K": EvidenceRoot(
            "ROOT_ISSUER_10K",
            "issuer_filing",
            "Issuer 10-K audited financial statements",
            0.90,
        ),
        "ROOT_AUDITOR_COMFORT": EvidenceRoot(
            "ROOT_AUDITOR_COMFORT",
            "auditor_letter",
            "External auditor comfort letter on going concern",
            0.88,
        ),
        "ROOT_BANK_SYNDICATE_NOTE": EvidenceRoot(
            "ROOT_BANK_SYNDICATE_NOTE",
            "bank_research",
            "Lead bank syndicate internal credit memo (primary diligence)",
            0.80,
        ),
        "ROOT_SUPPLY_CHAIN_AUDIT": EvidenceRoot(
            "ROOT_SUPPLY_CHAIN_AUDIT",
            "ops_audit",
            "Independent supply-chain site audit (third party)",
            0.77,
        ),
        "ROOT_CUSTOMER_CONCENTRATION": EvidenceRoot(
            "ROOT_CUSTOMER_CONCENTRATION",
            "commercial_diligence",
            "Top-10 customer concentration survey (sales ops)",
            0.74,
        ),
        "ROOT_MACRO_IMF_NOTE": EvidenceRoot(
            "ROOT_MACRO_IMF_NOTE",
            "macro",
            "IMF regional industrial outlook note",
            0.70,
        ),
        "ROOT_REGULATOR_FILING": EvidenceRoot(
            "ROOT_REGULATOR_FILING",
            "regulator",
            "National competition authority clearance filing",
            0.85,
        ),
        "ROOT_INSIDER_WHISTLE": EvidenceRoot(
            "ROOT_INSIDER_WHISTLE",
            "allegation",
            "Unverified whistleblower channel note (low weight)",
            0.35,
        ),
    }

    # Add filler unique roots for scale (evidence items)
    for i in range(1, 41):
        rid = f"ROOT_SECONDARY_EVIDENCE_{i:02d}"
        roots[rid] = EvidenceRoot(
            rid,
            "secondary",
            f"Secondary diligence item #{i} (news clip / peer note / local filing)",
            0.55 + (i % 10) * 0.02,
        )

    decision = "UPGRADE_ISSUER_XYZ_TO_BBB_PLUS"
    paths: list[DecisionPath] = []

    # Paths that LOOK independent but share vendor pricing feed (dense sharing)
    for i, desk in enumerate(
        [
            "Desk_EMEA_Credit",
            "Desk_US_HY",
            "Desk_Asia_Corp",
            "Quant_Signal_A",
            "Quant_Signal_B",
            "Sellside_Note_1",
            "Sellside_Note_2",
            "Internal_Screen_1",
            "Prop_Desk_Note",
            "Risk_Overlay_Note",
        ],
        start=1,
    ):
        paths.append(
            DecisionPath(
                path_id=f"PATH_VENDOR_LOOKALIKE_{i:02d}",
                label=f"{desk} upgrade thesis",
                root_ids=[
                    "ROOT_VENDOR_PRICING_FEED_X",
                    "ROOT_VENDOR_MODEL_CM_7",  # dual shared roots → stronger false plurality
                    f"ROOT_SECONDARY_EVIDENCE_{i:02d}",
                ],
                intermediate_steps=[
                    "Normalize spreads from terminal",
                    "Peer relative value screen",
                    "Committee memo paragraph",
                ],
                conclusion=decision,
            )
        )

    # Paths sharing commercial credit model CM-7 (+ feed echo)
    for i, name in enumerate(
        ["ModelDesk_A", "ModelDesk_B", "ModelDesk_C", "Outsourced_Score", "Consultant_Score"],
        start=1,
    ):
        paths.append(
            DecisionPath(
                path_id=f"PATH_MODEL_LOOKALIKE_{i:02d}",
                label=f"{name} CM-7 driven upgrade",
                root_ids=[
                    "ROOT_VENDOR_MODEL_CM_7",
                    "ROOT_VENDOR_PRICING_FEED_X",
                    f"ROOT_SECONDARY_EVIDENCE_{20+i:02d}",
                ],
                intermediate_steps=[
                    "Run CM-7 scorecard",
                    "Map score to rating notch",
                    "Attach to committee pack",
                ],
                conclusion=decision,
            )
        )

    # Truly independent diligence paths
    true_independent = [
        (
            "PATH_TRUE_FILING",
            "Issuer filing + auditor path",
            ["ROOT_ISSUER_10K", "ROOT_AUDITOR_COMFORT", "ROOT_REGULATOR_FILING"],
        ),
        (
            "PATH_TRUE_BANK",
            "Bank syndicate primary diligence",
            ["ROOT_BANK_SYNDICATE_NOTE", "ROOT_CUSTOMER_CONCENTRATION", "ROOT_SECONDARY_EVIDENCE_30"],
        ),
        (
            "PATH_TRUE_OPS",
            "Ops / supply-chain audit path",
            ["ROOT_SUPPLY_CHAIN_AUDIT", "ROOT_SECONDARY_EVIDENCE_31", "ROOT_SECONDARY_EVIDENCE_32"],
        ),
        (
            "PATH_TRUE_WHISTLE_CONTRA",
            "Whistleblower contra-signal (still concludes upgrade — weak)",
            ["ROOT_INSIDER_WHISTLE", "ROOT_SECONDARY_EVIDENCE_33", "ROOT_SECONDARY_EVIDENCE_34"],
        ),
    ]
    for pid, label, rids in true_independent:
        paths.append(
            DecisionPath(
                path_id=pid,
                label=label,
                root_ids=rids,
                intermediate_steps=["Collect primary evidence", "Cross-check", "Conclude"],
                conclusion=decision,
            )
        )

    return DecisionScenario(
        scenario_id="RW_CREDIT_COMMITTEE_FALSE_PLURALITY",
        description=(
            "Credit committee sees 16 corroborating paths for BBB+ upgrade; "
            "8 share pricing feed X and 4 share model CM-7 — false plurality."
        ),
        decision=decision,
        action_digest="upgrade:issuer_xyz:bbb_plus",
        paths=paths,
        roots=roots,
    )


def human_miss_baseline(hidden: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "method": "committee_count_of_agreeing_memos",
        "apparent_corroboration_count": 16,
        "humans_treat_vendor_feed_paths_as_independent": True,
        "humans_treat_same_model_runs_as_independent": True,
        "hidden_shared_roots_found_by_humans_pre_meeting": 0,
        "rootfall_hidden_shared_roots": len(hidden),
        "typical_failure_mode": (
            "Plurality of memos is counted as independence; shared terminal "
            "feeds and identical vendor models are not ablated."
        ),
    }


def run() -> dict[str, Any]:
    scenario = build_credit_committee_scenario()
    hidden = scenario.detect_hidden_shared_roots()
    independence = scenario.compute_independence_score()
    ablation = run_ablation_battery(scenario)
    cert = generate_rootfall_certificate(scenario, ablation)

    # Critical ablation: remove the vendor pricing feed
    feed_ablation = next(a for a in ablation if a["ablated_root"] == "ROOT_VENDOR_PRICING_FEED_X")
    model_ablation = next(a for a in ablation if a["ablated_root"] == "ROOT_VENDOR_MODEL_CM_7")

    evidence = {
        "framework": "ROOTFALL",
        "script": "rootfall_realworld.py",
        "author": AUTHOR,
        "orcid": ORCID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario": {
            "incident_class": "credit_rating_false_plurality",
            "decision": scenario.decision,
            "path_count": len(scenario.paths),
            "root_count": len(scenario.roots),
            "evidence_item_scale": len(scenario.roots),
            "why_realistic": (
                "Investment committees routinely treat separately authored "
                "desk notes as independent even when they consume the same "
                "vendor terminal feed and the same commercial scorecard."
            ),
        },
        "metrics": {
            "independence_score": independence,
            "hidden_shared_roots": hidden,
            "certificate_verdict": cert.get("verdict", cert.get("status")),
            "certificate": cert,
            "ablation_vendor_feed": feed_ablation,
            "ablation_vendor_model": model_ablation,
        },
        "human_baseline": human_miss_baseline(hidden),
        "what_rootfall_revealed": (
            "ROOTFALL flags false plurality: ablating ROOT_VENDOR_PRICING_FEED_X "
            f"collapses {len(feed_ablation['affected_paths'])} paths; ablating "
            f"ROOT_VENDOR_MODEL_CM_7 collapses {len(model_ablation['affected_paths'])} "
            "paths. Humans counting '16 agreeing memos' miss this."
        ),
        "pass": (
            len(scenario.paths) >= 15
            and len(scenario.roots) >= 40
            and len(hidden) >= 2
            and independence < 0.67
            and len(feed_ablation["affected_paths"]) >= 8
            and cert.get("verdict", cert.get("status")) == "FAIL"
        ),
    }
    return evidence


def main() -> int:
    evidence = run()
    OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print(
        f"ROOTFALL real-world: pass={evidence['pass']} "
        f"paths={evidence['scenario']['path_count']} "
        f"indep={evidence['metrics']['independence_score']} "
        f"verdict={evidence['metrics']['certificate_verdict']}"
    )
    print(f"Wrote {OUT.name}")
    return 0 if evidence["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
