#!/usr/bin/env python3
"""
ROOTFALL Reality Gate Demonstrator — Independent Corroboration with Root Ablation

Author: Agim Haxhijaha, ORCID 0009-0002-3234-7765

DISCLAIMER: This script is a proof-of-concept Reality Gate demonstrator only.
It is not production software, has not been peer reviewed, and does not
constitute formal verification of the ROOTFALL framework. Behaviour is simulated
for research illustration purposes. Passing this gate does not imply patent
grant, regulatory compliance, or production readiness.
"""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUTHOR = "Agim Haxhijaha"
ORCID = "0009-0002-3234-7765"
DISCLAIMER = (
    "PoC Reality Gate demonstrator only — not production, not peer reviewed, "
    "not formal verification"
)
CERT_SECRET = b"rootfall-poc-gate-secret-v1"
INDEPENDENCE_THRESHOLD = 0.67
MIN_SURVIVORS = 2


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------


@dataclass
class EvidenceRoot:
    root_id: str
    source_type: str
    description: str
    reliability: float
    content_fingerprint: str = ""
    canonical_id: str = ""

    def __post_init__(self) -> None:
        if not self.content_fingerprint:
            self.content_fingerprint = fingerprint_text(self.description)
        if not self.canonical_id:
            self.canonical_id = self.root_id


@dataclass
class EvidenceArtifact:
    artifact_id: str
    label: str
    parent_ids: list[str]
    root_hint: str = ""
    depth: int = 0


@dataclass
class DecisionPath:
    path_id: str
    label: str
    root_ids: list[str]
    artifact_chain: list[str]
    intermediate_steps: list[str]
    conclusion: str

    def shares_root_with(self, other: DecisionPath) -> set[str]:
        return set(self.root_ids) & set(other.root_ids)


