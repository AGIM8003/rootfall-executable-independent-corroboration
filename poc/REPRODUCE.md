# Reproducibility Guide — ROOTFALL

## Requirements
- Python 3.10+ (tested on 3.14.4)
- No external dependencies (stdlib only)

## Verify the Core Mechanism
```bash
python rootfall_poc.py
python rootfall_gate.py
python rootfall_benchmark.py
python rootfall_alt_impl.py
python rootfall_mutation_test.py
```

## Expected Output (last lines)
- `rootfall_poc.py`: `Demonstration success : True`
- `rootfall_gate.py`: `GATE VERDICT: PASS`
- `rootfall_benchmark.py`: `Correctness rate    : 100.0% (10/10)`
- `rootfall_alt_impl.py`: `Replication agree: True`
- `rootfall_mutation_test.py`: `Mutation score: 100%` (or ≥90%)

## Verification Time
All scripts complete in under 5 seconds on a standard machine.

## Evidence Files Generated
| File | Contents |
|------|----------|
| `rootfall_evidence.json` | PASS/FAIL certificates |
| `rootfall_gate_results.json` | Gate suite + versioning |
| `rootfall_benchmark_results.json` | Benchmarks + scalability |
| `rootfall_replication_evidence.json` | Set-theoretic vs graph agreement |
| `rootfall_mutation_results.json` | Mutation detections |

## Author
Agim Haxhijaha · ORCID 0009-0002-3234-7765 · Independent Researcher

## REALITY_FORGE additions (v2.2.0)

```bash
python rootfall_realworld.py
python rootfall_stress.py
```

Expect EXIT 0 and JSON evidence/results beside the scripts. Deploy reference: `rootfall_deploy_manifest.json`.

## INVENTION_CRYSTALLIZATION (v2.3.0)

```bash
from rootfall import ROOTFALLEngine
python rootfall_quickstart.py
python rootfall_integration_test.py
```
