"""Acoustic source — moves along a waypoint path at configured speed."""
from __future__ import annotations
import numpy as np


class AcousticSource:
    def __init__(self, waypoints: list[list[float]], speed_m_per_s: float):
        self.waypoints = [np.array(w, dtype=float) for w in waypoints]
        self.speed = speed_m_per_s
        self._position = self.waypoints[0].copy()
        self._segment = 0
        self._done = False

    @property
    def position(self) -> np.ndarray:
        return self._position.copy()

    @property
    def done(self) -> bool:
        return self._done

    def step(self, dt: float) -> np.ndarray:
        """Advance source by dt seconds. Returns new position."""
        if self._done:
            return self._position.copy()

        remaining = self.speed * dt
        while remaining > 0 and self._segment < len(self.waypoints) - 1:
            target = self.waypoints[self._segment + 1]
            to_target = target - self._position
            dist = float(np.linalg.norm(to_target))
            if dist < 1e-9:
                self._segment += 1
                continue
            if remaining >= dist:
                self._position = target.copy()
                self._segment += 1
                remaining -= dist
            else:
                self._position += (to_target / dist) * remaining
                remaining = 0

        if self._segment >= len(self.waypoints) - 1:
            self._done = True

        return self._position.copy()
