"""
TDOA-based source localizer — least-squares hyperbolic intersection.

Algorithm: linearize the hyperbolic equations around an initial guess
(centroid of sensor array) and solve iteratively via Gauss-Newton.
This is equivalent to the Fang / Chan-Ho linearization approach but
implemented directly so the math is transparent.

Each TDOA measurement defines a hyperboloid:
    ||x - s_i|| - ||x - s_0|| = c * tdoa_i

We linearize around current estimate x_k, form the Jacobian, and
update: x_{k+1} = x_k + (J^T J)^{-1} J^T r
"""
from __future__ import annotations
import numpy as np
from typing import Protocol


class Localizer(Protocol):
    def estimate(
        self, tdoa: np.ndarray, sensor_positions: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return (position_estimate [2], covariance [2x2])."""
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
        self, tdoa: np.ndarray, sensor_positions: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        tdoa: shape (N-1,)  — differences relative to sensor 0
        sensor_positions: shape (N, 2)
        Returns (xy_est [2], cov [2x2])
        """
        s0 = sensor_positions[0]
        sensors = sensor_positions[1:]   # (N-1, 2)
        d_meas = tdoa * self.c           # measured range differences (metres)

        # Initial guess: centroid of array
        x = sensor_positions.mean(axis=0).copy().astype(float)

        for _ in range(self.max_iter):
            r0 = np.linalg.norm(x - s0)
            ri = np.linalg.norm(x - sensors, axis=1)   # (N-1,)

            # Residuals: predicted range diff - measured range diff
            residuals = (ri - r0) - d_meas              # (N-1,)

            # Jacobian: d(residuals)/d(x)  shape (N-1, 2)
            J = (x - sensors) / ri[:, None] - (x - s0) / r0

            # Gauss-Newton step
            JtJ = J.T @ J
            delta = np.linalg.solve(JtJ, J.T @ (-residuals))
            x = x + delta

            if np.linalg.norm(delta) < self.tol:
                break

        # Covariance estimate via linearized propagation:
        # cov(x) ≈ (J^T J)^{-1} * sigma_r^2
        # where sigma_r = c * noise_std_s (range noise from timing noise)
        # We return the raw (J^T J)^{-1} — caller scales by sigma_r^2
        try:
            cov = np.linalg.inv(JtJ)
        except np.linalg.LinAlgError:
            cov = np.eye(2) * 1e6

        return x, cov
