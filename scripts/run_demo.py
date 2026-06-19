"""
Step 7: Full demo launcher — single command to start everything.

Launches the Rich terminal panel in a new PowerShell window, then runs
the live 3D PyVista render in the current terminal.

Usage:
    python scripts/run_demo.py
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
PYTHON = sys.executable

print("=" * 60)
print("  Acoustic Source Localization — Digital Twin Demo")
print("=" * 60)
print()
print("Starting Rich terminal panel in a new window...")

# Open panel in a new PowerShell window (Windows)
subprocess.Popen(
    [
        "powershell", "-NoExit", "-Command",
        f'cd "{ROOT}"; & "{PYTHON}" scripts/run_panel.py',
    ],
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

print("Starting 3D live render (close the PyVista window to exit)...")
print()

# Run the 3D render in the current process — blocks until window is closed
import importlib.util, os
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from scenarios.loader import load_scenario
from engine.engine import Engine
from visualization.live_renderer import LiveRenderer

SCENARIO = ROOT / "scenarios" / "configs" / "wildlife_monitoring.yaml"
scenario = load_scenario(SCENARIO)

print(f"Scenario : {scenario.name}")
print(f"Source   : ({scenario.source.path[0].x}, {scenario.source.path[0].y})"
      f" -> ({scenario.source.path[-1].x}, {scenario.source.path[-1].y})"
      f" at {scenario.source.speed_m_per_s} m/s")
print(f"Sensors  : {len(scenario.sensor_positions)}")
print(f"Tick     : {scenario.sim.tick_interval_s}s")
print()

engine = Engine(scenario, seed=42)
renderer = LiveRenderer(scenario)
renderer.run(engine)

print()
print("Demo complete.")
