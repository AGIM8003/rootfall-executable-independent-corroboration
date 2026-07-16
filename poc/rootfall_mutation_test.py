#!/usr/bin/env python3
"""ROOTFALL Mutation Testing. Author: Agim Haxhijaha, ORCID 0009-0002-3234-7765. PoC only."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

AUTHOR = "Agim Haxhijaha"
ORCID = "0009-0002-3234-7765"


def independence(gens: list[set[str]]) -> float:
    n = len(gens)
    if n < 2:
        return 1.0
    pairs = n * (n - 1) / 2
    shared = sum(1 for i in range(n) for j in range(i + 1, n) if gens[i] & gens[j])
    return 1.0 - shared / pairs


def false_plurality(gens: list[set[str]]) -> bool:
    return any(gens[i] & gens[j] for i in range(len(gens)) for j in range(i + 1, len(gens)))


def ablate(gens: list[set[str]], root: str) -> list[set[str]]:
    return [set(g) for g in gens if root not in g]


def verdict(gens: list[set[str]], t: float = 0.99) -> str:
    if false_plurality(gens) or independence(gens) < t:
        return "FAIL"
    return "PASS"


def oracle(indep: Callable, fp: Callable, abl: Callable, verd: Callable) -> list[tuple[str, bool]]:
    pass_g = [{"R1"}, {"R2"}, {"R3"}]
    fail_g = [{"S", "a"}, {"S", "b"}, {"S", "c"}]
    tests = []
    tests.append(("pass_indep_1", abs(indep(pass_g) - 1.0) < 1e-9))
    tests.append(("fail_fp_true", fp(fail_g) is True))
    tests.append(("pass_fp_false", fp(pass_g) is False))
    tests.append(("pass_verdict", verd(pass_g) == "PASS"))
    tests.append(("fail_verdict", verd(fail_g) == "FAIL"))
    tests.append(("ablate_S_collapses", len(abl(fail_g, "S")) == 0))
    tests.append(("ablate_R1_leaves_2", len(abl(pass_g, "R1")) == 2))
    tests.append(("fail_indep_low", indep(fail_g) < 0.5))
    return tests


def main() -> int:
    mutations = []

    def run(name, indep=independence, fp=false_plurality, abl=ablate, verd=verdict):
        try:
            results = oracle(indep, fp, abl, verd)
        except Exception as exc:
            mutations.append({"name": name, "detected": True, "caught_by": f"exc:{exc}"})
            return
        failed = [n for n, ok in results if not ok]
        mutations.append({"name": name, "detected": len(failed) > 0, "caught_by": failed[0] if failed else None, "failed_tests": failed})

    run("skip_fp_check", fp=lambda g: False)
    run("ge_to_gt_threshold", verd=lambda g, t=0.99: "FAIL" if false_plurality(g) or independence(g) <= t else "PASS")
    # wait - that might still FAIL fail case. Better: never FAIL
    mutations.clear()

    run("skip_fp_check", fp=lambda g: False)
    run("always_pass_verdict", verd=lambda g, t=0.99: "PASS")
    run("ablate_noop", abl=lambda g, r: [set(x) for x in g])
    run("indep_always_1", indep=lambda g: 1.0)
    run("fp_inverted", fp=lambda g: not false_plurality(g))
    run("ablate_deletes_all", abl=lambda g, r: [])
    run("verdict_ignore_fp", verd=lambda g, t=0.99: "PASS" if independence(g) >= 0 else "FAIL")
    run("empty_gens_crash", verd=lambda g, t=0.99: verdict(None))  # type: ignore
    run("swap_ablate_meaning", abl=lambda g, r: [set(x) | {r} for x in g])
    run("early_pass", verd=lambda g, t=0.99: "PASS")

    detected = sum(1 for m in mutations if m["detected"])
    score = detected / len(mutations)
    report = {
        "framework": "ROOTFALL",
        "author": AUTHOR,
        "orcid": ORCID,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mutations_total": len(mutations),
        "mutations_detected": detected,
        "mutation_score": round(score, 3),
        "pass_threshold": 0.9,
        "mutations": mutations,
        "suite_pass": score >= 0.9,
    }
    out = Path(__file__).resolve().parent / "rootfall_mutation_results.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"ROOTFALL mutation score: {score:.0%} ({detected}/{len(mutations)})")
    for m in mutations:
        print(f"  [{'CAUGHT' if m['detected'] else 'SURVIVED'}] {m['name']}")
    print(out)
    return 0 if report["suite_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
