#!/usr/bin/env python3
"""ROOTFALL public API integration tests."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from rootfall import ROOTFALLEngine

OUT = Path(__file__).with_name("rootfall_integration_results.json")


def run() -> dict:
    results = []

    e = ROOTFALLEngine()
    r = e.attest()
    results.append({"name": "empty_input", "pass": r.verdict == "PASS" and r.corroboration_count == 0})

    e = ROOTFALLEngine(decision="OK")
    e.add_root("R1", description="only")
    e.add_path("P1", root_ids=["R1"], conclusion="OK")
    r = e.attest()
    results.append({"name": "single_path", "pass": r.corroboration_count == 1})

    e = ROOTFALLEngine(decision="UPGRADE")
    e.add_root("shared")
    e.add_root("a")
    e.add_root("b")
    e.add_path("p1", root_ids=["shared", "a"])
    e.add_path("p2", root_ids=["shared", "b"])
    r = e.attest()
    results.append({"name": "typical_false_plurality", "pass": r.verdict == "FAIL" and r.false_plurality_detected})

    e = ROOTFALLEngine(decision="GO")
    for i in range(120):
        e.add_root(f"R{i}")
    for i in range(100):
        e.add_path(f"P{i}", root_ids=[f"R{i}", f"R{(i+1)%120}"], conclusion="GO")
    r = e.attest()
    results.append({"name": "large_scale_100_paths", "pass": r.corroboration_count == 100})

    ok_err = True
    e = ROOTFALLEngine()
    e.add_root("R1")
    try:
        e.add_root("R1")
        ok_err = False
    except ValueError:
        pass
    try:
        e.add_path("P1", root_ids=["missing"])
        ok_err = False
    except ValueError:
        pass
    results.append({"name": "error_handling", "pass": ok_err})

    e = ROOTFALLEngine(decision="SAFE")
    e.add_root("R1")
    e.add_root("R2")
    e.add_root("R3")
    e.add_path("P1", root_ids=["R1"], conclusion="SAFE")
    e.add_path("P2", root_ids=["R2"], conclusion="SAFE")
    e.add_path("P3", root_ids=["R3"], conclusion="SAFE")
    r = e.attest()
    results.append({
        "name": "genuinely_independent",
        "pass": r.verdict == "PASS" and not r.false_plurality_detected and r.independence_score == 1.0,
    })

    return {
        "framework": "ROOTFALL",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "pass": all(x["pass"] for x in results),
    }


def main() -> int:
    evidence = run()
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"ROOTFALL integration pass={evidence['pass']}")
    return 0 if evidence["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
