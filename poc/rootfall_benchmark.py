#!/usr/bin/env python3
"""
ROOTFALL Benchmark Harness — Root Ablation Performance & Correctness

Author: Agim Haxhijaha, ORCID 0009-0002-3234-7765

DISCLAIMER: Proof-of-concept benchmark only. Not production validation.
Stdlib only. Reuses rootfall_gate.py and rootfall_poc.py logic.
"""

from __future__ import annotations

import json
import sys
import time
import tracemalloc
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from rootfall_gate import (
    build_deep_false_plurality_scenario,
    build_evasion_scenario,
    build_multi_decision_scenarios,
    build_pass_baseline,
    build_scale_scenario,
    gateway_permit,
    generate_rootfall_certificate,
    graduated_ablation_series,
    run_ablation_battery,
    verify_certificate_integrity,
)
from rootfall_poc import (
    build_fail_scenario,
    build_pass_scenario,
    generate_rootfall_certificate as poc_generate_certificate,
    run_ablation_battery as poc_run_ablation,
)

AUTHOR = "Agim Haxhijaha"
ORCID = "0009-0002-3234-7765"
DISCLAIMER = "PoC benchmark only — not production, not peer reviewed"
RESULTS_FILE = "rootfall_benchmark_results.json"


@dataclass
class ScenarioResult:
    name: str
    size: str
    expected_pass: bool
    actual_pass: bool
    execution_time_ms: float
    memory_bytes_peak: int
    details: dict[str, Any]


def _cert_verdict(scenario) -> str:
    ablation = run_ablation_battery(scenario)
    return generate_rootfall_certificate(scenario, ablation)["verdict"]


def _measure(
    name: str, size: str, expected_pass: bool, fn: Callable[[], tuple[bool, dict[str, Any]]]
) -> ScenarioResult:
    tracemalloc.start()
    t0 = time.perf_counter()
    actual_pass, details = fn()
    elapsed_ms = (time.perf_counter() - t0) * 1000
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return ScenarioResult(
        name=name, size=size, expected_pass=expected_pass, actual_pass=actual_pass,
        execution_time_ms=round(elapsed_ms, 3), memory_bytes_peak=peak, details=details,
    )


# --- 10 scenarios ---


def s01_pass_baseline() -> tuple[bool, dict[str, Any]]:
    sc = build_pass_baseline()
    v = _cert_verdict(sc)
    return v == "PASS", {"verdict": v, "paths": len(sc.paths)}


def s02_poc_pass() -> tuple[bool, dict[str, Any]]:
    sc = build_pass_scenario()
    cert = poc_generate_certificate(sc, poc_run_ablation(sc))
    return cert["verdict"] == "PASS", {"verdict": cert["verdict"], "independence": sc.compute_independence_score()}


def s03_poc_fail_detected() -> tuple[bool, dict[str, Any]]:
    sc = build_fail_scenario()
    cert = poc_generate_certificate(sc, poc_run_ablation(sc))
    detected = cert["false_plurality_detected"] and cert["verdict"] == "FAIL"
    return detected, {"verdict": cert["verdict"], "false_plurality": cert["false_plurality_detected"]}


def s04_deep_false_plurality() -> tuple[bool, dict[str, Any]]:
    sc = build_deep_false_plurality_scenario()
    deep = sc.detect_deep_shared_roots(4)
    cert = generate_rootfall_certificate(sc, run_ablation_battery(sc))
    return len(deep) > 0 and cert["false_plurality_detected"], {"deep_findings": len(deep), "verdict": cert["verdict"]}


def s05_evasion_laundering() -> tuple[bool, dict[str, Any]]:
    sc = build_evasion_scenario()
    laundered = sc.detect_laundered_origins()
    cert = generate_rootfall_certificate(sc, run_ablation_battery(sc))
    return len(laundered) >= 2 and cert["verdict"] == "FAIL", {"laundered_pairs": len(laundered)}


