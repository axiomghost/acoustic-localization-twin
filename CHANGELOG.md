# Changelog

All notable changes to this project are documented here.
Format: `[step-N] YYYY-MM-DD — Description`

---

## [step-4] 2026-06-18 — PyVista 3D single-frame renderer

### Added
- `visualization/renderer.py` — PyVista renderer (terrain, sensors, true/est positions, confidence ellipse)
- `visualization/__init__.py`
- `scripts/render_frame.py` — single-frame demo with --screenshot flag

### Changed
- `scenarios/configs/wildlife_monitoring.yaml` — name updated to human-readable display string
- `visualization/renderer.py` — window title pulled from scenario.name

### Results
- 3D window renders correctly: 300m terrain, 4 sensors, source at centroid, 3.48cm error, 5.9x5.9cm ellipse

---

## [step-3] 2026-06-18 — Confidence ellipse validation, unit tests, and concept notebook

### Added
- `tests/test_propagation.py` — 5 tests
- `tests/test_tdoa.py` — 6 tests
- `tests/test_localizer.py` — 11 tests (including Monte Carlo coverage test)
- `docs/concepts.ipynb` — estimation theory concept notebook (TDOA, Gauss-Newton,
  noise correlation, weighted LS, FIM/CRLB, confidence ellipse, GDOP)

### Fixed
- `engine/localizer.py` — weighted GN with M^{-1} = I - (1/N)*ones (DEC-007)
- `engine/confidence.py` — normalise ellipse angle to [-90, 90]

### Results
- 22/22 tests pass
- Monte Carlo coverage validated at 95%

---

## [step-3-pre] 2026-06-18 — Confidence ellipse validation and unit tests

### Added
- `tests/test_propagation.py` — 5 tests for SimplePropagation
- `tests/test_tdoa.py` — 6 tests for TDOA measurement generation
- `tests/test_localizer.py` — 11 tests for localizer, confidence ellipse, and scenario loader
- `tests/__init__.py`

### Fixed
- `engine/localizer.py` — upgraded unweighted to weighted Gauss-Newton using correct
  TDOA noise covariance M^{-1} = I - (1/N)*ones. Coverage improved from 73% to 95%.
- `engine/confidence.py` — normalise ellipse angle to [-90, 90] (180-degree symmetry)

### Results
- 22/22 tests pass
- Monte Carlo coverage: 95% confidence ellipse validated statistically

---

## [step-2] 2026-06-18 — Scenario YAML loader and wildlife monitoring config

### Added
- `scenarios/loader.py` — Pydantic v2 ScenarioConfig models with validation
- `scenarios/configs/wildlife_monitoring.yaml` — forest clearing wildlife monitoring scenario
- `scenarios/__init__.py`

### Changed
- `scripts/run_tdoa_demo.py` — now loads fully from scenario YAML, no hardcoded values

### Results
- Wildlife scenario (300m array): mean error 2.6 cm, max 4.7 cm at 0.1 ms noise
- GDOP variation visible across path: ellipse grows near array edges as expected

---

## [step-1] 2026-06-18 — Project scaffold and TDOA algorithm baseline

### Added
- Project folder structure: engine, shared, scenarios, visualization, dashboard, scripts, tests, docs
- `engine/propagation.py` — SimplePropagation (constant speed of sound, 1/r attenuation)
- `engine/tdoa.py` — TDOA measurement generator with Gaussian timing noise
- `engine/localizer.py` — Gauss-Newton TDOA solver (linearized hyperbolic intersection)
- `engine/confidence.py` — 95% confidence ellipse via eigendecomposition (CRLB proxy)
- `shared/state.py` — EngineState dataclass with atomic JSON file write
- `scripts/run_tdoa_demo.py` — runnable smoke test (20 ticks, 4 sensors, 1 source)
- `pyproject.toml` — project metadata and dependency spec
- `README.md` — project overview and quick start
- `docs/project-status.md` — living status report (updated each step)
- `docs/decision-log.md` — architectural and algorithmic decision rationale
- `.gitignore` — excludes venv, pycache, runtime state files

### Results
- Mean localization error: 2.6 cm at 0.1 ms timing noise, 200m x 200m array
