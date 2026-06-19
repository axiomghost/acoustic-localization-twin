"""TDOA measurement generation with additive Gaussian noise.

Noise can be homogeneous (one std for all sensors) or heterogeneous
(per-sensor std). Heterogeneous noise is the realistic case: a sensor
farther from the source receives a weaker signal, so its arrival-time
estimate is noisier. See timing_std_from_range (DEC-009).
"""
from __future__ import annotations
import numpy as np
from .propagation import PropagationModel, SimplePropagation

# Reference point for the range -> timing-noise model (DEC-009).
REF_DISTANCE_M = 100.0   # distance at which timing std equals the nominal value
REF_SNR_DB = 20.0        # display SNR at REF_DISTANCE_M


def timing_std_from_range(
    distances: np.ndarray,
    ref_std_s: float = 1e-4,
    ref_distance_m: float = REF_DISTANCE_M,
) -> np.ndarray:
    """
    Per-sensor arrival-time noise std as a function of source-sensor range.

    Physical basis: received amplitude falls as 1/r, so SNR_linear ~ 1/r^2.
    A matched filter's time-delay CRLB gives std(tau) ~ 1/sqrt(SNR_linear) ~ r.
    Hence timing std grows linearly with range:

        sigma_i = ref_std_s * (dist_i / ref_distance_m)

    This is the mechanism that makes sensors heterogeneous and motivates
    inverse-variance (maximum-ratio) weighting in the localizer.
    """
    return ref_std_s * (np.asarray(distances, dtype=float) / ref_distance_m)


def snr_db_from_range(
    distances: np.ndarray,
    ref_distance_m: float = REF_DISTANCE_M,
    ref_snr_db: float = REF_SNR_DB,
) -> np.ndarray:
    """Display SNR consistent with the timing-noise model: SNR_dB falls 20 dB/decade of range."""
    return ref_snr_db - 20.0 * np.log10(np.asarray(distances, dtype=float) / ref_distance_m)


def compute_tdoa_measurements(
    source_xy: np.ndarray,
    sensor_positions: np.ndarray,   # shape (N, 2)
    propagation: PropagationModel | None = None,
    noise_std_s: float | np.ndarray = 1e-4,   # scalar or per-sensor array, length N
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """
    Return TDOA vector of length N-1: tdoa[i] = toa[i+1] - toa[0].
    Sensor 0 is the reference.

    noise_std_s may be a scalar (same noise on every sensor) or an array of
    length N (per-sensor noise). numpy broadcasts both cases.
    """
    if propagation is None:
        propagation = SimplePropagation()
    if rng is None:
        rng = np.random.default_rng()

    N = len(sensor_positions)
    toa = np.array([propagation.compute_toa(source_xy, sensor_positions[i]) for i in range(N)])
    toa += rng.normal(0.0, 1.0, size=N) * np.asarray(noise_std_s)   # timing noise (scalar or per-sensor)
    return toa[1:] - toa[0]   # TDOA relative to sensor 0