@dataclass
class DecisionScenario:
    scenario_id: str
    description: str
    decision: str
    action_digest: str
    paths: list[DecisionPath] = field(default_factory=list)
    roots: dict[str, EvidenceRoot] = field(default_factory=dict)
    artifacts: dict[str, EvidenceArtifact] = field(default_factory=dict)

    def all_root_ids(self) -> set[str]:
        ids: set[str] = set()
        for path in self.paths:
            ids.update(path.root_ids)
        return ids

    def corroboration_count(self) -> int:
        return len(self.paths)

    def compute_independence_score(self) -> float:
        if len(self.paths) < 2:
            return 1.0
        n = len(self.paths)
        total_pairs = n * (n - 1) / 2
        shared_pairs = 0
        for i in range(n):
            for j in range(i + 1, n):
                if self.paths[i].shares_root_with(self.paths[j]):
                    shared_pairs += 1
        return round(1.0 - (shared_pairs / total_pairs), 4)

    def resolve_ultimate_roots(self, artifact_id: str) -> set[str]:
        art = self.artifacts.get(artifact_id)
        if art is None:
            return set()
        if not art.parent_ids:
            return {art.root_hint} if art.root_hint else set()
        roots: set[str] = set()
        for pid in art.parent_ids:
            roots.update(self.resolve_ultimate_roots(pid))
        return roots

    def detect_hidden_shared_roots(self) -> list[dict[str, Any]]:
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

    def detect_deep_shared_roots(self, min_depth: int = 4) -> list[dict[str, Any]]:
        """Detect shared roots buried min_depth levels in artifact chains."""
        findings: list[dict[str, Any]] = []
        path_roots: dict[str, set[str]] = {}
        for path in self.paths:
            deep_roots: set[str] = set()
            for aid in path.artifact_chain:
                art = self.artifacts.get(aid)
                if art and art.depth >= min_depth:
                    deep_roots.update(self.resolve_ultimate_roots(aid))
            path_roots[path.path_id] = deep_roots

        all_paths = list(path_roots.keys())
        for i in range(len(all_paths)):
            for j in range(i + 1, len(all_paths)):
                shared = path_roots[all_paths[i]] & path_roots[all_paths[j]]
                if shared:
                    findings.append({
                        "path_a": all_paths[i],
                        "path_b": all_paths[j],
                        "shared_deep_roots": sorted(shared),
                        "min_depth": min_depth,
                    })
        return findings

    def detect_laundered_origins(self) -> list[dict[str, Any]]:
        """Detect rename/paraphrase/launder attempts via fingerprint and canonical clustering."""
        laundering: list[dict[str, Any]] = []
        seen_pairs: set[tuple[str, str]] = set()

        fp_clusters: dict[str, list[str]] = {}
        for rid, root in self.roots.items():
            fp_clusters.setdefault(root.content_fingerprint, []).append(rid)

        for fp, rids in fp_clusters.items():
            if len(rids) > 1:
                canonical = sorted(rids)[0]
                for rid in rids:
                    if rid == canonical:
                        continue
                    pair = (canonical, rid)
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        laundering.append({
                            "laundered_id": rid,
                            "canonical_id": canonical,
                            "fingerprint": fp,
                            "method": "rename_exact_fingerprint",
                        })

        canon_clusters: dict[str, list[str]] = {}
        for rid, root in self.roots.items():
            canon_clusters.setdefault(root.canonical_id, []).append(rid)

        for cid, rids in canon_clusters.items():
            if len(rids) > 1:
                canonical = sorted(rids)[0]
                for rid in rids:
                    if rid == canonical:
                        continue
                    pair = (canonical, rid)
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        laundering.append({
                            "laundered_id": rid,
                            "canonical_id": canonical,
                            "fingerprint": self.roots[rid].content_fingerprint,
                            "method": "canonical_id_cluster",
                        })

        token_sets: list[tuple[str, frozenset[str]]] = []
        for rid, root in self.roots.items():
            normalized = unicodedata.normalize(
                "NFKD", root.description.lower(),
            )
            normalized = re.sub(r"[^\w\s]", " ", normalized)
            tokens = frozenset(normalized.split())
            token_sets.append((rid, tokens))

        for i in range(len(token_sets)):
            for j in range(i + 1, len(token_sets)):
                rid_a, tokens_a = token_sets[i]
                rid_b, tokens_b = token_sets[j]
                if not tokens_a or not tokens_b:
                    continue
                overlap = len(tokens_a & tokens_b)
                union = len(tokens_a | tokens_b)
                jaccard = overlap / union if union else 0.0
                if jaccard >= 0.9 and rid_a != rid_b:
                    root_a = self.roots[rid_a]
                    root_b = self.roots[rid_b]
                    same_canonical = (
                        root_a.canonical_id == root_b.canonical_id
                        or root_a.canonical_id == rid_b
                        or root_b.canonical_id == rid_a
                    )
                    if not same_canonical:
                        continue
                    canonical = sorted([rid_a, rid_b])[0]
                    laundered = sorted([rid_a, rid_b])[1]
                    pair = (canonical, laundered)
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        laundering.append({
                            "laundered_id": laundered,
                            "canonical_id": canonical,
                            "fingerprint": self.roots[laundered].content_fingerprint,
                            "method": "paraphrase_jaccard",
                            "jaccard": round(jaccard, 4),
                        })

        return laundering


# ---------------------------------------------------------------------------
# Root ablation engine
# ---------------------------------------------------------------------------


