# Acoustic Source Localization Digital Twin

Real-time 3D digital twin of acoustic source localization in outdoor environments.
Visualizes how a network of microphone sensors triangulates a sound source position
using Time Difference of Arrival (TDOA) — for wildlife monitoring, environmental
noise mapping, urban acoustic awareness, and emergency response routing.

**Author:** Umar Farooq  
**Status:** Phase 1 in development — see [Project Status](docs/project-status.md)

## Architecture

```
scenarios/configs/*.yaml
        │
        ▼
   engine/          ← pure simulation, no viz imports
        │
        ▼
shared/current_state.json   ← atomic JSON (written each tick)
        ├──▶  visualization/   (PyVista 3D render)
        └──▶  dashboard/       (Streamlit browser UI)
```

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -e ".[dev]"

# Run algorithm smoke test
python scripts/run_tdoa_demo.py

# Run full demo (Phase 1, Step 7+)
python scripts/run_demo.py
```

## Components

| Folder | Purpose |
|--------|---------|
| `engine/` | Core simulation: propagation, TDOA, localization, confidence |
| `scenarios/` | YAML scenario configs + loader |
| `visualization/` | PyVista 3D renderer |
| `dashboard/` | Streamlit live dashboard |
| `shared/` | State dataclass + JSON IPC |
| `scripts/` | Entry points |
| `tests/` | Unit tests |
| `docs/` | Functional report, decision log, project status |

## Scenarios Included

- `wildlife_monitoring.yaml` — sensor array for wildlife acoustic monitoring in a forest clearing

## Phase 2 (planned)

Port visualization layer to Unreal Engine 5. Engine unchanged.

## License

MIT
