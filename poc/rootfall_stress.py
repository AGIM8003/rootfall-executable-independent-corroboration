#!/usr/bin/env python3
"""
ROOTFALL Stress-Scale Test — 100 paths, 500 evidence items, 50 root origins.

Author: Agim Haxhijaha, ORCID 0009-0002-3234-7765
"""

from __future__ import annotations

import json
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rootfall_poc import (
    DecisionPath,
    DecisionScenario,
    EvidenceRoot,
    generate_rootfall_certificate,
)

AUTHOR = "Agim Haxhijaha"
ORCID = "0009-0002-3234-7765"
OUT = Path(__file__).with_name("rootfall_stress_results.json")

BASE = {"paths": 100, "evidence_items": 500, "roots": 50}


def build_scale(n_paths: int, n_evidence: int, n_roots: int) -> DecisionScenario:
    roots: dict[str, EvidenceRoot] = {}
    for i in range(n_roots):
        rid = f"R_{i:03d}"
        roots[rid] = EvidenceRoot(rid, "synth", f"root origin {i}", 0.5 + (i % 50) / 100)

    # Extra evidence items registered as roots for inventory scale
    for i in range(n_roots, n_evidence):
        rid = f"E_{i:03d}"
        roots[rid] = EvidenceRoot(rid, "evidence", f"evidence item {i}", 0.5)

    decision = "STRESS_DECISION_APPROVE"
    paths: list[DecisionPath] = []
    for p in range(n_paths):
        # Inject controlled false plurality: every 5th path shares R_000
        root_ids = [f"R_{p % n_roots:03d}", f"R_{(p*3) % n_roots:03d}"]
        if p % 5 == 0:
            root_ids.append("R_000")
        # Attach some evidence ids as path roots for scale
        root_ids.append(f"E_{(n_roots + (p % max(1, n_evidence - n_roots))):03d}")
        paths.append(
            DecisionPath(
                path_id=f"P_{p:03d}",
                label=f"path_{p}",
                root_ids=root_ids,
                intermediate_steps=["s1", "s2", "s3"],
                conclusion=decision,
            )
        )

    return DecisionScenario(
        scenario_id=f"stress_{n_paths}_{n_evidence}_{n_roots}",
        description="stress-scale false plurality scenario",
        decision=decision,
        action_digest="stress:approve",
        paths=paths,
        roots=roots,
    )


def ablate_root_fast(scenario: DecisionScenario, root_id: str) -> dict[str, Any]:
    """Ablation without O(survivors²) independence recompute (stress-scale)."""
    affected_paths: list[str] = []
    surviving_paths: list[str] = []
    surviving_conclusions: set[str] = set()
    for path in scenario.paths:
        if root_id in path.root_ids:
            affected_paths.append(path.path_id)
        else:
            surviving_paths.append(path.path_id)
            surviving_conclusions.add(path.conclusion)
    decision_survives = scenario.decision in surviving_conclusions and len(surviving_paths) > 0
    return {
        "ablated_root": root_id,
        "affected_paths": affected_paths,
        "surviving_paths": surviving_paths,
        "decision_survives": decision_survives,
        "surviving_independence": None,  # skipped at stress scale
        "remaining_corroboration": len(surviving_paths),
    }


def run_ablation_primary_roots(scenario: DecisionScenario, n_roots: int) -> list[dict[str, Any]]:
    """Ablate the primary root origins only (not every secondary evidence id)."""
    return [ablate_root_fast(scenario, f"R_{i:03d}") for i in range(n_roots)]


def fast_independence(paths: list[DecisionPath]) -> float:
    """Independence using frozensets — same formula as PoC."""
    n = len(paths)
    if n < 2:
        return 1.0
    sets = [frozenset(p.root_ids) for p in paths]
    total_pairs = n * (n - 1) / 2
    shared_pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            if sets[i] & sets[j]:
                shared_pairs += 1
    return round(1.0 - (shared_pairs / total_pairs), 4)


def run_once(n_paths: int, n_evidence: int, n_roots: int) -> dict[str, Any]:
    tracemalloc.start()
    t0 = time.perf_counter()
    scenario = build_scale(n_paths, n_evidence, n_roots)
    t_build = time.perf_counter() - t0

    t1 = time.perf_counter()
    indep = fast_independence(scenario.paths)
    hidden = scenario.detect_hidden_shared_roots()
    t_indep = time.perf_counter() - t1

    t2 = time.perf_counter()
    ablation = run_ablation_primary_roots(scenario, n_roots)
    t_ablation = time.perf_counter() - t2

    t3 = time.perf_counter()
    # Certificate uses PoC independence again — temporarily patch score via thin wrapper
    # Avoid double O(n²) inside certificate by pre-filtering: call generate with ablation only
    # after setting a cached independence via monkeypatch of method
    original = scenario.compute_independence_score
    scenario.compute_independence_score = lambda: indep  # type: ignore[method-assign]
    cert = generate_rootfall_certificate(scenario, ablation)
    scenario.compute_independence_score = original  # type: ignore[method-assign]
    t_cert = time.perf_counter() - t3

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    total = time.perf_counter() - t0

    return {
        "scale": {"paths": n_paths, "evidence_items": n_evidence, "roots": n_roots},
        "timing_s": {
            "build": round(t_build, 6),
            "independence_and_hidden": round(t_indep, 6),
            "ablation_battery": round(t_ablation, 6),
            "certificate": round(t_cert, 6),
            "total": round(total, 6),
            "per_root_ablation_ms": round(1000 * t_ablation / max(n_roots, 1), 6),
        },
        "memory": {
            "current_bytes": current,
            "peak_bytes": peak,
            "peak_mb": round(peak / (1024 * 1024), 4),
        },
        "results": {
            "independence_score": indep,
            "hidden_shared_roots": len(hidden),
            "ablation_runs": len(ablation),
            "verdict": cert.get("verdict", cert.get("status")),
        },
    }


def main() -> int:
    curve = []
    for m in [1, 2, 5, 10]:
        n_paths = BASE["paths"] * m
        n_evidence = BASE["evidence_items"] * m
        n_roots = BASE["roots"] * m
        print(f"ROOTFALL stress {m}x paths={n_paths} evidence={n_evidence} roots={n_roots}", flush=True)
        row = run_once(n_paths, n_evidence, n_roots)
        row["multiplier"] = m
        curve.append(row)
        print(f"  total={row['timing_s']['total']}s peak_mb={row['memory']['peak_mb']}", flush=True)

    base_t = curve[0]["timing_s"]
    ops = ["build", "independence_and_hidden", "ablation_battery", "certificate"]
    bottleneck = max(ops, key=lambda k: base_t[k])
    growth = {
        op: [
            {
                "multiplier": r["multiplier"],
                "seconds": r["timing_s"][op],
                "vs_1x": round(r["timing_s"][op] / max(base_t[op], 1e-9), 3),
            }
            for r in curve
        ]
        for op in ops
    }

    out = {
        "framework": "ROOTFALL",
        "script": "rootfall_stress.py",
        "author": AUTHOR,
        "orcid": ORCID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_target": BASE,
        "scalability_curve": curve,
        "bottleneck_operation": bottleneck,
        "bottleneck_rationale": (
            f"Pairwise independence / ablation battery scales with paths×roots; "
            f"dominant op at 1× is '{bottleneck}'."
        ),
        "growth_by_operation": growth,
        "pass": all(r["results"]["ablation_runs"] > 0 for r in curve) and len(curve) == 4,
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"bottleneck={bottleneck} pass={out['pass']}")
    print(f"Wrote {OUT.name}")
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
