# ROOTFALL Prior-Art and Standards Review

**Review date:** July 16, 2026  
**Edition:** v2.1.0 Public Research Edition  
**Publication:** Independent Research Publication No. 9  
**Author:** Agim Haxhijaha — ORCID 0009-0002-3234-7765  
**Scope:** Public products, standards, research literature, and engineering practice adjacent to independent corroboration, ensemble decision-making, and execution control. This companion is **not** a freedom-to-operate opinion and **not** a patentability opinion.

## Executive Finding

ROOTFALL remains a credible publication candidate as a **proposed integrated architecture**. The v2.1.0 review compares ROOTFALL against eleven named adjacent systems. None of them combine frozen decision replay, conservative root clustering, counterfactual root ablation, action-bound certificates, and a fail-closed execution gateway in one ordered sequence.

**CORE claim spine (public quote surface):**

```text
frozen decision-and-action capsule → conservative root grouping → root+descendant removal → decision replay → necessity/sufficiency → action-bound certificate → fail-closed execution gateway
```

Publish ROOTFALL as ordered root ablation of a frozen decision with an action-bound fail-closed gateway. Do not claim provenance, fact-checking, ensemble voting, or quorum counting alone as the invention.

## Comparison Table (11 Named Systems)

| System | Year / era | What it does | What it lacks (gap ROOTFALL addresses) |
|---|---|---|---|
| **Random Forest / bagging ensembles** (Breiman; scikit-learn) | 1996+ | Aggregates many decision trees trained on bootstrap samples to reduce variance | No evidentiary root lineage; no counterfactual ablation of shared data sources; no action-bound execution gate |
| **Stacked generalization / model stacking** (Wolpert; MLflow patterns) | 1992+ | Meta-learner combines base model outputs | Treats model outputs as independent features; does not detect when base models share training data or feeds |
| **Deep ensembles / MC Dropout** (Lakshminarayanan et al.) | 2017+ | Epistemic uncertainty via multiple forward passes or ensemble heads | Uncertainty is distributional, not provenance-based; no root removal replay on a frozen action capsule |
| **Bayesian model averaging** (Hoeting et al.; PyMC) | 1999+ | Weights models by posterior probability | Assumes model list is given; does not ablate shared evidence roots or block trades pre-execution |
| **SHAP (SHapley Additive exPlanations)** (Lundberg & Lee) | 2017+ | Feature attribution via Shapley values | Explains feature contribution post hoc; does not certify independent corroboration paths or gate actions |
| **DoWhy causal inference** (Microsoft Research) | 2021+ | Causal effect estimation with refutation tests | Causal graphs are analyst-specified; no conservative root clustering from messy evidence imports; no PERMIT/DENY gateway |
| **Adversarial example detection** (CleverHans, ART) | 2014+ | Detects perturbed inputs that fool classifiers | Input-perturbation focus; does not address false plurality from duplicated sources or shared feeds |
| **Multi-armed bandits / A/B testing** (Thompson sampling; Optimizely) | 1930s / 2010s | Allocates traffic to maximize reward under uncertainty | Experimental allocation, not corroboration of a single high-stakes action; no root ablation |
| **Redundant sensor fusion / Kalman filtering** (ROS sensor fusion) | 1960s+ | Fuses noisy sensor streams with covariance weighting | Assumes known sensor independence or calibrated noise; weak on hidden shared upstream feeds (e.g., one Bloomberg terminal) |
| **Byzantine fault tolerance voting** (PBFT; Raft quorum) | 1999+ / 2014+ | Tolerates malicious or faulty replicas via quorum | Counts voters, not evidentiary roots; replicas can share the same corrupted source without detection |
| **Prediction markets / wisdom of crowds** (Polymarket; Metaculus) | 2000s+ | Aggregates dispersed beliefs into a price or forecast | Market price is not action-bound; no ablation of shared information roots before execution |

## What Makes ROOTFALL Different

- **Ordered counterfactual ablation:** Removes each evidentiary root and replays the *same* frozen decision — not a new model vote or a fresh forecast.
- **False plurality as first-class failure:** Detects when N apparent paths share a hidden ancestor (e.g., Bloomberg Terminal 7 feeding two quant models).
- **Action binding:** Certificate is cryptographically tied to one proposed action digest; substitution attacks fail at the gateway.
- **Fail-closed execution:** DENY/HOLD is the default when independence does not survive ablation — not an advisory score.
- **Conservative root clustering:** Merges suspected duplicates before counting independence; unresolved edges are not counted toward N_cert.

