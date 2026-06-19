# Acoustic Source Localization Digital Twin

Real-time 3D digital twin of acoustic source localization in outdoor environments.
A network of fixed microphone sensors estimates the 2D position of a moving sound
source using Time Difference of Arrival (TDOA) — with quantified localization
uncertainty shown as a live 95% confidence ellipse.

**Applications:** wildlife monitoring, environmental noise mapping, urban acoustic
awareness, emergency response routing, impulsive event localization.

**Author:** Umar Farooq  
**Phase:** 1 complete — Python + PyVista + Rich

---

## Demo

![Localization digital twin — single frame render](media/demo_frame.png)

Two windows run simultaneously from a single command:

**3D render (PyVista)** — terrain, sensor array, moving source (green), estimated
position (yellow), and live 95% confidence ellipse updating every tick.

**Terminal panel (Rich)** — localization metrics, error sparkline, per-sensor SNR
table.

```powershell
python scripts/run_demo.py
```

---

## Algorithm

The core algorithm is a **weighted Gauss-Newton TDOA solver** with a
**CRLB-based confidence ellipse**:

1. Each sensor records the Time of Arrival (TOA) of the acoustic wavefront.
2. TDOA is computed relative to sensor 0 — this introduces correlated noise
   (all measurements share sensor-0's noise).
3. Gauss-Newton iterates on the nonlinear hyperbolic system using weighted MLE,
   where the weight `W` is the inverse TDOA measurement covariance:
   `Δp = (JᵀWJ)⁻¹ Jᵀ W (−residuals)`
4. The weighting is **maximum-ratio combining**: each sensor contributes in proportion
   to its reliability. Per-sensor noise grows with range (`σ_τ ∝ r`), so far sensors
   are down-weighted. The equal-variance case reduces to `W = M⁻¹ = I − (1/N)·11ᵀ`
   (Sherman-Morrison) with `C = σ²(I + 11ᵀ)`.
5. Position covariance is the Fisher Information Matrix inverse `Σ = (JᵀWJ)⁻¹`.
6. The 95% confidence ellipse uses the chi-squared threshold `χ²(0.95, 2) = 5.991`.

**Validated:** 25/25 unit tests pass; Monte Carlo confirms 95% CI coverage. Under a
degraded sensor (×10 noise), maximum-ratio weighting holds error at ~4.8 cm where
equal-weight LS degrades to 17 cm — an 11 dB array gain. See `docs/concepts.ipynb`
section 8 for the derivation.

---

## Architecture

```
scenarios/configs/*.yaml
        |
        v
  scenarios/loader.py    (Pydantic v2 — validated on load)
        |
        v
   engine/               (pure algorithm — never imports viz or dashboard)
   ├── source.py         (waypoint path follower)
   ├── propagation.py    (PropagationModel Protocol + SimplePropagation)
   ├── tdoa.py           (TDOA measurements + Gaussian noise)
   ├── localizer.py      (GaussNewtonTDOA — weighted MLE)
   ├── confidence.py     (95% CI ellipse via CRLB)
   └── engine.py         (tick loop orchestrator)
        |
        v
  shared/current_state.json   (atomic JSON IPC — written each tick)
        |
   ┌────┴────┐
   v         v
visualization/  dashboard/
live_renderer   panel.py
(PyVista 3D)   (Rich terminal)
```

---

## Quick Start

```powershell
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Algorithm smoke test (no window)
python scripts/run_tdoa_demo.py

# Full demo — 3D window + terminal panel
python scripts/run_demo.py

# Tests
python -m pytest tests/ -v
```

---

## Scenarios

Scenarios are fully defined in YAML — swap the file, get a different deployment.

| Scenario | Description |
|---|---|
| `wildlife_monitoring.yaml` | 4 sensors, 300 m forest clearing, animal at 1.2 m/s |

---

## Project Docs

| Document | Purpose |
|---|---|
| [Functional Report](docs/functional-report.md) | Algorithm derivation, validation results, deployment questions |
| [Decision Log](docs/decision-log.md) | All architectural and algorithmic decisions with rationale |
| [Concepts Notebook](docs/concepts.ipynb) | Estimation theory: TDOA geometry, CRLB, GDOP |
| [Project Status](docs/project-status.md) | Step-by-step progress log |

---

## Phase 2 (planned)

Port visualization layer to Unreal Engine 5. Engine and algorithm layer unchanged.

---

## License

MIT
