"""
Step 5: live animated render — source moves, estimate tracks it in real time.

Usage:
    python scripts/run_live.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scenarios.loader import load_scenario
from engine.engine import Engine
from visualization.live_renderer import LiveRenderer

SCENARIO_PATH = Path(__file__).parent.parent / "scenarios" / "configs" / "wildlife_monitoring.yaml"

scenario = load_scenario(SCENARIO_PATH)
print(f"Scenario : {scenario.name}")
print(f"Source   : {scenario.source.path[0].x},{scenario.source.path[0].y}"
      f" -> {scenario.source.path[-1].x},{scenario.source.path[-1].y}"
      f" at {scenario.source.speed_m_per_s} m/s")
print(f"Tick     : {scenario.sim.tick_interval_s}s interval")
print()
print("Starting engine + renderer. Close the window to exit.")

engine   = Engine(scenario, seed=42)
renderer = LiveRenderer(scenario)
renderer.run(engine)
