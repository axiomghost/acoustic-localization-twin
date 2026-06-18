"""Shared engine state dataclass — written by engine, read by viz and dashboard."""
from __future__ import annotations
from dataclasses import dataclass, field
import json, os, time
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent / "shared" / "current_state.json"
_TMP_FILE  = STATE_FILE.with_suffix(".tmp")


@dataclass
class SensorStatus:
    id: int
    position: list[float]       # [x, y, z] metres
    toa: float                  # time of arrival (seconds), NaN if no detection
    snr_db: float               # estimated SNR


@dataclass
class EngineState:
    tick: int
    sim_time: float             # seconds
    true_position: list[float]  # [x, y] metres
    est_position: list[float]   # [x, y] metres
    error_m: float              # Euclidean error metres
    confidence_ellipse: dict    # {cx, cy, a, b, angle_deg}
    sensors: list[SensorStatus]
    scenario_name: str = ""
    timestamp: float = field(default_factory=time.time)

    def write(self) -> None:
        """Atomically write state to JSON file for dashboard/viz consumption."""
        data = {
            "tick": self.tick,
            "sim_time": self.sim_time,
            "true_position": self.true_position,
            "est_position": self.est_position,
            "error_m": self.error_m,
            "confidence_ellipse": self.confidence_ellipse,
            "sensors": [
                {"id": s.id, "position": s.position, "toa": s.toa, "snr_db": s.snr_db}
                for s in self.sensors
            ],
            "scenario_name": self.scenario_name,
            "timestamp": self.timestamp,
        }
        _TMP_FILE.write_text(json.dumps(data, indent=2))
        os.replace(_TMP_FILE, STATE_FILE)

    @staticmethod
    def read() -> dict | None:
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return None
