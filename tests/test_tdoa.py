"""Tests for TDOA measurement generation."""
import numpy as np
import pytest
from engine.tdoa import compute_tdoa_measurements
from engine.propagation import SimplePropagation, SPEED_OF_SOUND

SENSORS = np.array([
    [  0.0,   0.0],
    [200.0,   0.0],
    [200.0, 200.0],
    [  0.0, 200.0],
], dtype=float)


def test_tdoa_length():
    """TDOA vector length == N_sensors - 1."""
    src = np.array([100.0, 100.0])
    tdoa = compute_tdoa_measurements(src, SENSORS, noise_std_s=0.0,
                                     rng=np.random.default_rng(0))
    assert len(tdoa) == len(SENSORS) - 1


def test_tdoa_zero_noise_symmetric_source():
    """Source equidistant from all sensors => all TDOAs == 0 (no noise)."""
    src = np.array([100.0, 100.0])   # centre of square array
    tdoa = compute_tdoa_measurements(src, SENSORS, noise_std_s=0.0,
                                     rng=np.random.default_rng(0))
    np.testing.assert_allclose(tdoa, 0.0, atol=1e-12)


def test_tdoa_zero_noise_known_geometry():
    """
    Source at (0, 100): equidistant from sensor-0 and sensor-3 (both at x=0),
    so tdoa[2] (sensor-3 vs sensor-0) should be ~0.
    """
    src = np.array([0.0, 100.0])
    tdoa = compute_tdoa_measurements(src, SENSORS, noise_std_s=0.0,
                                     rng=np.random.default_rng(0))
    # sensor-3 is at (0, 200), sensor-0 at (0, 0): both 100m from src
    assert tdoa[2] == pytest.approx(0.0, abs=1e-12)


def test_tdoa_sign_convention():
    """
    Source closer to sensor-1 than sensor-0 => tdoa[0] < 0
    (sensor-1 receives signal earlier than sensor-0).
    """
    src = np.array([180.0, 10.0])   # near sensor-1 at (200, 0)
    tdoa = compute_tdoa_measurements(src, SENSORS, noise_std_s=0.0,
                                     rng=np.random.default_rng(0))
    # tdoa[0] = toa[1] - toa[0]; toa[1] < toa[0] => tdoa[0] < 0
    assert tdoa[0] < 0.0


def test_tdoa_noise_statistics():
    """
    With noise, TDOA values should scatter around noiseless values.
    Over many samples, mean should be close to noiseless (unbiased noise).
    """
    src = np.array([120.0, 80.0])
    rng = np.random.default_rng(42)
    noiseless = compute_tdoa_measurements(src, SENSORS, noise_std_s=0.0,
                                          rng=np.random.default_rng(0))
    noisy_samples = np.array([
        compute_tdoa_measurements(src, SENSORS, noise_std_s=1e-4, rng=rng)
        for _ in range(500)
    ])
    # Mean should be within 3*std/sqrt(500) of noiseless
    mean_error = np.abs(noisy_samples.mean(axis=0) - noiseless)
    assert np.all(mean_error < 3 * 1e-4 / np.sqrt(500))


def test_tdoa_physical_units():
    """TDOA range-equivalent (tdoa * c) must not exceed sensor baseline."""
    src = np.array([50.0, 50.0])
    tdoa = compute_tdoa_measurements(src, SENSORS, noise_std_s=0.0,
                                     rng=np.random.default_rng(0))
    max_baseline = 200.0 * np.sqrt(2)   # diagonal of 200m square
    assert np.all(np.abs(tdoa * SPEED_OF_SOUND) <= max_baseline + 1e-9)
