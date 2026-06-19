"""
Live PyVista renderer — updates scene each engine tick.

Engine runs in a background thread pushing state.
Main thread runs a tight render loop using interactive_update=True.
"""
from __future__ import annotations
import threading
import time
import numpy as np
import pyvista as pv
from scenarios.loader import ScenarioConfig
from visualization.renderer import _make_terrain, _make_ellipse_curve, RenderConfig


class LiveRenderer:
    def __init__(self, scenario: ScenarioConfig):
        self.scenario = scenario
        self.cfg = RenderConfig()
        self.vis = scenario.visualization
        self.size = scenario.terrain.size_m
        self._lock = threading.Lock()
        self._latest_state = None
        self._last_tick = -1
        self._running = True

    def push_state(self, state) -> None:
        with self._lock:
            self._latest_state = state

    def _get_state(self):
        with self._lock:
            return self._latest_state

    def run(self, engine) -> None:
        # Engine in background thread
        def engine_thread():
            engine.run(on_tick=self.push_state, realtime=True)
            self._running = False

        t = threading.Thread(target=engine_thread, daemon=True)
        t.start()

        pl = pv.Plotter(
            window_size=list(self.cfg.window_size),
            title=f"Acoustic Source Localization — {self.scenario.name}",
        )
        pl.set_background(self.cfg.background_color)

        # ── Static elements ───────────────────────────────────────────────────
        pl.add_mesh(
            _make_terrain(self.size),
            color=self.vis.terrain_color,
            show_edges=True, edge_color="lightgray", opacity=0.6,
        )

        sensor_positions = np.array(self.scenario.sensor_positions, dtype=float)
        for i, (sx, sy) in enumerate(sensor_positions):
            pl.add_mesh(
                pv.Sphere(radius=self.cfg.sensor_radius,
                          center=(sx, sy, self.cfg.sensor_radius)),
                color=self.vis.sensor_color,
            )
            pl.add_point_labels(
                np.array([[sx, sy, self.cfg.sensor_radius * 2.8]]),
                [f"S{i}"], font_size=12,
                text_color=self.vis.sensor_color,
                shape=None, always_visible=True,
            )

        # Faint planned path line
        path_pts = np.array([[w.x, w.y, 0.5] for w in self.scenario.source.path])
        pl.add_mesh(pv.Spline(path_pts, n_points=100),
                    color=self.vis.true_path_color, line_width=1, opacity=0.25)

        pl.camera_position = [
            (self.size * 1.6, -self.size * 0.4, self.size * 1.0),
            (self.size / 2,    self.size / 2,    0),
            (0, 0, 1),
        ]

        pl.add_legend(
            labels=[
                ("Sensor",        self.vis.sensor_color),
                ("True position", self.vis.true_path_color),
                ("Estimate",      self.vis.estimate_color),
                ("95% CI",        self.vis.ellipse_color),
            ],
            bcolor="white", border=True, size=(0.22, 0.16),
        )

        r = self.cfg.source_radius

        # ── Open window in interactive_update mode ────────────────────────────
        pl.show(interactive_update=True, auto_close=False)

        # ── Render loop — runs until window is closed ─────────────────────────
        while pl.render_window is not None and pl.render_window.initialized:
            state = self._get_state()

            if state is not None and state.tick != self._last_tick:
                self._last_tick = state.tick
                tx, ty = state.true_position
                ex, ey = state.est_position
                e = state.confidence_ellipse

                # Remove previous dynamic actors by name
                for name in ("_true", "_est", "_ellipse", "_line", "_info"):
                    pl.remove_actor(name, render=False)

                pl.add_mesh(
                    pv.Sphere(radius=r, center=(tx, ty, r)),
                    color=self.vis.true_path_color, name="_true",
                )
                pl.add_mesh(
                    pv.Sphere(radius=r, center=(ex, ey, r)),
                    color=self.vis.estimate_color, name="_est",
                )
                pl.add_mesh(
                    _make_ellipse_curve(ex, ey, e["a"], e["b"],
                                        e["angle_deg"], z=1.0),
                    color=self.vis.ellipse_color,
                    line_width=3, name="_ellipse",
                )
                pl.add_mesh(
                    pv.Line((tx, ty, r), (ex, ey, r)),
                    color="gray", line_width=2, name="_line",
                )
                pl.add_text(
                    f"Tick {state.tick}  |  t={state.sim_time:.1f}s  |  "
                    f"Error: {state.error_m*100:.1f} cm\n"
                    f"Ellipse: {e['a']*100:.1f} x {e['b']*100:.1f} cm (95% CI)",
                    position="upper_left", font_size=11,
                    color="black", name="_info",
                )

            pl.update(1)          # process window events, render
            time.sleep(0.02)      # ~50 fps max, keeps CPU sane

        pl.close()
