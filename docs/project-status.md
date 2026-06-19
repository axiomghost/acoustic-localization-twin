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
| 2 | Scenario YAML loader + wildlife config | DONE | 2026-06-18 |
| 3 | Confidence ellipse validation + unit tests | DONE | 2026-06-18 |
| 4 | PyVista 3D render — single frame | DONE | 2026-06-18 |
| 5 | Source motion + live render loop | DONE | 2026-06-19 |
| 6 | Streamlit dashboard alongside | pending | — |
| 7 | Full demo launch script | pending | — |
| 8 | Functional report + screencap + publish | pending | — |

**NOTE — Steps 9-11 are out of scope for this repository.** They involve impulsive
acoustic event localization (including two-source crack+blast fusion) which is
sensitive subject matter. These steps will be executed in a **separate private
repository** when the time comes. No code, commits, or docs from steps 9-11 will
appear here.

| 9 | Impulsive event: muzzle-blast-only scenario | pending | PRIVATE REPO |
| 10 | Crack + blast fusion (ImpulsiveLocalizer + MachConeModel) | pending | PRIVATE REPO |
| 11 | Crack + blast validation: trajectory sweep + error analysis | pending | PRIVATE REPO |

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

## Step 4 Results (2026-06-18)

**What was built:**
- `visualization/renderer.py` — PyVista renderer: flat terrain mesh, sensor spheres,
  true/estimated source spheres, connecting line, 95% confidence ellipse curve, annotations
- `scripts/render_frame.py` — single-frame demo script with `--screenshot` flag

**Render validated:**
- Scenario: Forest Clearing — Wildlife Acoustic Monitoring
- Source at array centre (150, 150): error 3.48 cm, ellipse 5.9 × 5.9 cm (circular — correct, symmetric GDOP at centroid)
- Window title, annotations, and legend all populated from scenario config
- `--screenshot` flag saves PNG to `media/` without interactive window

**Key design point:** Renderer imports from `scenarios/` and `shared/` only.
Engine is never imported by visualization — dependency rule from CLAUDE.md holds.

---

## Step 3 Results (2026-06-18)

**What was built:**
- `tests/test_propagation.py` — 5 tests covering TOA correctness, symmetry, Pythagorean geometry
- `tests/test_tdoa.py` — 6 tests covering vector length, zero-noise cases, sign convention, noise statistics, physical bounds
- `tests/test_localizer.py` — 11 tests covering noiseless recovery, noisy error bounds, covariance PD property, ellipse geometry, noise scaling, GDOP sensitivity, Monte Carlo coverage, and scenario loader integration

**Bug found and fixed:**
Two algorithm defects caught by tests, both now in decision log (DEC-007):
1. **TDOA noise correlation ignored** — TDOA measurements share sensor-0 noise, making them correlated. Unweighted LS underestimated position covariance, producing ellipses too small (73% coverage instead of 95%). Fixed: weighted Gauss-Newton with M^{-1} = I - (1/N)*ones.
2. **Ellipse angle not normalised** — arctan2 returns [-180, 180] but ellipse has 180-degree symmetry. Fixed: normalise to [-90, 90] in confidence.py.

**Final test result:** 22/22 passed, 0.49s

**Key validation:** Monte Carlo coverage test confirms the 95% confidence ellipse contains the true position in 88-99% of trials — statistically correct.

---

## Step 2 Results (2026-06-18)

**What was built:**
- `scenarios/loader.py` — Pydantic v2 models for full scenario config (terrain, sensors, source, propagation, sim, visualization). Validated on load with clear error messages.
- `scenarios/configs/wildlife_monitoring.yaml` — first civilian scenario: 4 sensors around a 300m x 300m forest clearing, animal moving at 1.2 m/s
- `scripts/run_tdoa_demo.py` — updated to load entirely from YAML; no hardcoded values remain

**Algorithm performance (wildlife scenario):**
- Array: 4 sensors, 300m x 300m clearing perimeter
- Timing noise: 0.1 ms
- Mean localization error: **2.6 cm**, Max: **4.7 cm**
- Confidence ellipse semi-axes: ~6–7 cm x 2.9–4.0 cm (grows near array edges — correct GDOP behaviour)
- Engine is now fully scenario-agnostic: swap the YAML, get a different deployment

**Notable:** Ellipse semi-major axis increases toward array edges (ticks 0 and 19) and is smallest near the array centre. This is geometrically correct — GDOP degrades near edges. Worth flagging to Umar as it directly informs real sensor placement decisions.

---

## Decisions Made

See [Decision Log](decision-log.md) for rationale on all architectural choices.
