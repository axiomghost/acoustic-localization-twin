"""TDOA measurement generation with additive Gaussian noise."""
from __future__ import annotations
import numpy as np
from .propagation import PropagationModel, SimplePropagation


def compute_tdoa_measurements(
    source_xy: np.ndarray,
    sensor_positions: np.ndarray,   # shape (N, 2)
    propagation: PropagationModel | None = None,
    noise_std_s: float = 1e-4,      # ~0.1 ms timing noise
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """
    Return TDOA vector of length N-1: tdoa[i] = toa[i+1] - toa[0].
    Sensor 0 is the reference.
    """
    if propagation is None:
        propagation = SimplePropagation()
    if rng is None:
        rng = np.random.default_rng()

    N = len(sensor_positions)
    toa = np.array([propagation.compute_toa(source_xy, sensor_positions[i]) for i in range(N)])
    toa += rng.normal(0.0, noise_std_s, size=N)   # timing noise
    return toa[1:] - toa[0]   # TDOA relative to sensor 0
