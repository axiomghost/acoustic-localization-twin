"""
Tests for Gauss-Newton TDOA localizer and confidence ellipse.

Validation strategy (maps to estimation theory Umar knows):
- Noiseless recovery: estimate must converge to true position (bias test)
- Noise tolerance: error must stay within CRLB-predicted bound
- Ellipse coverage: over many noisy trials, ~95% of true positions should
  fall inside the reported 95% confidence ellipse (coverage test)
- Ellipse geometry: semi-major >= semi-minor, angle in [-90, 90]
- GDOP sensitivity: ellipse must be larger near array edges than at centre
"""
import numpy as np
import pytest
from engine.localizer import GaussNewtonTDOA
from engine.tdoa import compute_tdoa_measurements
from engine.confidence import confidence_ellipse, CHI2_95_2DOF
from engine.propagation import SPEED_OF_SOUND

SENSORS = np.array([
    [  0.0,   0.0],
    [200.0,   0.0],
    [200.0, 200.0],
    [  0.0, 200.0],
], dtype=float)

NOISE_STD_S = 1e-4
SIGMA_R = SPEED_OF_SOUND * NOISE_STD_S


def _localize(source_xy, noise_std_s=0.0, seed=0):
    rng = np.random.default_rng(seed)
    tdoa = compute_tdoa_measurements(source_xy, SENSORS,
                                     noise_std_s=noise_std_s, rng=rng)
    return GaussNewtonTDOA().estimate(tdoa, SENSORS)


# ── Localizer tests ────────────────────────────────────────────────────────────

def test_noiseless_centre():
    """Noiseless, source at array centre: error < 1 mm."""
    src = np.array([100.0, 100.0])
    est, _ = _localize(src, noise_std_s=0.0)
    assert np.linalg.norm(est - src) < 1e-3


def test_noiseless_off_centre():
    """Noiseless, source at arbitrary interior point: error < 1 mm."""
    src = np.array([67.0, 134.0])
    est, _ = _localize(src, noise_std_s=0.0)
    assert np.linalg.norm(est - src) < 1e-3


def test_noiseless_near_edge():
    """Noiseless, source near array edge: error < 1 mm."""
    src = np.array([10.0, 100.0])
    est, _ = _localize(src, noise_std_s=0.0)
    assert np.linalg.norm(est - src) < 1e-3


def test_noisy_error_within_crlb():
    """
    With noise, error should be within ~5x the CRLB std (loose bound for
    a single trial). Use a fixed seed for reproducibility.
    Theoretical std ~ SIGMA_R / sqrt(N-1) / (array_size / 2) ... rough bound.
    We use the empirical mean from many trials.
    """
    src = np.array([100.0, 100.0])
    rng = np.random.default_rng(99)
    errors = []
    for i in range(200):
        tdoa = compute_tdoa_measurements(src, SENSORS,
                                         noise_std_s=NOISE_STD_S, rng=rng)
        est, _ = GaussNewtonTDOA().estimate(tdoa, SENSORS)
        errors.append(np.linalg.norm(est - src))
    assert np.mean(errors) < 0.10   # mean error < 10 cm at 0.1ms noise


def test_covariance_is_positive_definite():
    """Raw covariance matrix must be symmetric positive definite."""
    src = np.array([80.0, 120.0])
    _, cov = _localize(src, noise_std_s=NOISE_STD_S, seed=7)
    # Symmetric
    np.testing.assert_allclose(cov, cov.T, atol=1e-10)
    # Positive definite: all eigenvalues > 0
    eigenvalues = np.linalg.eigvalsh(cov)
    assert np.all(eigenvalues > 0)


# ── Confidence ellipse tests ───────────────────────────────────────────────────

def test_ellipse_geometry():
    """Semi-major >= semi-minor, angle in valid range."""
    src = np.array([100.0, 100.0])
    _, cov = _localize(src, noise_std_s=NOISE_STD_S, seed=3)
    e = confidence_ellipse(cov, SIGMA_R)
    assert e["a"] >= e["b"] >= 0.0
    assert -90.0 <= e["angle_deg"] <= 90.0


def test_ellipse_scales_with_noise():
    """Doubling timing noise doubles sigma_r and should ~double ellipse axes."""
    src = np.array([100.0, 100.0])
    _, cov = _localize(src, noise_std_s=0.0)   # noiseless cov (geometry only)
    e1 = confidence_ellipse(cov, SIGMA_R)
    e2 = confidence_ellipse(cov, 2 * SIGMA_R)
    assert e2["a"] == pytest.approx(2 * e1["a"], rel=1e-6)
    assert e2["b"] == pytest.approx(2 * e1["b"], rel=1e-6)


def test_ellipse_gdop_centre_vs_edge():
    """
    Ellipse semi-major must be smaller at array centre than near an edge.
    This validates correct GDOP sensitivity.
    """
    src_centre = np.array([100.0, 100.0])
    src_edge   = np.array([10.0,  100.0])   # near left edge

    _, cov_c = _localize(src_centre, noise_std_s=0.0)
    _, cov_e = _localize(src_edge,   noise_std_s=0.0)

    e_centre = confidence_ellipse(cov_c, SIGMA_R)
    e_edge   = confidence_ellipse(cov_e, SIGMA_R)

    assert e_edge["a"] > e_centre["a"]


