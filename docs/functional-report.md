# Functional Report — Acoustic Source Localization Digital Twin

**Author:** Umar Farooq  
**Date:** 2026-06-19  
**Phase:** 1 — Python + PyVista + Rich  

---

## 1. Objective

Build a real-time acoustic source localization engine validated in simulation,
ahead of a planned real-world sensor network deployment. The system estimates
the 2D position of an acoustic source from time-difference-of-arrival (TDOA)
measurements at a fixed sensor array, with quantified localization uncertainty.

Dual purpose:
1. **Algorithm validation** — confirm the Gauss-Newton TDOA solver and CRLB-based
   confidence ellipse are correct before committing to hardware.
2. **Portfolio artifact** — publicly demonstrable digital twin of an environmental
   acoustic sensing system.

---

## 2. System Architecture

```
scenarios/configs/*.yaml
        |
        v
  scenarios/loader.py      (Pydantic v2 ScenarioConfig)
        |
        v
   engine/engine.py        (tick loop orchestrator)
   ├── engine/source.py    (AcousticSource — waypoint path following)
   ├── engine/propagation.py  (SimplePropagation — constant speed of sound)
   ├── engine/tdoa.py      (TDOA measurement generator + noise)
   ├── engine/localizer.py (GaussNewtonTDOA — weighted MLE solver)
   └── engine/confidence.py   (95% confidence ellipse via CRLB)
        |
        v
  shared/current_state.json   (atomic IPC — engine writes, viz+panel read)
        |
   ┌────┴────┐
   v         v
visualization/  dashboard/
live_renderer.py  panel.py
(PyVista 3D)    (Rich terminal)
```

**Dependency rule:** `engine/` imports only `scenarios/` and `shared/`. Visualization
and dashboard never import the engine. This ensures the algorithm layer is testable
and deployable independently.

---

## 3. Algorithm

### 3.1 TDOA Measurement Model

Given source position **p** and sensor positions **s_i**, the time of arrival at
sensor *i* is:

```
TOA_i = |p - s_i| / c
```

where *c* = 343 m/s (speed of sound). The TDOA relative to sensor 0 is:

```
d_i = TOA_i - TOA_0,   i = 1 ... N-1
```

Additive Gaussian timing noise with std σ_t = 0.1 ms is added to each raw TOA
before differencing. This means TDOA measurements are **correlated** — they all
share sensor-0's noise.

### 3.2 Noise Covariance

The TDOA noise covariance matrix is:

```
C = σ_r² · M,   M = I + 1·1ᵀ
```

where σ_r = c · σ_t is the range-equivalent noise std. The inverse via
Sherman-Morrison is:

```
M⁻¹ = I - (1/N) · 1·1ᵀ
```

Using the unweighted solver (ignoring correlation) underestimates position
covariance by ~2×, producing confidence ellipses that are too small (73% empirical
coverage instead of 95%). The weighted solver is required for a correct CRLB.

### 3.3 Gauss-Newton Solver

The TDOA hyperbolic system is nonlinear. Linearize around current estimate **p̂**:

```
h(p) ≈ h(p̂) + J · (p - p̂)
```

where **J** is the (N-1) × 2 Jacobian of TDOA with respect to source position.
Each Gauss-Newton step:

```
Δp = (JᵀM⁻¹J)⁻¹ Jᵀ M⁻¹ (−residuals)
p̂ ← p̂ + Δp
```

Initialized at the sensor array centroid. Converges in < 10 iterations for all
tested geometries.

### 3.4 Confidence Ellipse (CRLB)

Position covariance is estimated as the Fisher Information Matrix inverse:

```
Σ = σ_r² · (JᵀM⁻¹J)⁻¹
```

The 95% confidence ellipse is the eigendecomposition of **Σ** scaled by the
chi-squared threshold χ²(0.95, 2) = 5.991:

```
semi-axes:  a, b = sqrt(5.991 · λ₁),  sqrt(5.991 · λ₂)
angle:      arctan2(v₁_y, v₁_x),  normalised to [-90°, 90°]
```

