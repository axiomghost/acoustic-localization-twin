"""Acoustic propagation model — pluggable via Protocol."""
from __future__ import annotations
from typing import Protocol
import numpy as np

SPEED_OF_SOUND = 343.0  # m/s at ~20°C


class PropagationModel(Protocol):
    def compute_toa(self, source_xy: np.ndarray, sensor_xy: np.ndarray) -> float:
        """Return time of arrival in seconds."""
        ...


class SimplePropagation:
    """Constant speed of sound, no terrain occlusion."""

    def __init__(self, speed: float = SPEED_OF_SOUND):
        self.speed = speed

    def compute_toa(self, source_xy: np.ndarray, sensor_xy: np.ndarray) -> float:
        dist = float(np.linalg.norm(source_xy - sensor_xy))
        return dist / self.speed
