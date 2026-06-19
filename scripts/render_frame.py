"""
Step 4: render a single static 3D frame of the localization result.

Loads wildlife_monitoring.yaml, runs one localization at the source
midpoint, and opens a PyVista window showing terrain, sensors,
true position, estimate, and 95% confidence ellipse.

Usage:
    python scripts/render_frame.py              # interactive window
    python scripts/render_frame.py --screenshot # save PNG and exit
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import numpy as np
from scenarios.loader import load_scenario
from engine.propagation import SimplePropagation
from engine.tdoa import compute_tdoa_measurements
from engine.localizer import GaussNewtonTDOA
from engine.confidence import confidence_ellipse
from visualization.renderer import render_single_frame

SCENARIO_PATH = Path(__file__).parent.parent / "scenarios" / "configs" / "wildlife_monitoring.yaml"

parser = argparse.ArgumentParser()
parser.add_argument("--screenshot", action="store_true",
                    help="Save PNG to media/ and exit instead of opening window")
parser.add_argument("--out", default=None,
                    help="Override output PNG path (used with --screenshot)")
args = parser.parse_args()

# ── Load scenario ─────────────────────────────────────────────────────────────
scenario = load_scenario(SCENARIO_PATH)
sensors  = np.array(scenario.sensor_positions, dtype=float)
noise_std_s = scenario.timing_noise_std_s
sigma_r     = scenario.propagation.speed_of_sound_m_per_s * noise_std_s

# ── Pick source midpoint ──────────────────────────────────────────────────────
src_start = np.array([scenario.source.path[0].x, scenario.source.path[0].y])
src_end   = np.array([scenario.source.path[-1].x, scenario.source.path[-1].y])
true_xy   = (src_start + src_end) / 2.0

# ── Run localization ──────────────────────────────────────────────────────────
rng = np.random.default_rng(seed=42)
tdoa = compute_tdoa_measurements(
    true_xy, sensors,
    propagation=SimplePropagation(scenario.propagation.speed_of_sound_m_per_s),
    noise_std_s=noise_std_s,
    rng=rng,
)
est_xy, raw_cov = GaussNewtonTDOA(
    speed_of_sound=scenario.propagation.speed_of_sound_m_per_s
).estimate(tdoa, sensors)

ellipse = confidence_ellipse(raw_cov, sigma_r)
error_m = float(np.linalg.norm(est_xy - true_xy))

print(f"Scenario  : {scenario.name}")
print(f"True pos  : ({true_xy[0]:.2f}, {true_xy[1]:.2f}) m")
print(f"Est pos   : ({est_xy[0]:.2f}, {est_xy[1]:.2f}) m")
print(f"Error     : {error_m*100:.2f} cm")
print(f"Ellipse   : {ellipse['a']*100:.1f} x {ellipse['b']*100:.1f} cm @ {ellipse['angle_deg']:.1f} deg")
print()

screenshot_path = None
if args.screenshot:
    if args.out:
        screenshot_path = args.out
        Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
    else:
        media_dir = Path(__file__).parent.parent / "media"
        media_dir.mkdir(exist_ok=True)
        screenshot_path = str(media_dir / "step4_single_frame.png")

print("Opening PyVista window..." if not args.screenshot else "Rendering screenshot...")
render_single_frame(
    scenario=scenario,
    true_xy=true_xy,
    est_xy=est_xy,
    ellipse=ellipse,
    screenshot_path=screenshot_path,
    interactive=not args.screenshot,
)
