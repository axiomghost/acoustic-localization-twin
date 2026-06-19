"""
PyVista 3D renderer for acoustic source localization.

Renders: flat terrain mesh, sensor array, true source position,
estimated source position, 95% confidence ellipse.

Engine dependency: reads EngineState via shared/current_state.json.
Visualization layer never imports from engine/ directly.
"""
from __future__ import annotations
import numpy as np
import pyvista as pv
from dataclasses import dataclass
from pathlib import Path
from scenarios.loader import ScenarioConfig


@dataclass
class RenderConfig:
    window_size: tuple[int, int] = (1200, 800)
    background_color: str = "white"
    z_scale: float = 0.0          # flat terrain: z=0 for all points
    sensor_radius: float = 4.0    # sphere radius in metres
    source_radius: float = 5.0
    ellipse_resolution: int = 60  # points on ellipse curve


def _make_terrain(size_m: float, n_divisions: int = 10) -> pv.PolyData:
    """Flat terrain as a subdivided plane mesh."""
    plane = pv.Plane(
        center=(size_m / 2, size_m / 2, 0),
        direction=(0, 0, 1),
        i_size=size_m,
        j_size=size_m,
        i_resolution=n_divisions,
        j_resolution=n_divisions,
    )
    return plane


def _make_ellipse_curve(
    cx: float, cy: float,
    a: float, b: float,
    angle_deg: float,
    resolution: int = 60,
    z: float = 0.5,
) -> pv.PolyData:
    """Return a closed spline curve tracing the 95% confidence ellipse."""
    theta = np.linspace(0, 2 * np.pi, resolution, endpoint=False)
    # Ellipse in local frame
    x_local = a * np.cos(theta)
    y_local = b * np.sin(theta)
    # Rotate by angle
    rad = np.radians(angle_deg)
    cos_a, sin_a = np.cos(rad), np.sin(rad)
    x_rot = cos_a * x_local - sin_a * y_local + cx
    y_rot = sin_a * x_local + cos_a * y_local + cy
    z_pts = np.full_like(x_rot, z)
    points = np.column_stack([x_rot, y_rot, z_pts])
    # Close the loop
    points = np.vstack([points, points[0]])
    spline = pv.Spline(points, n_points=resolution * 2)
    return spline


def render_single_frame(
    scenario: ScenarioConfig,
    true_xy: np.ndarray,
    est_xy: np.ndarray,
    ellipse: dict,
    screenshot_path: str | None = None,
    interactive: bool = True,
) -> None:
    """
    Render one static frame.

    Args:
        scenario:        loaded ScenarioConfig
        true_xy:         [x, y] true source position (metres)
        est_xy:          [x, y] estimated source position (metres)
        ellipse:         dict with keys a, b, angle_deg (from confidence_ellipse())
        screenshot_path: if set, save PNG here and close (no interactive window)
        interactive:     show interactive window (ignored if screenshot_path set)
    """
    cfg = RenderConfig()
    vis = scenario.visualization
    size = scenario.terrain.size_m

    pl = pv.Plotter(
        window_size=list(cfg.window_size),
        title=f"Acoustic Source Localization — {scenario.name}",
        off_screen=bool(screenshot_path),
    )
    pl.set_background(cfg.background_color)

    # ── Terrain ───────────────────────────────────────────────────────────────
    terrain = _make_terrain(size)
    pl.add_mesh(
        terrain,
        color=vis.terrain_color,
        show_edges=True,
        edge_color="lightgray",
        opacity=0.6,
        label="Terrain",
    )

    # ── Sensors ───────────────────────────────────────────────────────────────
    sensor_positions = np.array(scenario.sensor_positions, dtype=float)
    for i, (sx, sy) in enumerate(sensor_positions):
        sphere = pv.Sphere(radius=cfg.sensor_radius, center=(sx, sy, cfg.sensor_radius))
        pl.add_mesh(sphere, color=vis.sensor_color, label="Sensor" if i == 0 else "")
        pl.add_point_labels(
            np.array([[sx, sy, cfg.sensor_radius * 2.5]]),
            [f"S{i}"],
            font_size=12,
            text_color=vis.sensor_color,
            shape=None,
            always_visible=True,
        )

    # ── True source position ──────────────────────────────────────────────────
    true_sphere = pv.Sphere(
        radius=cfg.source_radius,
        center=(true_xy[0], true_xy[1], cfg.source_radius),
    )
    pl.add_mesh(true_sphere, color=vis.true_path_color, label="True position")
    pl.add_point_labels(
        np.array([[true_xy[0], true_xy[1], cfg.source_radius * 2.5]]),
        ["True"],
        font_size=12,
        text_color=vis.true_path_color,
        shape=None,
        always_visible=True,
    )

    # ── Estimated source position ─────────────────────────────────────────────
    est_sphere = pv.Sphere(
        radius=cfg.source_radius,
        center=(est_xy[0], est_xy[1], cfg.source_radius),
    )
    pl.add_mesh(est_sphere, color=vis.estimate_color, label="Estimate")
    pl.add_point_labels(
        np.array([[est_xy[0], est_xy[1], cfg.source_radius * 2.5]]),
        ["Est"],
        font_size=12,
        text_color=vis.estimate_color,
        shape=None,
        always_visible=True,
    )

    # ── Line connecting true to estimate ─────────────────────────────────────
    line_pts = np.array([
        [true_xy[0], true_xy[1], cfg.source_radius],
        [est_xy[0],  est_xy[1],  cfg.source_radius],
    ])
    line = pv.Line(line_pts[0], line_pts[1])
    pl.add_mesh(line, color="gray", line_width=2)

    # ── 95% Confidence ellipse ────────────────────────────────────────────────
    ellipse_curve = _make_ellipse_curve(
        cx=est_xy[0], cy=est_xy[1],
        a=ellipse["a"], b=ellipse["b"],
        angle_deg=ellipse["angle_deg"],
        resolution=cfg.ellipse_resolution,
        z=1.0,
    )
    pl.add_mesh(
        ellipse_curve,
        color=vis.ellipse_color,
        line_width=3,
        label="95% CI ellipse",
    )

    # ── Annotations ──────────────────────────────────────────────────────────
    error_m = float(np.linalg.norm(est_xy - true_xy))
    pl.add_text(
        f"Scenario: {scenario.name}\n"
        f"Error: {error_m*100:.1f} cm\n"
        f"Ellipse: {ellipse['a']*100:.1f} x {ellipse['b']*100:.1f} cm (95% CI)",
        position="upper_left",
        font_size=11,
        color="black",
    )

    # ── Camera ───────────────────────────────────────────────────────────────
    pl.camera_position = [
        (size * 1.6, -size * 0.4, size * 1.0),   # camera location
        (size / 2,   size / 2,    0),              # focal point (centre of terrain)
        (0, 0, 1),                                 # up vector
    ]

    pl.add_legend(bcolor="white", border=True, size=(0.2, 0.15))

    if screenshot_path:
        Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
        pl.show(screenshot=screenshot_path, auto_close=True)
        print(f"Screenshot saved: {screenshot_path}")
    else:
        pl.show()
