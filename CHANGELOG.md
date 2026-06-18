# Changelog

All notable changes to this project are documented here.
Format: `[step-N] YYYY-MM-DD — Description`

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
