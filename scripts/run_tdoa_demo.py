"""
Step 1 smoke test — synthetic TDOA localization on flat terrain.

4 sensors at fixed positions, 1 source at known location.
Runs 20 ticks along a straight path, prints localization error each tick.
No visualization yet — just algorithm validation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from engine.propagation import SimplePropagation, SPEED_OF_SOUND
from engine.tdoa import compute_tdoa_measurements
from engine.localizer import GaussNewtonTDOA
from engine.confidence import confidence_ellipse

# ── Sensor array: 4 sensors in a 200m square ──────────────────────────────────
SENSORS = np.array([
    [  0.0,   0.0],   # sensor 0 (reference)
    [200.0,   0.0],   # sensor 1
    [200.0, 200.0],   # sensor 2
    [  0.0, 200.0],   # sensor 3
], dtype=float)

# ── Source path: straight line across the monitored area ─────────────────────
SOURCE_START = np.array([ 50.0,  80.0])
SOURCE_END   = np.array([160.0, 130.0])
N_TICKS      = 20

NOISE_STD_S  = 1e-4   # 0.1 ms timing noise
SIGMA_R      = SPEED_OF_SOUND * NOISE_STD_S   # ~34 mm range noise

propagation = SimplePropagation()
localizer   = GaussNewtonTDOA()
rng         = np.random.default_rng(seed=42)

print(f"{'Tick':>4} | {'True (x,y)':>22} | {'Est  (x,y)':>22} | {'Error (m)':>10} | {'Ellipse a×b (m)':>18}")
print("-" * 90)

errors = []
for tick in range(N_TICKS):
    t = tick / (N_TICKS - 1)
    true_xy = SOURCE_START + t * (SOURCE_END - SOURCE_START)

    tdoa = compute_tdoa_measurements(
        true_xy, SENSORS,
        propagation=propagation,
        noise_std_s=NOISE_STD_S,
        rng=rng,
    )

    est_xy, raw_cov = localizer.estimate(tdoa, SENSORS)
    error = float(np.linalg.norm(est_xy - true_xy))
    ellipse = confidence_ellipse(raw_cov, SIGMA_R)
    errors.append(error)

    print(
        f"{tick:>4} | "
        f"({true_xy[0]:8.2f}, {true_xy[1]:8.2f}) | "
        f"({est_xy[0]:8.2f}, {est_xy[1]:8.2f}) | "
        f"{error:>10.3f} | "
        f"{ellipse['a']:7.3f} × {ellipse['b']:7.3f}"
    )

print("-" * 90)
print(f"Mean error: {np.mean(errors):.3f} m   |   Max error: {np.max(errors):.3f} m")
print(f"\nAlgorithm: Gauss-Newton TDOA (linearized hyperbolic intersection)")
print(f"Noise model: Gaussian timing noise std = {NOISE_STD_S*1000:.2f} ms  ->  range noise std = {SIGMA_R*100:.1f} cm")
