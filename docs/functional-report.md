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

Per-sensor arrival-time noise grows with range (amplitude ∝ 1/r ⇒ timing CRLB ∝ r,
DEC-009), so each sensor has its own variance σ_i². The TDOA covariance in range
units is:

```
C_r = c² · ( diag(σ_1² … σ_{N-1}²) + σ_0² · 1·1ᵀ )
```

The off-diagonal `σ_0²·11ᵀ` term is the correlation from the shared reference sensor 0.
The estimator weights by `W = C_r⁻¹` (maximum-ratio combining — DEC-010).

**Equal-variance special case:** if every σ_i = σ_t, then `C_r = σ_r²·M` with
`M = I + 1·1ᵀ`, and `W = M⁻¹ = I − (1/N)·1·1ᵀ` (Sherman-Morrison). The unweighted
solver (ignoring even this correlation) underestimates covariance by ~2×, giving 73%
coverage instead of 95% — the original motivation for weighting (DEC-007).

### 3.3 Gauss-Newton Solver

The TDOA hyperbolic system is nonlinear. Linearize around current estimate **p̂**:

```
h(p) ≈ h(p̂) + J · (p - p̂)
```

where **J** is the (N-1) × 2 Jacobian of TDOA with respect to source position.
Each Gauss-Newton step:

```
Δp = (JᵀWJ)⁻¹ Jᵀ W (−residuals),   W = C_r⁻¹
p̂ ← p̂ + Δp
```

Initialized at the sensor array centroid. Converges in < 10 iterations for all
tested geometries.

### 3.4 Confidence Ellipse (CRLB)

Position covariance is estimated as the Fisher Information Matrix inverse:

```
Σ = (JᵀWJ)⁻¹     (= σ_r² · (JᵀM⁻¹J)⁻¹ in the equal-variance case)
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

### 4.1 Unit Tests — 25/25 Passing

| Test suite | Tests | Coverage |
|---|---|---|
| `test_propagation.py` | 5 | TOA correctness, symmetry, Pythagorean geometry |
| `test_tdoa.py` | 6 | Vector length, zero-noise, sign convention, noise stats, physical bounds |
| `test_localizer.py` | 14 | Noiseless recovery, error bounds, covariance PD, GDOP, Monte Carlo coverage, maximum-ratio weighting |

### 4.2 Monte Carlo Coverage (equal-variance baseline)

10 000 trials, source at array centroid, uniform σ_t = 0.1 ms:

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

### 4.4 Maximum-Ratio Weighting (Phase 1.5 · A2)

With heterogeneous per-sensor noise, inverse-variance (maximum-ratio) weighting
outperforms equal-weight LS. Source at array centre, one sensor's noise degraded:

| Degraded sensor noise | Equal-weight RMSE | Maximum-ratio RMSE | Gain |
|---|---|---|---|
| ×1 | 3.4 cm | 3.4 cm | 0 dB |
| ×10 | 17.4 cm | 4.8 cm | 11 dB |
| ×30 | 51.4 cm | 4.9 cm | 20 dB |

Maximum-ratio weighting holds accuracy by down-weighting the degraded sensor;
95% coverage is preserved. Derivation and "break it" experiment: `concepts.ipynb`
section 8. See DEC-009 (noise model) and DEC-010 (weighting).

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