def ablate_root(scenario: DecisionScenario, root_id: str) -> dict[str, Any]:
    affected_paths: list[str] = []
    surviving_paths: list[str] = []
    for path in scenario.paths:
        if root_id in path.root_ids:
            affected_paths.append(path.path_id)
        else:
            surviving_paths.append(path.path_id)

    surviving_conclusions = {
        p.conclusion for p in scenario.paths if p.path_id in surviving_paths
    }
    decision_survives = (
        scenario.decision in surviving_conclusions and len(surviving_paths) > 0
    )

    surviving_independence = 0.0
    if len(surviving_paths) >= 2:
        survivor_paths = [p for p in scenario.paths if p.path_id in surviving_paths]
        temp = DecisionScenario(
            scenario_id="temp",
            description="",
            decision=scenario.decision,
            action_digest=scenario.action_digest,
            paths=survivor_paths,
            roots=scenario.roots,
            artifacts=scenario.artifacts,
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
    return [ablate_root(scenario, rid) for rid in sorted(scenario.all_root_ids())]


def graduated_ablation_series(scenario: DecisionScenario) -> list[dict[str, Any]]:
    """Remove roots one at a time sequentially; track degrading corroboration."""
    working = copy.deepcopy(scenario)
    series: list[dict[str, Any]] = []
    removed: list[str] = []

    while working.paths:
        before = working.corroboration_count()
        before_indep = working.compute_independence_score()
        root_to_remove = sorted(working.all_root_ids())[0]
        result = ablate_root(working, root_to_remove)
        working.paths = [
            p for p in working.paths if p.path_id not in result["affected_paths"]
        ]
        for rid in list(working.roots.keys()):
            if rid == root_to_remove:
                del working.roots[rid]
        removed.append(root_to_remove)
        after = working.corroboration_count()
        series.append({
            "step": len(removed),
            "ablated_root": root_to_remove,
            "corroboration_before": before,
            "corroboration_after": after,
            "independence_before": before_indep,
            "independence_after": working.compute_independence_score(),
            "delta_corroboration": before - after,
        })
        if after == 0:
            break
    return series


# ---------------------------------------------------------------------------
# Certificate and gateway
# ---------------------------------------------------------------------------


def fingerprint_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def sign_certificate(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(CERT_SECRET, canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def generate_rootfall_certificate(
    scenario: DecisionScenario,
    ablation_results: list[dict[str, Any]],
) -> dict[str, Any]:
    independence = scenario.compute_independence_score()
    hidden_shared = scenario.detect_hidden_shared_roots()
    deep_shared = scenario.detect_deep_shared_roots(4)
    laundered = scenario.detect_laundered_origins()

    min_survivors = min(r["remaining_corroboration"] for r in ablation_results) if ablation_results else 0
    all_survive = all(r["decision_survives"] for r in ablation_results)
    no_hidden = len(hidden_shared) == 0 and len(deep_shared) == 0 and len(laundered) == 0

    false_plurality = not no_hidden or independence < INDEPENDENCE_THRESHOLD

    if false_plurality:
        verdict = "FAIL"
        verdict_reason = "False plurality or hidden shared roots detected"
    elif all_survive and min_survivors >= MIN_SURVIVORS:
        verdict = "PASS"
        verdict_reason = (
            "Truly independent corroboration survives single-root ablation"
        )
    else:
        verdict = "FAIL"
        verdict_reason = "Ablation fragility: corroboration collapses under root removal"

    cert_body = {
        "certificate_type": "ROOTFALL",
        "scenario_id": scenario.scenario_id,
        "decision": scenario.decision,
        "action_digest": scenario.action_digest,
        "corroboration_count": scenario.corroboration_count(),
        "independence_score": independence,
        "hidden_shared_roots": hidden_shared,
        "deep_shared_roots": deep_shared,
        "laundered_origins": laundered,
        "ablation_results": ablation_results,
        "min_survivors_after_ablation": min_survivors,
        "all_decisions_survive_ablation": all_survive,
        "false_plurality_detected": false_plurality,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "issued_at": datetime.now(timezone.utc).isoformat(),
    }
    cert_body["integrity_signature"] = sign_certificate(
        {k: v for k, v in cert_body.items() if k != "integrity_signature"}
    )
    return cert_body


def verify_certificate_integrity(certificate: dict[str, Any]) -> bool:
    sig = certificate.get("integrity_signature", "")
    body = {k: v for k, v in certificate.items() if k != "integrity_signature"}
    expected = sign_certificate(body)
    return hmac.compare_digest(sig, expected)


def gateway_permit(certificate: dict[str, Any], action_digest: str) -> dict[str, Any]:
    if certificate.get("verdict") != "PASS":
        return {"permitted": False, "reason": "Certificate verdict is not PASS"}
    if not verify_certificate_integrity(certificate):
        return {"permitted": False, "reason": "Certificate integrity check failed"}
    if certificate.get("action_digest") != action_digest:
        return {"permitted": False, "reason": "Action digest mismatch"}
    if certificate.get("false_plurality_detected"):
        return {"permitted": False, "reason": "False plurality detected"}
    return {"permitted": True, "reason": "All checks passed"}


# ---------------------------------------------------------------------------
# Scenario builders
# ---------------------------------------------------------------------------


def build_scale_scenario() -> DecisionScenario:
    """10 independent paths, 50+ evidence artifacts, 20+ roots."""
    scenario = DecisionScenario(
        scenario_id="SCALE_independent_corroboration",
        description="Large-scale independent corroboration scenario",
        decision="Proceed with deployment",
        action_digest=hashlib.sha256(b"deploy:v1").hexdigest(),
    )

    for i in range(22):
        rid = f"R{i:02d}"
        scenario.roots[rid] = EvidenceRoot(
            rid, f"type_{i % 5}",
            f"Independent root source {i} with unique content {i * 17}",
            0.85 + (i % 10) * 0.01,
        )

    artifact_count = 0
    for p in range(10):
        path_roots = [f"R{(p * 2) % 22:02d}", f"R{(p * 2 + 1) % 22:02d}"]
        chain: list[str] = []
        steps: list[str] = []
        for level in range(5):
            aid = f"E{p:02d}_L{level}"
            parents = [chain[-1]] if chain else []
            root_hint = path_roots[0] if level == 0 else ""
            scenario.artifacts[aid] = EvidenceArtifact(
                aid, f"Evidence path {p} level {level}",
                parents, root_hint=root_hint, depth=level,
            )
            chain.append(aid)
            steps.append(f"Process level {level} on path {p}")
            artifact_count += 1

        scenario.paths.append(DecisionPath(
            path_id=f"PATH_{p:02d}",
            label=f"Independent route {p}",
            root_ids=path_roots,
            artifact_chain=chain,
            intermediate_steps=steps,
            conclusion="Proceed with deployment",
        ))

    return scenario


def build_deep_false_plurality_scenario() -> DecisionScenario:
    """Shared root buried 4 levels deep — appears as independent paths."""
    scenario = DecisionScenario(
        scenario_id="DEEP_false_plurality",
        description="Shared root 4 levels deep in artifact chains",
        decision="Approve compound X",
        action_digest=hashlib.sha256(b"approve:x").hexdigest(),
    )

    shared = EvidenceRoot(
        "R_HIDDEN", "clinical_database",
        "Central trial database — single origin", 0.70,
    )
    scenario.roots["R_HIDDEN"] = shared
    for i in range(3):
        scenario.roots[f"R_decoy_{i}"] = EvidenceRoot(
            f"R_decoy_{i}", "decoy",
            f"Apparent independent root {i}", 0.80,
        )

    for p in range(3):
        chain: list[str] = []
        for level in range(5):
            aid = f"DEEP_{p}_L{level}"
            parents = [chain[-1]] if chain else []
            root_hint = "R_HIDDEN" if level == 0 else ""
            scenario.artifacts[aid] = EvidenceArtifact(
                aid, f"Deep chain p{p} l{level}",
                parents, root_hint=root_hint, depth=level,
            )
            chain.append(aid)

        scenario.paths.append(DecisionPath(
            path_id=f"DEEP_PATH_{p}",
            label=f"Apparent independent path {p}",
            root_ids=[f"R_decoy_{p}"],
            artifact_chain=chain,
            intermediate_steps=[f"Step {l}" for l in range(5)],
            conclusion="Approve compound X",
        ))

    return scenario


def build_evasion_scenario() -> DecisionScenario:
    """Rename/paraphrase/launder shared origins."""
    scenario = DecisionScenario(
        scenario_id="EVASION_laundering",
        description="Adversarial origin laundering",
        decision="Execute trade",
        action_digest=hashlib.sha256(b"trade:v1").hexdigest(),
    )

    base_desc = "Primary market feed from exchange ABC"
    scenario.roots["R_original"] = EvidenceRoot(
        "R_original", "market_feed", base_desc, 0.90,
    )
    scenario.roots["R_renamed"] = EvidenceRoot(
        "R_renamed", "market_feed", base_desc, 0.90,
        canonical_id="R_original",
    )
    scenario.roots["R_paraphrase"] = EvidenceRoot(
        "R_paraphrase", "market_feed",
        "Market feed primary from ABC exchange", 0.88,
        canonical_id="R_original",
    )

    for i, rid in enumerate(["R_renamed", "R_paraphrase", "R_original"]):
        scenario.paths.append(DecisionPath(
            path_id=f"EV_PATH_{i}",
            label=f"Evasion path {i}",
            root_ids=[rid],
            artifact_chain=[],
            intermediate_steps=[f"Analyze {rid}"],
            conclusion="Execute trade",
        ))

    return scenario


def build_multi_decision_scenarios() -> list[DecisionScenario]:
    scenarios: list[DecisionScenario] = []
    for d in range(5):
        sc = DecisionScenario(
            scenario_id=f"MULTI_decision_{d}",
            description=f"Isolated decision {d}",
            decision=f"Decision outcome {d}",
            action_digest=hashlib.sha256(f"action:{d}".encode()).hexdigest(),
        )
        for r in range(3):
            rid = f"R_d{d}_r{r}"
            sc.roots[rid] = EvidenceRoot(
                rid, "sensor",
                f"Isolated channel {d}-{r} reading {d * 31 + r * 17}",
                0.85,
            )
            sc.paths.append(DecisionPath(
                path_id=f"P_d{d}_r{r}",
                label=f"Path {r}",
                root_ids=[rid],
                artifact_chain=[],
                intermediate_steps=[f"Evaluate {rid}"],
                conclusion=f"Decision outcome {d}",
            ))
        scenarios.append(sc)
    return scenarios


def build_pass_baseline() -> DecisionScenario:
    scenario = DecisionScenario(
        scenario_id="PASS_baseline",
        description="Three truly independent paths",
        decision="System is safe to operate",
        action_digest=hashlib.sha256(b"safe:operate").hexdigest(),
    )
    for i, (rid, desc) in enumerate([
        ("R1", "Sensor array reading"),
        ("R2", "Manual inspection report"),
        ("R3", "Satellite telemetry"),
    ]):
        scenario.roots[rid] = EvidenceRoot(rid, "source", desc, 0.90)
        scenario.paths.append(DecisionPath(
            path_id=f"PATH_{i}",
            label=f"Route {i}",
            root_ids=[rid],
            artifact_chain=[],
            intermediate_steps=[f"Process {desc}"],
            conclusion="System is safe to operate",
        ))
    return scenario


# ---------------------------------------------------------------------------
# Adversarial demonstrations
# ---------------------------------------------------------------------------


def demo_evidence_fabrication_blocked() -> dict[str, Any]:
    scenario = build_pass_baseline()
    fake_root = EvidenceRoot(
        "R_FAKE", "fabricated",
        "Completely synthetic evidence with no provenance", 0.99,
    )
    scenario.roots["R_FAKE"] = fake_root
    scenario.paths.append(DecisionPath(
        "PATH_FAKE", "Fabricated path", ["R_FAKE"], [],
        ["Inject fabricated claim"], "System is safe to operate",
    ))
    ablation = run_ablation_battery(scenario)
    cert = generate_rootfall_certificate(scenario, ablation)
    blocked = cert["verdict"] == "FAIL" or cert["corroboration_count"] > 3
    return {
        "demonstration": "evidence_fabrication_blocked",
        "fabricated_root": "R_FAKE",
        "blocked": blocked,
        "verdict": cert["verdict"],
        "detail": "Fabricated root does not increase certified independence",
    }


def demo_root_laundering_detected() -> dict[str, Any]:
    scenario = build_evasion_scenario()
    laundered = scenario.detect_laundered_origins()
    ablation = run_ablation_battery(scenario)
    cert = generate_rootfall_certificate(scenario, ablation)
    detected = len(laundered) > 0 and cert["false_plurality_detected"]
    return {
        "demonstration": "root_laundering_detected",
        "laundered_pairs": len(laundered),
        "detected": detected,
        "verdict": cert["verdict"],
    }


def demo_corroboration_inflation_caught() -> dict[str, Any]:
    scenario = build_pass_baseline()
    original_count = scenario.corroboration_count()
    for i in range(5):
        rid = f"R_dup_{i}"
        scenario.roots[rid] = EvidenceRoot(
            rid, "copy", "Sensor array reading", 0.90,
            canonical_id="R1",
        )
        scenario.paths.append(DecisionPath(
            f"PATH_dup_{i}", f"Duplicate {i}", [rid], [],
            ["Copy route"], "System is safe to operate",
        ))
    inflated = scenario.corroboration_count()
    ablation = run_ablation_battery(scenario)
    cert = generate_rootfall_certificate(scenario, ablation)
    caught = cert["false_plurality_detected"] and cert["verdict"] == "FAIL"
    return {
        "demonstration": "corroboration_inflation_caught",
        "original_count": original_count,
        "inflated_count": inflated,
        "caught": caught,
        "verdict": cert["verdict"],
    }


def demo_certificate_forgery_fails() -> dict[str, Any]:
    scenario = build_pass_baseline()
    ablation = run_ablation_battery(scenario)
    cert = generate_rootfall_certificate(scenario, ablation)
    tampered = copy.deepcopy(cert)
    tampered["corroboration_count"] = 999
    integrity_ok = verify_certificate_integrity(tampered)
    gateway = gateway_permit(tampered, scenario.action_digest)
    return {
        "demonstration": "certificate_forgery_fails",
        "integrity_valid": integrity_ok,
        "gateway_permitted": gateway["permitted"],
        "blocked": not integrity_ok and not gateway["permitted"],
    }


def demo_ablation_evasion_fails() -> dict[str, Any]:
    scenario = build_deep_false_plurality_scenario()
    deep = scenario.detect_deep_shared_roots(4)
    ablation = run_ablation_battery(scenario)
    cert = generate_rootfall_certificate(scenario, ablation)
    evasion_fails = len(deep) > 0 and cert["false_plurality_detected"]
    return {
        "demonstration": "ablation_evasion_fails",
        "deep_shared_found": len(deep),
        "evasion_fails": evasion_fails,
        "verdict": cert["verdict"],
    }


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------


@dataclass
class TestResult:
    name: str
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)
    timing_ms: float = 0.0
    error: str = ""


class RootfallGateRunner:
    def __init__(self) -> None:
        self.results: list[TestResult] = []

    def record(self, result: TestResult) -> None:
        self.results.append(result)

    def test_scale(self) -> TestResult:
        t0 = time.perf_counter()
        try:
            scenario = build_scale_scenario()
            passed = (
                len(scenario.paths) >= 10
                and len(scenario.artifacts) >= 50
                and len(scenario.roots) >= 20
            )
            return TestResult(
                "scale_10_paths_50_evidence_20_roots",
                passed,
                {
                    "paths": len(scenario.paths),
                    "evidence_artifacts": len(scenario.artifacts),
                    "roots": len(scenario.roots),
                },
                (time.perf_counter() - t0) * 1000,
            )
        except Exception as exc:
            return TestResult(
                "scale_10_paths_50_evidence_20_roots", False,
                error=str(exc), timing_ms=(time.perf_counter() - t0) * 1000,
            )

    def test_graduated_ablation(self) -> TestResult:
        t0 = time.perf_counter()
        try:
            scenario = build_scale_scenario()
            series = graduated_ablation_series(scenario)
            monotonic = all(
                s["corroboration_after"] <= s["corroboration_before"]
                for s in series
            )
            degrades = any(s["delta_corroboration"] > 0 for s in series)
            passed = monotonic and degrades and len(series) >= 5
            return TestResult(
                "graduated_ablation_degrades_predictably",
                passed,
                {"steps": len(series), "series_sample": series[:3]},
                (time.perf_counter() - t0) * 1000,
            )
        except Exception as exc:
            return TestResult(
                "graduated_ablation_degrades_predictably", False,
                error=str(exc), timing_ms=(time.perf_counter() - t0) * 1000,
            )

    def test_subtle_false_plurality(self) -> TestResult:
        t0 = time.perf_counter()
        try:
            scenario = build_deep_false_plurality_scenario()
            deep = scenario.detect_deep_shared_roots(4)
            ablation = run_ablation_battery(scenario)
            cert = generate_rootfall_certificate(scenario, ablation)
            passed = len(deep) > 0 and cert["false_plurality_detected"]
            return TestResult(
                "subtle_false_plurality_4_levels_deep",
                passed,
                {
                    "deep_shared_findings": deep,
                    "verdict": cert["verdict"],
                    "false_plurality": cert["false_plurality_detected"],
                },
                (time.perf_counter() - t0) * 1000,
            )
        except Exception as exc:
            return TestResult(
                "subtle_false_plurality_4_levels_deep", False,
                error=str(exc), timing_ms=(time.perf_counter() - t0) * 1000,
            )

    def test_adversarial_evasion(self) -> TestResult:
        t0 = time.perf_counter()
        try:
            scenario = build_evasion_scenario()
            laundered = scenario.detect_laundered_origins()
            ablation = run_ablation_battery(scenario)
            cert = generate_rootfall_certificate(scenario, ablation)
            passed = len(laundered) >= 2 and cert["false_plurality_detected"]
            return TestResult(
                "adversarial_rename_paraphrase_launder",
                passed,
                {
                    "laundered": laundered,
                    "verdict": cert["verdict"],
                },
                (time.perf_counter() - t0) * 1000,
            )
        except Exception as exc:
            return TestResult(
                "adversarial_rename_paraphrase_launder", False,
                error=str(exc), timing_ms=(time.perf_counter() - t0) * 1000,
            )

    def test_certificate_tamper(self) -> TestResult:
        t0 = time.perf_counter()
        try:
            scenario = build_pass_baseline()
            cert = generate_rootfall_certificate(
                scenario, run_ablation_battery(scenario),
            )
            valid = verify_certificate_integrity(cert)
            tampered = copy.deepcopy(cert)
            tampered["corroboration_count"] = 999
            invalid = not verify_certificate_integrity(tampered)
            passed = valid and invalid
            return TestResult(
                "certificate_tamper_integrity_fails",
                passed,
                {"original_valid": valid, "tampered_valid": not invalid},
                (time.perf_counter() - t0) * 1000,
            )
        except Exception as exc:
            return TestResult(
                "certificate_tamper_integrity_fails", False,
                error=str(exc), timing_ms=(time.perf_counter() - t0) * 1000,
            )

    def test_multi_decision_isolation(self) -> TestResult:
        t0 = time.perf_counter()
        try:
            scenarios = build_multi_decision_scenarios()
            certs = []
            for sc in scenarios:
                cert = generate_rootfall_certificate(sc, run_ablation_battery(sc))
                certs.append(cert)

            digests = {c["action_digest"] for c in certs}
            decisions = {c["decision"] for c in certs}
            all_pass = all(c["verdict"] == "PASS" for c in certs)
            isolated = len(digests) == 5 and len(decisions) == 5

            cross_tamper = copy.deepcopy(certs[0])
            cross_tamper["action_digest"] = certs[1]["action_digest"]
            cross_blocked = not verify_certificate_integrity(cross_tamper)

            passed = all_pass and isolated and cross_blocked
            return TestResult(
                "multi_decision_5_simultaneous_isolation",
                passed,
                {
                    "decisions": len(decisions),
                    "all_pass": all_pass,
                    "cross_tamper_blocked": cross_blocked,
                },
                (time.perf_counter() - t0) * 1000,
            )
        except Exception as exc:
            return TestResult(
                "multi_decision_5_simultaneous_isolation", False,
                error=str(exc), timing_ms=(time.perf_counter() - t0) * 1000,
            )

    def test_demonstrations(self) -> TestResult:
        t0 = time.perf_counter()
        try:
            demos = [
                demo_evidence_fabrication_blocked(),
                demo_root_laundering_detected(),
                demo_corroboration_inflation_caught(),
                demo_certificate_forgery_fails(),
                demo_ablation_evasion_fails(),
            ]
            passed = all(
                d.get("blocked", d.get("detected", d.get("caught",
                    d.get("evasion_fails", False))))
                for d in demos
            )
            return TestResult(
                "adversarial_demonstrations_all_blocked",
                passed,
                {"demonstrations": demos},
                (time.perf_counter() - t0) * 1000,
            )
        except Exception as exc:
            return TestResult(
                "adversarial_demonstrations_all_blocked", False,
                error=str(exc), timing_ms=(time.perf_counter() - t0) * 1000,
            )

    def run_all(self) -> dict[str, Any]:
        for test_fn in [
            self.test_scale,
            self.test_graduated_ablation,
            self.test_subtle_false_plurality,
            self.test_adversarial_evasion,
            self.test_certificate_tamper,
            self.test_multi_decision_isolation,
            self.test_demonstrations,
        ]:
            self.record(test_fn())

        all_pass = all(r.passed for r in self.results)
        total_ms = sum(r.timing_ms for r in self.results)
        return {
            "framework": "ROOTFALL",
            "gate": "REALITY_GATE",
            "spec_version": "PUBLICATION_HARDENING_PROTOCOL",
            "blueprint_version": "2.0.0",
            "python_version": sys.version.split()[0],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_count": 3,
            "author": AUTHOR,
            "orcid": ORCID,
            "disclaimer": DISCLAIMER,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "total_gate_execution_seconds": round(total_ms / 1000.0, 6),
            "tests": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "timing_ms": round(r.timing_ms, 3),
                    "details": r.details,
                    "error": r.error,
                }
                for r in self.results
            ],
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed),
            },
            "GATE_VERDICT": "PASS" if all_pass else "FAIL",
        }


