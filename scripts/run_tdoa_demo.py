"""
Step 2 smoke test — TDOA localization driven by scenario YAML config.

Loads wildlife_monitoring.yaml, runs localization along the source path,
prints per-tick results and summary statistics.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from scenarios.loader import load_scenario
from engine.propagation import SimplePropagation
from engine.tdoa import compute_tdoa_measurements
from engine.localizer import GaussNewtonTDOA
from engine.confidence import confidence_ellipse

SCENARIO_PATH = Path(__file__).parent.parent / "scenarios" / "configs" / "wildlife_monitoring.yaml"
N_TICKS = 20

# ── Load scenario ─────────────────────────────────────────────────────────────
scenario = load_scenario(SCENARIO_PATH)
print(f"Scenario : {scenario.name}")
print(f"Use case : {scenario.use_case}")
print(f"Terrain  : {scenario.terrain.type}, {scenario.terrain.size_m}m x {scenario.terrain.size_m}m")
print(f"Sensors  : {len(scenario.sensors)}")
print(f"Noise    : {scenario.propagation.timing_noise_std_ms} ms timing std")
print()

sensors = np.array(scenario.sensor_positions, dtype=float)
src_start = np.array([scenario.source.path[0].x, scenario.source.path[0].y])
src_end   = np.array([scenario.source.path[-1].x, scenario.source.path[-1].y])
noise_std_s = scenario.timing_noise_std_s
sigma_r = scenario.propagation.speed_of_sound_m_per_s * noise_std_s

propagation = SimplePropagation(scenario.propagation.speed_of_sound_m_per_s)
localizer   = GaussNewtonTDOA(speed_of_sound=scenario.propagation.speed_of_sound_m_per_s)
rng         = np.random.default_rng(seed=42)

# ── Run ticks ─────────────────────────────────────────────────────────────────
print(f"{'Tick':>4} | {'True (x,y)':>22} | {'Est  (x,y)':>22} | {'Error (m)':>10} | Ellipse a x b (m)")
print("-" * 92)

errors = []
for tick in range(N_TICKS):
    t = tick / (N_TICKS - 1)
    true_xy = src_start + t * (src_end - src_start)

    tdoa = compute_tdoa_measurements(
        true_xy, sensors,
        propagation=propagation,
        noise_std_s=noise_std_s,
        rng=rng,
    )

    est_xy, raw_cov = localizer.estimate(tdoa, sensors)
    error = float(np.linalg.norm(est_xy - true_xy))
    ellipse = confidence_ellipse(raw_cov, sigma_r)
    errors.append(error)

    print(
        f"{tick:>4} | "
        f"({true_xy[0]:8.2f}, {true_xy[1]:8.2f}) | "
        f"({est_xy[0]:8.2f}, {est_xy[1]:8.2f}) | "
        f"{error:>10.3f} | "
        f"{ellipse['a']:7.3f} x {ellipse['b']:7.3f}"
    )

print("-" * 92)
print(f"Mean error: {np.mean(errors):.3f} m   |   Max error: {np.max(errors):.3f} m")
print(f"Range noise std: {sigma_r*100:.1f} cm  (from {noise_std_s*1000:.2f} ms timing noise)")