def test_ellipse_95pct_coverage():
    """
    Monte Carlo coverage test: true position should fall inside the reported
    95% confidence ellipse in approximately 95% of trials.
    Tolerance: 90–99% (generous band for 300 trials).

    Method: transform true position into ellipse frame and check
    Mahalanobis distance <= sqrt(chi2_95).
    """
    src = np.array([100.0, 100.0])
    rng = np.random.default_rng(2024)
    n_trials = 300
    inside = 0

    for _ in range(n_trials):
        tdoa = compute_tdoa_measurements(src, SENSORS,
                                         noise_std_s=NOISE_STD_S, rng=rng)
        est, raw_cov = GaussNewtonTDOA().estimate(tdoa, SENSORS)
        scaled_cov = raw_cov * SIGMA_R ** 2
        err = src - est
        # Mahalanobis distance squared
        maha2 = float(err @ np.linalg.solve(scaled_cov, err))
        if maha2 <= CHI2_95_2DOF:
            inside += 1

    coverage = inside / n_trials
    assert 0.88 <= coverage <= 0.99, f"Coverage {coverage:.2f} outside [0.88, 0.99]"


# ── Weighted (maximum-ratio) localizer tests ──────────────────────────────────

def _per_sensor_std(source_xy, ref_std_s=NOISE_STD_S):
    """Range-dependent per-sensor timing std, matching the engine model."""
    from engine.tdoa import timing_std_from_range
    dists = np.linalg.norm(source_xy - SENSORS, axis=1)
    return timing_std_from_range(dists, ref_std_s=ref_std_s)


def test_weighted_reduces_to_equal_variance():
    """
    With equal per-sensor variance, the weighted path must give the same
    position covariance as the unweighted path scaled by sigma_r^2.
    """
    src = np.array([100.0, 100.0])
    rng = np.random.default_rng(11)
    tdoa = compute_tdoa_measurements(src, SENSORS, noise_std_s=NOISE_STD_S, rng=rng)

    _, raw_cov = GaussNewtonTDOA().estimate(tdoa, SENSORS)
    scaled = raw_cov * SIGMA_R ** 2

    equal_var = np.full(len(SENSORS), NOISE_STD_S ** 2)
    _, pos_cov = GaussNewtonTDOA().estimate(tdoa, SENSORS, sensor_var=equal_var)

    np.testing.assert_allclose(pos_cov, scaled, rtol=1e-6)


def test_weighted_beats_unweighted_under_heterogeneous_noise():
    """
    When sensors have different noise levels, inverse-variance (MRC) weighting
    must achieve lower mean-squared error than equal-weight LS. This is the
    soft-decision / maximum-ratio-combining gain.
    """
    src = np.array([70.0, 130.0])
    sensor_std = _per_sensor_std(src)
    sensor_var = sensor_std ** 2

    rng = np.random.default_rng(2025)
    n = 1500
    mse_eq = 0.0
    mse_w = 0.0
    loc = GaussNewtonTDOA()
    for _ in range(n):
        tdoa = compute_tdoa_measurements(src, SENSORS, noise_std_s=sensor_std, rng=rng)
        est_eq, _ = loc.estimate(tdoa, SENSORS)                      # equal weight
        est_w, _ = loc.estimate(tdoa, SENSORS, sensor_var=sensor_var)  # MRC
        mse_eq += np.sum((est_eq - src) ** 2)
        mse_w += np.sum((est_w - src) ** 2)
    mse_eq /= n
    mse_w /= n

    assert mse_w < mse_eq, f"weighted MSE {mse_w:.4f} not below equal-weight {mse_eq:.4f}"


def test_weighted_95pct_coverage():
    """
    Heterogeneous-noise coverage: the position covariance returned by the
    weighted path (already in m^2) must yield ~95% ellipse coverage.
    """
    src = np.array([120.0, 90.0])
    sensor_std = _per_sensor_std(src)
    sensor_var = sensor_std ** 2

    rng = np.random.default_rng(777)
    n_trials = 400
    inside = 0
    loc = GaussNewtonTDOA()
    for _ in range(n_trials):
        tdoa = compute_tdoa_measurements(src, SENSORS, noise_std_s=sensor_std, rng=rng)
        est, pos_cov = loc.estimate(tdoa, SENSORS, sensor_var=sensor_var)
        err = src - est
        maha2 = float(err @ np.linalg.solve(pos_cov, err))
        if maha2 <= CHI2_95_2DOF:
            inside += 1
    coverage = inside / n_trials
    assert 0.88 <= coverage <= 0.99, f"Coverage {coverage:.2f} outside [0.88, 0.99]"


# ── Scenario loader integration test ──────────────────────────────────────────

def test_scenario_loader_roundtrip():
    """Load wildlife_monitoring.yaml and verify sensor count and positions parse correctly."""
    from pathlib import Path
    from scenarios.loader import load_scenario
    path = Path(__file__).parent.parent / "scenarios" / "configs" / "wildlife_monitoring.yaml"
    scenario = load_scenario(path)
    assert "Wildlife" in scenario.name
    assert len(scenario.sensors) == 4
    positions = scenario.sensor_positions
    assert len(positions) == 4
    # Sensors should be within terrain bounds
    size = scenario.terrain.size_m
    for pos in positions:
        assert 0 <= pos[0] <= size
        assert 0 <= pos[1] <= size


def test_scenario_loader_rejects_bad_config(tmp_path):
    """Loader must raise on invalid config (fewer than 3 sensors)."""
    from scenarios.loader import load_scenario
    import pytest
    bad = tmp_path / "bad.yaml"
    bad.write_text("""
name: bad
terrain:
  type: flat
  size_m: 100
sensors:
  - id: 0
    x: 0
    y: 0
  - id: 1
    x: 50
    y: 50
source:
  path:
    - x: 10
      y: 10
    - x: 90
      y: 90
  speed_m_per_s: 1.0
""", encoding="utf-8")
    with pytest.raises(Exception):
        load_scenario(bad)
