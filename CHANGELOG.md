# Changelog

All notable changes to this project are documented here.
Format: `[step-N] YYYY-MM-DD — Description`

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