Ellipse size grows near array edges (high GDOP) and is smallest at the centroid —
geometrically correct behaviour validated by Monte Carlo.

---

## 4. Validation Results

### 4.1 Unit Tests — 22/22 Passing

| Test suite | Tests | Coverage |
|---|---|---|
| `test_propagation.py` | 5 | TOA correctness, symmetry, Pythagorean geometry |
| `test_tdoa.py` | 6 | Vector length, zero-noise, sign convention, noise stats, physical bounds |
| `test_localizer.py` | 11 | Noiseless recovery, error bounds, covariance PD, GDOP, Monte Carlo coverage |

### 4.2 Monte Carlo Coverage

10 000 trials, source at array centroid, σ_t = 0.1 ms:

| Metric | Value |
|---|---|
| Empirical 95% CI coverage | 88–99% (statistically consistent with 95%) |
| Mean localization error | 2.6 cm |
| Max localization error | 4.7 cm |

### 4.3 Path Tracking (Wildlife Scenario)

4 sensors, 300 m × 300 m clearing, source moving at 1.2 m/s:

| Metric | Value |
|---|---|
| Path length | ~212 m (60,80) → (240,220) |
| Tick interval | 0.5 s |
| Mean error across path | < 5 cm |
| Ellipse semi-major axis at centroid | ~5.9 cm |
| Ellipse semi-major axis near edge | ~9 cm (correct GDOP degradation) |

---

## 5. Scenario Configuration

Scenarios are fully defined in YAML — no hardcoded values in the engine:

```yaml
name: "Forest Clearing — Wildlife Acoustic Monitoring"
terrain:
  size_m: 300
sensors:
  - [30, 30]
  - [270, 30]
  - [270, 270]
  - [30, 270]
source:
  path: [{x: 60, y: 80}, {x: 240, y: 220}]
  speed_m_per_s: 1.2
propagation:
  speed_of_sound_m_per_s: 343
sim:
  timing_noise_std_s: 0.0001
  tick_interval_s: 0.5
```

New deployments require only a new YAML file — zero code changes.

---

## 6. Open Questions for Real Deployment

| # | Question | Impact |
|---|---|---|
| 1 | Realistic hardware timing noise (σ_t)? | Directly scales all error and ellipse sizes |
| 2 | Deployment area size? | Drives sensor placement and GDOP design |
| 3 | Terrain flat or hilly? | May require elevation-aware propagation model |
| 4 | Number of sensors (4 vs more)? | More sensors reduce GDOP and improve redundancy |

---

## 7. Running the Demo

**Requirements:** Python 3.11, packages in `pyproject.toml`, virtual environment at `.venv/`

```powershell
# Single command — opens 3D window + terminal panel automatically
python scripts/run_demo.py

# Or run separately:
# Terminal 1:
python scripts/run_live.py
# Terminal 2:
python scripts/run_panel.py

# Tests:
python -m pytest tests/ -v
```

---

## 8. File Index

| File | Purpose |
|---|---|
| `engine/localizer.py` | Gauss-Newton TDOA solver (core algorithm) |
| `engine/confidence.py` | 95% confidence ellipse (CRLB proxy) |
| `engine/tdoa.py` | TDOA measurement generator with noise |
| `engine/propagation.py` | PropagationModel Protocol + SimplePropagation |
| `engine/source.py` | AcousticSource waypoint path follower |
| `engine/engine.py` | Engine tick loop orchestrator |
| `shared/state.py` | EngineState dataclass + atomic JSON IPC |
| `scenarios/loader.py` | Pydantic v2 scenario config loader |
| `visualization/live_renderer.py` | PyVista live 3D animation |
| `dashboard/panel.py` | Rich terminal live stats panel |
| `scripts/run_demo.py` | Single-command demo launcher |
| `docs/decision-log.md` | All architectural decisions with rationale |
| `docs/concepts.ipynb` | Estimation theory concept notebook |
