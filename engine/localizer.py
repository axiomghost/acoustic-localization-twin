"""
TDOA-based source localizer — weighted least-squares hyperbolic intersection.

Algorithm: Gauss-Newton with the correct TDOA noise covariance (DEC-007).

Each TDOA measurement is tdoa[i] = toa[i+1] - toa[0].
Since sensor-0 appears in all differences, the (N-1) TDOA measurements are
correlated. Their noise covariance in range units is:

    C = sigma_r^2 * M,   M = I + 1*1^T   (N-1) x (N-1)

where 1 is the all-ones vector. By Sherman-Morrison:

    M^{-1} = I - (1/N) * 1*1^T

The weighted Gauss-Newton update and covariance are:

    delta = (J^T M^{-1} J)^{-1} J^T M^{-1} (-r)
    cov(x) = sigma_r^2 * (J^T M^{-1} J)^{-1}

We return the raw (J^T M^{-1} J)^{-1} — caller scales by sigma_r^2.
"""
from __future__ import annotations
import numpy as np
from typing import Protocol


class Localizer(Protocol):
    def estimate(
        self, tdoa: np.ndarray, sensor_positions: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return (position_estimate [2], raw_cov [2x2]). Caller scales cov by sigma_r^2."""
        ...


class GaussNewtonTDOA:
    def __init__(
        self,
        speed_of_sound: float = 343.0,
        max_iter: int = 50,
        tol: float = 1e-6,
    ):
        self.c = speed_of_sound
        self.max_iter = max_iter
        self.tol = tol

    def estimate(
        self,
        tdoa: np.ndarray,
        sensor_positions: np.ndarray,
        sensor_var: np.ndarray | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        tdoa: shape (N-1,)  — TDOA differences relative to sensor 0
        sensor_positions: shape (N, 2)
        sensor_var: optional per-sensor arrival-time noise variance (s^2), length N.

        The weighting matrix W is the inverse of the TDOA measurement covariance —
        this is the maximum-ratio / soft-decision step (give noisy sensors less say):

          - sensor_var is None  (equal variance): W = M^{-1} = I - (1/N)*ones.
            Returns raw_cov = (J^T W J)^{-1}, DIMENSIONLESS. Caller scales by sigma_r^2.

          - sensor_var given (heterogeneous): the TDOA covariance in range units is
            C_r = c^2 * (diag(var[1:]) + var[0]*ones), so W = C_r^{-1}.
            Returns pos_cov = (J^T W J)^{-1}, already in m^2 (do NOT scale again).
        """
        N = len(sensor_positions)
        s0 = sensor_positions[0]
        sensors = sensor_positions[1:]       # (N-1, 2)
        d_meas = tdoa * self.c               # measured range differences (metres)

        if sensor_var is None:
            # Equal-variance case: W = M^{-1} via Sherman-Morrison (dimensionless).
            W = np.eye(N - 1) - np.ones((N - 1, N - 1)) / N
        else:
            # Heterogeneous case: build the true TDOA covariance and invert it.
            var = np.asarray(sensor_var, dtype=float)
            cov_tau = np.diag(var[1:]) + var[0] * np.ones((N - 1, N - 1))  # s^2
            cov_r = (self.c ** 2) * cov_tau                                # m^2
            W = np.linalg.inv(cov_r)

        # Initial guess: centroid of array
        x = sensor_positions.mean(axis=0).copy().astype(float)

        JtWJ = np.eye(2)  # initialised; will be set in first iteration
        for _ in range(self.max_iter):
            r0 = np.linalg.norm(x - s0)
            ri = np.linalg.norm(x - sensors, axis=1)   # (N-1,)

            residuals = (ri - r0) - d_meas              # (N-1,)

            # Jacobian d(residuals)/d(x), shape (N-1, 2)
            J = (x - sensors) / ri[:, None] - (x - s0) / r0

            JtWJ = J.T @ W @ J
            delta = np.linalg.solve(JtWJ, J.T @ W @ (-residuals))
            x = x + delta

            if np.linalg.norm(delta) < self.tol:
                break

        # Covariance: (J^T W J)^{-1}. Dimensionless if sensor_var is None
        # (caller scales by sigma_r^2); already m^2 if sensor_var was given.
        try:
            cov = np.linalg.inv(JtWJ)
        except np.linalg.LinAlgError:
            cov = np.eye(2) * 1e6

        return x, cov