def s06_certificate_integrity() -> tuple[bool, dict[str, Any]]:
    sc = build_pass_baseline()
    cert = generate_rootfall_certificate(sc, run_ablation_battery(sc))
    valid = verify_certificate_integrity(cert)
    tampered = dict(cert)
    tampered["corroboration_count"] = 999
    invalid = not verify_certificate_integrity(tampered)
    return valid and invalid, {"original_valid": valid}


def s07_gateway_permit() -> tuple[bool, dict[str, Any]]:
    sc = build_pass_baseline()
    cert = generate_rootfall_certificate(sc, run_ablation_battery(sc))
    permit = gateway_permit(cert, sc.action_digest)
    return permit["permitted"], {"reason": permit["reason"]}


def s08_scale_scenario() -> tuple[bool, dict[str, Any]]:
    sc = build_scale_scenario()
    ok = len(sc.paths) >= 10 and len(sc.artifacts) >= 50 and len(sc.roots) >= 20
    cert = generate_rootfall_certificate(sc, run_ablation_battery(sc))
    return ok and cert["independence_score"] >= 0.67, {
        "paths": len(sc.paths), "artifacts": len(sc.artifacts), "roots": len(sc.roots),
    }


def s09_graduated_ablation() -> tuple[bool, dict[str, Any]]:
    sc = build_scale_scenario()
    series = graduated_ablation_series(sc)
    monotonic = all(s["corroboration_after"] <= s["corroboration_before"] for s in series)
    degrades = any(s["delta_corroboration"] > 0 for s in series)
    return monotonic and degrades and len(series) >= 5, {"steps": len(series)}


def s10_multi_decision() -> tuple[bool, dict[str, Any]]:
    scenarios = build_multi_decision_scenarios()
    certs = [generate_rootfall_certificate(sc, run_ablation_battery(sc)) for sc in scenarios]
    all_pass = all(c["verdict"] == "PASS" for c in certs)
    isolated = len({c["action_digest"] for c in certs}) == 5
    return all_pass and isolated, {"decisions": len(certs), "all_pass": all_pass}


SCENARIOS = [
    ("pass_baseline_3_paths", "small", True, s01_pass_baseline),
    ("poc_independent_pass", "small", True, s02_poc_pass),
    ("poc_false_plurality_fail", "small", True, s03_poc_fail_detected),
    ("deep_shared_root_detection", "medium", True, s04_deep_false_plurality),
    ("evasion_laundering_detection", "medium", True, s05_evasion_laundering),
    ("certificate_tamper_detection", "medium", True, s06_certificate_integrity),
    ("gateway_permit_valid_cert", "medium", True, s07_gateway_permit),
    ("scale_10_paths_50_artifacts", "large", True, s08_scale_scenario),
    ("graduated_ablation_series", "large", True, s09_graduated_ablation),
    ("multi_decision_isolation", "large", True, s10_multi_decision),
]


def compute_rates(results: list[ScenarioResult]) -> dict[str, float]:
    total = len(results)
    correct = sum(1 for r in results if r.expected_pass == r.actual_pass)
    fp = sum(1 for r in results if not r.expected_pass and r.actual_pass)
    fn = sum(1 for r in results if r.expected_pass and not r.actual_pass)
    neg = sum(1 for r in results if not r.expected_pass)
    pos = sum(1 for r in results if r.expected_pass)
    return {
        "correctness_rate": round(correct / total, 4) if total else 0.0,
        "false_positive_rate": round(fp / neg, 4) if neg else 0.0,
        "false_negative_rate": round(fn / pos, 4) if pos else 0.0,
        "correct": correct, "false_positives": fp, "false_negatives": fn, "total": total,
    }


