"""
Engine orchestrator — runs the simulation tick loop.

Reads a ScenarioConfig, advances the source each tick, runs TDOA
localization, computes confidence ellipse, and writes EngineState
to shared/current_state.json for visualization and dashboard.
"""
from __future__ import annotations
import time
import numpy as np
from scenarios.loader import ScenarioConfig
from engine.source import AcousticSource
from engine.propagation import SimplePropagation
from engine.tdoa import compute_tdoa_measurements
from engine.localizer import GaussNewtonTDOA
from engine.confidence import confidence_ellipse
from shared.state import EngineState, SensorStatus


class Engine:
    def __init__(self, scenario: ScenarioConfig, seed: int = 0):
        self.scenario = scenario
        self.sensors = np.array(scenario.sensor_positions, dtype=float)
        self.noise_std_s = scenario.timing_noise_std_s
        self.sigma_r = scenario.propagation.speed_of_sound_m_per_s * self.noise_std_s
        self.dt = scenario.sim.tick_interval_s

        self.source = AcousticSource(
            waypoints=[[w.x, w.y] for w in scenario.source.path],
            speed_m_per_s=scenario.source.speed_m_per_s,
        )
        self.propagation = SimplePropagation(scenario.propagation.speed_of_sound_m_per_s)
        self.localizer = GaussNewtonTDOA(scenario.propagation.speed_of_sound_m_per_s)
        self.rng = np.random.default_rng(seed)
        self.tick = 0
        self.sim_time = 0.0

    def step(self) -> EngineState:
        """Advance one tick. Returns the new EngineState."""
        true_xy = self.source.step(self.dt)

        tdoa = compute_tdoa_measurements(
            true_xy, self.sensors,
            propagation=self.propagation,
            noise_std_s=self.noise_std_s,
            rng=self.rng,
        )
        est_xy, raw_cov = self.localizer.estimate(tdoa, self.sensors)
        ellipse = confidence_ellipse(raw_cov, self.sigma_r)
        error_m = float(np.linalg.norm(est_xy - true_xy))

        # Per-sensor TOA for dashboard health display
        sensor_statuses = []
        for i, spos in enumerate(self.sensors):
            toa = self.propagation.compute_toa(true_xy, spos)
            dist = float(np.linalg.norm(true_xy - spos))
            snr_db = max(0.0, 40.0 - 20.0 * np.log10(max(dist, 1.0)))
            sensor_statuses.append(SensorStatus(
                id=i,
                position=spos.tolist(),
                toa=toa,
                snr_db=snr_db,
            ))

        state = EngineState(
            tick=self.tick,
            sim_time=self.sim_time,
            true_position=true_xy.tolist(),
            est_position=est_xy.tolist(),
            error_m=error_m,
            confidence_ellipse={
                "cx": float(est_xy[0]),
                "cy": float(est_xy[1]),
                "a": ellipse["a"],
                "b": ellipse["b"],
                "angle_deg": ellipse["angle_deg"],
            },
            sensors=sensor_statuses,
            scenario_name=self.scenario.name,
        )

        self.tick += 1
        self.sim_time += self.dt
        return state

    def run(self, on_tick=None, realtime: bool = True) -> None:
        """
        Run until source reaches end of path.
        on_tick: optional callback(EngineState) called each tick.
        realtime: if True, sleep between ticks to match sim time.
        """
        while not self.source.done:
            t0 = time.perf_counter()
            state = self.step()
            state.write()
            if on_tick:
                on_tick(state)
            if realtime:
                elapsed = time.perf_counter() - t0
                sleep_s = self.dt - elapsed
                if sleep_s > 0:
                    time.sleep(sleep_s)
