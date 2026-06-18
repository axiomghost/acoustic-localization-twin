"""
95% confidence ellipse from 2D position covariance matrix.

Given cov = (J^T J)^{-1} * sigma_r^2, compute the ellipse parameters
via eigendecomposition. The chi-squared threshold for 95% CI in 2D is 5.991.
"""
from __future__ import annotations
import numpy as np


CHI2_95_2DOF = 5.991


def confidence_ellipse(cov: np.ndarray, sigma_r: float) -> dict:
    """
    cov: raw (J^T J)^{-1} from localizer (unitless, needs scaling)
    sigma_r: range-domain noise std (metres) = c * timing_noise_std_s

    Returns dict with keys: cx, cy (set to 0—caller adds estimate),
    a (semi-major), b (semi-minor), angle_deg (rotation from x-axis).
    """
    scaled_cov = cov * sigma_r ** 2
    eigenvalues, eigenvectors = np.linalg.eigh(scaled_cov)
    # eigh returns ascending order; largest is semi-major
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]

    # Clip negative eigenvalues from numerical noise
    eigenvalues = np.maximum(eigenvalues, 0.0)

    a = np.sqrt(CHI2_95_2DOF * eigenvalues[0])
    b = np.sqrt(CHI2_95_2DOF * eigenvalues[1])
    angle_deg = float(np.degrees(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0])))
    # Normalise to [-90, 90]: ellipse has 180-degree symmetry
    if angle_deg > 90.0:
        angle_deg -= 180.0
    elif angle_deg < -90.0:
        angle_deg += 180.0

    return {"a": float(a), "b": float(b), "angle_deg": angle_deg}