def scalability_projection(results: list[ScenarioResult]) -> dict[str, Any]:
    large = [r for r in results if r.size == "large"]
    base_ms = sum(r.execution_time_ms for r in large) / max(len(large), 1)
    base_paths = 10
    return {
        "baseline_ms": round(base_ms, 3),
        "baseline_reference": "mean of large scenarios",
        "assumption": "linear O(n) extrapolation over corroboration paths",
        "projections": {
            "10x": round(base_ms * 10, 3),
            "100x": round(base_ms * 100, 3),
            "1000x": round(base_ms * 1000, 3),
        },
        "projected_paths": {"10x": base_paths * 10, "100x": base_paths * 100, "1000x": base_paths * 1000},
    }


def run_benchmark() -> dict[str, Any]:
    results = [_measure(name, size, exp, fn) for name, size, exp, fn in SCENARIOS]
    rates = compute_rates(results)
    scale = scalability_projection(results)
    by_size = {}
    for sz in ("small", "medium", "large"):
        subset = [r for r in results if r.size == sz]
        if subset:
            by_size[sz] = {
                "count": len(subset),
                "mean_time_ms": round(sum(r.execution_time_ms for r in subset) / len(subset), 3),
                "mean_memory_kb": round(sum(r.memory_bytes_peak for r in subset) / len(subset) / 1024, 2),
            }
    return {
        "framework": "ROOTFALL",
        "harness": "rootfall_benchmark",
        "author": AUTHOR,
        "orcid": ORCID,
        "disclaimer": DISCLAIMER,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "scenarios": [
            {
                "name": r.name, "size": r.size, "expected_pass": r.expected_pass,
                "actual_pass": r.actual_pass, "correct": r.expected_pass == r.actual_pass,
                "execution_time_ms": r.execution_time_ms, "memory_bytes_peak": r.memory_bytes_peak,
                "memory_kb_peak": round(r.memory_bytes_peak / 1024, 2), "details": r.details,
            }
            for r in results
        ],
        "metrics": rates,
        "by_size": by_size,
        "scalability_projection": scale,
        "memory_profile": {
            "largest_scenario": max(results, key=lambda r: r.memory_bytes_peak).name,
            "peak_memory_bytes": max(r.memory_bytes_peak for r in results),
            "peak_memory_kb": round(max(r.memory_bytes_peak for r in results) / 1024, 2),
        },
    }


def print_summary(report: dict[str, Any]) -> None:
    m, s = report["metrics"], report["scalability_projection"]
    print("\n" + "=" * 72)
    print("ROOTFALL BENCHMARK SUMMARY")
    print("=" * 72)
    print(f"{'SCENARIO':<42} {'SIZE':<8} {'PASS':<6} {'TIME(ms)':>10} {'MEM(KB)':>10}")
    print("-" * 72)
    for sc in report["scenarios"]:
        mark = "OK" if sc["correct"] else "MISS"
        print(f"{sc['name']:<42} {sc['size']:<8} {mark:<6} {sc['execution_time_ms']:>10.1f} {sc['memory_kb_peak']:>10.1f}")
    print("-" * 72)
    print(f"Correctness rate    : {m['correctness_rate']:.1%} ({m['correct']}/{m['total']})")
    print(f"False positive rate : {m['false_positive_rate']:.1%}")
    print(f"False negative rate : {m['false_negative_rate']:.1%}")
    print(f"\nScalability (baseline {s['baseline_ms']:.1f} ms):")
    for factor in ("10x", "100x", "1000x"):
        proj = s["projections"][factor]
        paths = s["projected_paths"][factor]
        print(f"  {factor:>5} (~{paths} paths): {proj:,.1f} ms ({proj / 1000:.2f} s)")
    print("=" * 72)


def main() -> int:
    print("ROOTFALL Benchmark Harness")
    print(f"Author: {AUTHOR} (ORCID {ORCID})")
    print(DISCLAIMER)
    report = run_benchmark()
    print_summary(report)
    out_path = Path(__file__).resolve().parent / RESULTS_FILE
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    print(f"\nResults written to: {out_path}")
    return 0 if report["metrics"]["correctness_rate"] == 1.0 else 1


if __name__ == "__main__":
    sys.exit(main())
