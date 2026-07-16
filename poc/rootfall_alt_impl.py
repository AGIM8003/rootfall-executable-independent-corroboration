#!/usr/bin/env python3
"""
ROOTFALL Alternative Implementation — Set-theoretic independence / ablation.

Author: Agim Haxhijaha, ORCID 0009-0002-3234-7765

DISCLAIMER: PoC alternative implementation only. Not production, not peer reviewed.
Uses generating-set disjointness instead of graph path traversal.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUTHOR = "Agim Haxhijaha"
ORCID = "0009-0002-3234-7765"


def independence_score(gens: list[set[str]]) -> float:
    n = len(gens)
    if n < 2:
        return 1.0
    pairs = n * (n - 1) / 2
    shared = sum(1 for i in range(n) for j in range(i + 1, n) if gens[i] & gens[j])
    return round(1.0 - shared / pairs, 4)


def ablate(gens: list[set[str]], root: str) -> list[set[str]]:
    survivors = []
    for g in gens:
        if root in g:
            continue
        survivors.append(set(g))
    return survivors


def false_plurality(gens: list[set[str]]) -> bool:
    """Non-empty intersection across ostensibly independent generating sets."""
    n = len(gens)
    for i in range(n):
        for j in range(i + 1, n):
            if gens[i] & gens[j]:
                return True
    return False


def certificate(decision: str, gens: list[set[str]], threshold: float = 0.99) -> dict[str, Any]:
    score = independence_score(gens)
    fp = false_plurality(gens)
    # graduated ablation: any single-root ablation that collapses corroboration
    roots = sorted({r for g in gens for r in g})
    ablation = []
    for r in roots:
        after = ablate(gens, r)
        ablation.append({
            "root": r,
            "before": len(gens),
            "after": len(after),
            "delta": len(gens) - len(after),
        })
    verdict = "FAIL" if fp or score < threshold else "PASS"
    if any(a["after"] == 0 for a in ablation) and len(gens) > 1:
        # if removing one root kills all paths — false plurality style FAIL
        if any(a["delta"] == len(gens) for a in ablation):
            verdict = "FAIL"
    return {
        "decision": decision,
        "corroboration_count": len(gens),
        "independence_score": score,
        "false_plurality_detected": fp,
        "ablation": ablation,
        "verdict": verdict,
    }


def pass_case() -> dict[str, Any]:
    gens = [{"R_sensor"}, {"R_inspect"}, {"R_sat"}]
    return certificate("SAFE_TO_OPERATE", gens)


def fail_case() -> dict[str, Any]:
    gens = [
        {"R_SHARED", "R_a"},
        {"R_SHARED", "R_b"},
        {"R_SHARED", "R_c"},
    ]
    return certificate("APPROVE_TRADE", gens)


def graph_style_reference() -> dict[str, Any]:
    """Reference matching set logic (simulates primary PoC verdicts)."""
    return {
        "pass": {"verdict": "PASS", "independence_score": 1.0, "false_plurality_detected": False},
        "fail": {"verdict": "FAIL", "independence_score": independence_score([{"R_SHARED"}, {"R_SHARED"}, {"R_SHARED"}]), "false_plurality_detected": True},
    }


def main() -> int:
    print("ROOTFALL Alternative Implementation (set-theoretic)")
    print(f"Author: {AUTHOR} ORCID {ORCID}")
    p = pass_case()
    f = fail_case()
    ref = graph_style_reference()
    agree = (
        p["verdict"] == ref["pass"]["verdict"]
        and f["verdict"] == ref["fail"]["verdict"]
        and f["false_plurality_detected"] is True
        and p["false_plurality_detected"] is False
    )
    evidence = {
        "framework": "ROOTFALL",
        "author": AUTHOR,
        "orcid": ORCID,
        "disclaimer": "PoC replication evidence only — not production",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "primary_style": "graph_path_ablation",
        "alternative_style": "set_theoretic_generating_sets",
        "pass_case": p,
        "fail_case": f,
        "reference": ref,
        "replication_pass": agree,
    }
    out = Path(__file__).resolve().parent / "rootfall_replication_evidence.json"
    out.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"PASS verdict={p['verdict']} score={p['independence_score']}")
    print(f"FAIL verdict={f['verdict']} fp={f['false_plurality_detected']}")
    print(f"Replication agree: {agree}")
    print(f"Evidence: {out}")
    return 0 if agree else 1


if __name__ == "__main__":
    sys.exit(main())
