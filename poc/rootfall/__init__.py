"""ROOTFALL — Independent Corroboration with Root Ablation (research library)."""
from .core import (
    DecisionPath,
    DecisionScenario,
    EvidenceRoot,
    ablate_root,
    generate_rootfall_certificate,
    run_ablation_battery,
)
from .engine import ROOTFALLEngine
from .types import AttestationReport

__all__ = [
    "ROOTFALLEngine",
    "AttestationReport",
    "EvidenceRoot",
    "DecisionPath",
    "DecisionScenario",
    "ablate_root",
    "run_ablation_battery",
    "generate_rootfall_certificate",
]
__version__ = "2.3.0"
