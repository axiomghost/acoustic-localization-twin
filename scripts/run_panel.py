"""
Step 6: Rich terminal panel — run this in a second terminal alongside run_live.py.

Usage:
    # Terminal 1:
    python scripts/run_live.py

    # Terminal 2:
    python scripts/run_panel.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scenarios.loader import load_scenario
from dashboard.panel import run_panel

SCENARIO_PATH = Path(__file__).parent.parent / "scenarios" / "configs" / "wildlife_monitoring.yaml"

scenario = load_scenario(SCENARIO_PATH)
print(f"Panel watching: {scenario.name}")
print("Waiting for engine state... (start run_live.py in another terminal)")
print("Press Ctrl-C to exit.\n")

run_panel(scenario.name)