## What This Blueprint Does NOT Improve Over

- **Ensemble accuracy for IID data:** Random forests and stacking remain superior for standard classification benchmarks where training-data independence is assumed.
- **Feature explainability UX:** SHAP and LIME provide richer per-prediction explanations for data scientists; ROOTFALL does not replace them.
- **Causal discovery:** DoWhy and structural causal models are stronger when the causal graph is the research object itself.
- **Byzantine replication:** PBFT/Raft are mature, production-proven for state-machine replication; ROOTFALL does not compete on consensus throughput.
- **Uncertainty quantification depth:** Deep ensembles and Bayesian methods offer finer-grained epistemic intervals; ROOTFALL trades that for executable corroboration gates.
- **Prediction market efficiency:** Markets aggregate dispersed private information well for forecasting; ROOTFALL targets pre-execution authorization, not price discovery.

## Adjacent Standards (Non-Substitutes)

| Standard / framework | Relationship |
|---|---|
| C2PA / OpenLineage | Lineage adjacency; do not authorize action after counterfactual ablation |
| ISO 42001 (AI management) | Governance context; not a corroboration runtime |
| EU AI Act high-risk controls | Compliance framing; ROOTFALL is a proposed mechanism, not a certification |

## Honesty Rules for Public Release

1. Do not claim zero prior art — eleven adjacent systems are named above.
2. Do not claim production implementation — minimal PoC only (`poc/rootfall_poc.py`).
3. Do not claim that Reality Gate Zero documentation equals a passed Gate.
4. Do not merge claims with sibling blueprints (DERF, INTENTIDE, REALITY ACCORD).
5. Do not treat Real-Invention Readiness ~90% as a legal or patent-grant conclusion.
6. Do not claim ROOTFALL replaces ensemble methods for general ML — it addresses a different failure mode (false plurality before action).

## Recommended Public Positioning

Publish as an independent technical blueprint and proposed architecture with demonstrated minimal PoC. Invite criticism of the ordered CORE combination — especially whether conservative root clustering plus ablation replay is sufficient for regulated trading, medical, and procurement domains — not marketing of a proven product or granted patent.

## 2025–2026 Live Prior Art Expansion

| System / Paper | Year | URL / DOI | What it does | Gap ROOTFALL addresses |
|---|---|---|---|---|
| **ProRCA** | 2025 | [arXiv:2503.01475](https://arxiv.org/abs/2503.01475) | Causal Python package for multi-hop root-cause analysis in business operations (extends DoWhy) | Post-hoc anomaly RCA on KPIs; no frozen decision capsule, action-bound certificate, or fail-closed execution gateway |
| **DoWhy RCA** (PyWhy) | 2021+ | [https://github.com/py-why/dowhy](https://github.com/py-why/dowhy) | Causal inference with refutation tests and graph-based reasoning | Analyst-specified causal graphs; no conservative evidence clustering or counterfactual ablation before trade execution |
| **Causal AI Decision Intelligence** (theCUBE) | 2026 | [theCUBE research briefings](https://www.thecube.net/) | Industry coverage of causal AI for enterprise decision intelligence | Strategic framing; no executable PERMIT/DENY gateway tied to root ablation |
| **CausalML RCA practice notes** | 2025–2026 | [https://causalml.readthedocs.io](https://causalml.readthedocs.io) | Uplift modeling and causal ML experimentation patterns | Treatment-effect estimation; not independent corroboration under evidence laundering |
| **PyRCA** (Salesforce) | 2023+ | [https://github.com/salesforce/PyRCA](https://github.com/salesforce/PyRCA) | Metric-centric root-cause analysis for IT operations | Telemetry graphs; no action-bound AI decision certificates |

### What competitors do better

1. **ProRCA / DoWhy / PyRCA:** Richer multi-hop causal pathway analytics for human analysts after incidents occur.
2. **CausalML / enterprise causal AI stacks:** Stronger treatment-effect and uplift estimation for experimentation programs.

### Why this still matters

No 2025–2026 adjacent system combines frozen decision replay, conservative root clustering, per-root counterfactual ablation, necessity/sufficiency metrics, action-bound certificates, and a fail-closed execution gateway — ROOTFALL blocks false plurality *before* irreversible machine action, not after dashboard RCA.