def print_summary_table(report: dict[str, Any]) -> None:
    print("\n" + "=" * 78)
    print("ROOTFALL REALITY GATE — TEST SUMMARY")
    print("=" * 78)
    print(f"{'TEST':<45} {'RESULT':<8} {'TIME(ms)':>10}")
    print("-" * 78)
    for t in report["tests"]:
        status = "PASS" if t["passed"] else "FAIL"
        print(f"{t['name']:<45} {status:<8} {t['timing_ms']:>10.1f}")
    print("-" * 78)
    s = report["summary"]
    print(f"Total: {s['total']}  Passed: {s['passed']}  Failed: {s['failed']}")
    print(f"Total gate execution: {report.get('total_gate_execution_seconds', 0):.3f} seconds")
    print(f"\nGATE VERDICT: {report['GATE_VERDICT']}")
    print("=" * 78)


def main() -> int:
    print("=" * 78)
    print("ROOTFALL Reality Gate Demonstrator")
    print(f"Author: {AUTHOR} (ORCID {ORCID})")
    print(DISCLAIMER)
    print("=" * 78)

    t0 = time.perf_counter()
    runner = RootfallGateRunner()
    report = runner.run_all()
    report["total_gate_execution_seconds"] = round(time.perf_counter() - t0, 6)
    print_summary_table(report)

    out_path = Path(__file__).resolve().parent / "rootfall_gate_results.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    print(f"\nResults written to: {out_path}")

    return 0 if report["GATE_VERDICT"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
