#!/usr/bin/env python3
"""ROOTFALL Quickstart — false plurality detection in ~25 lines."""
from rootfall import ROOTFALLEngine

engine = ROOTFALLEngine(decision="UPGRADE_TO_BBB_PLUS")
engine.add_root("vendor_feed_X", source_type="market_data", description="Shared CDS terminal feed")
engine.add_root("issuer_10k", source_type="filing", description="Audited 10-K")
engine.add_root("site_audit", source_type="ops", description="Independent site audit")

engine.add_path("desk_emea", label="EMEA desk", root_ids=["vendor_feed_X"])
engine.add_path("desk_us", label="US desk", root_ids=["vendor_feed_X"])
engine.add_path("primary_diligence", label="Primary", root_ids=["issuer_10k", "site_audit"])

report = engine.attest()
print(f"Verdict: {report.verdict}")
print(f"Independence: {report.independence_score}")
print(f"False plurality: {report.false_plurality_detected}")
print(f"Hidden shared roots: {len(report.hidden_shared_roots)}")
print(f"Reason: {report.verdict_reason}")
