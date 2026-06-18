"""
Scenario YAML loader — parses and validates scenario config files into typed models.

A scenario config defines everything that varies between deployments:
  - terrain geometry
  - sensor positions
  - source path and signature
  - propagation / noise parameters
  - visualization styling

The engine accepts a ScenarioConfig and is otherwise scenario-agnostic.
"""
from __future__ import annotations
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator


class TerrainConfig(BaseModel):
    type: Literal["flat", "heightmap"] = "flat"
    size_m: float = Field(gt=0, description="Side length of square terrain in metres")
    heightmap_path: str | None = None   # required when type == "heightmap"

    @model_validator(mode="after")
    def heightmap_required_if_type(self) -> "TerrainConfig":
        if self.type == "heightmap" and not self.heightmap_path:
            raise ValueError("heightmap_path required when terrain type is 'heightmap'")
        return self


class SensorConfig(BaseModel):
    id: int
    x: float
    y: float
    label: str = ""


class WaypointConfig(BaseModel):
    x: float
    y: float


class SourceConfig(BaseModel):
    path: list[WaypointConfig] = Field(min_length=2)
    speed_m_per_s: float = Field(gt=0, description="Source travel speed in m/s")
    signature: str = "impulsive"        # e.g. "impulsive", "continuous"


class PropagationConfig(BaseModel):
    speed_of_sound_m_per_s: float = Field(default=343.0, gt=0)
    timing_noise_std_ms: float = Field(default=0.1, ge=0,
        description="Sensor timing noise standard deviation in milliseconds")


class SimConfig(BaseModel):
    tick_interval_s: float = Field(default=0.1, gt=0,
        description="Simulated time step in seconds")
    total_duration_s: float = Field(default=60.0, gt=0)


class VisualizationConfig(BaseModel):
    sensor_color: str = "blue"
    true_path_color: str = "green"
    estimate_color: str = "red"
    ellipse_color: str = "orange"
    terrain_color: str = "lightgray"


class ScenarioConfig(BaseModel):
    name: str
    description: str = ""
    use_case: str = ""          # e.g. "wildlife_monitoring", "urban_noise_mapping"
    terrain: TerrainConfig
    sensors: list[SensorConfig] = Field(min_length=3,
        description="At least 3 sensors required for 2D TDOA localization")
    source: SourceConfig
    propagation: PropagationConfig = PropagationConfig()
    sim: SimConfig = SimConfig()
    visualization: VisualizationConfig = VisualizationConfig()

    @model_validator(mode="after")
    def sensor_ids_unique(self) -> "ScenarioConfig":
        ids = [s.id for s in self.sensors]
        if len(ids) != len(set(ids)):
            raise ValueError("Sensor IDs must be unique")
        return self

    @property
    def sensor_positions(self):
        """Return sensor positions as list of [x, y] in sensor-id order."""
        sorted_sensors = sorted(self.sensors, key=lambda s: s.id)
        return [[s.x, s.y] for s in sorted_sensors]

    @property
    def timing_noise_std_s(self) -> float:
        return self.propagation.timing_noise_std_ms / 1000.0


def load_scenario(path: str | Path) -> ScenarioConfig:
    """Load and validate a scenario YAML file. Raises on invalid config."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Scenario config not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ScenarioConfig.model_validate(raw)
