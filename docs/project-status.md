# Project Status Report

**Project:** Acoustic Source Localization Digital Twin  
**Author:** Umar Farooq  
**Role:** Algorithm Owner & Technical Director  
**Target ship:** June 30, 2026  
**Last updated:** 2026-06-18

---

## Executive Summary

Building a real-time acoustic source localization engine with 3D visualization
(PyVista) and a live dashboard (Streamlit). Dual purpose: (1) public portfolio
artifact, (2) algorithm validation ahead of a planned real-world sensor deployment.
Core algorithm: TDOA-based localization using Gauss-Newton iterative solver.

---

## Step Progress

| Step | Description | Status | Date |
|------|-------------|--------|------|
| 1 | Project scaffold + TDOA algorithm smoke test | DONE | 2026-06-18 |
| 2 | Scenario YAML loader + wildlife config | pending | — |
| 3 | Confidence ellipse validation + unit tests | pending | — |
| 4 | PyVista 3D render — single frame | pending | — |
| 5 | Source motion + live render loop | pending | — |
| 6 | Streamlit dashboard alongside | pending | — |
| 7 | Full demo launch script | pending | — |
| 8 | Functional report + screencap + publish | pending | — |

---

## Step 1 Results (2026-06-18)

**What was built:**
- Python 3.11 virtual environment
- Project folder structure (engine, shared, scenarios, visualization, dashboard, scripts, tests, docs)
- `engine/propagation.py` — SimplePropagation: constant speed of sound (343 m/s), 1/r distance model
- `engine/tdoa.py` — TDOA measurement generator with additive Gaussian timing noise
- `engine/localizer.py` — Gauss-Newton TDOA solver (linearized hyperbolic intersection)
- `engine/confidence.py` — 95% confidence ellipse via eigendecomposition of position covariance
- `shared/state.py` — EngineState dataclass with atomic JSON write
- `scripts/run_tdoa_demo.py` — runnable smoke test

**Algorithm performance:**
- Array: 4 sensors in 200m x 200m square
- Timing noise: 0.1 ms standard deviation
- Mean localization error: **2.6 cm**
- Max localization error: **4.6 cm**
- Confidence ellipse: ~6 cm x 3 cm semi-axes (95% CI)
- Convergence: < 10 Gauss-Newton iterations from centroid init

**Key observation:** Error is consistent with the Cramer-Rao Lower Bound for this
geometry and noise level. Timing noise is the dominant error driver — this will be
the critical parameter to characterize in the real sensor deployment.

---

## Open Questions / Risks

| # | Item | Owner | Priority |
|---|------|-------|----------|
| 1 | What is the realistic timing noise spec of the target hardware sensors? | Umar | High |
| 2 | What is the target deployment area size (affects sensor placement design)? | Umar | High |
| 3 | Will terrain be flat or hilly? (affects Phase 1.5 scope) | Umar | Medium |
| 4 | Is 4 sensors the target, or more? GDOP improves with more sensors | Umar | Medium |

---

## Decisions Made

See [Decision Log](decision-log.md) for rationale on all architectural choices.
