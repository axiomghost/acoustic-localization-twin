"""
Rich terminal panel — live localization stats.

Reads EngineState from shared/current_state.json each tick and renders
a live-updating terminal layout: scenario header, localization metrics,
per-sensor SNR table, and a running error history sparkline.
"""
from __future__ import annotations
import time
import math
from collections import deque
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich import box
from shared.state import EngineState, STATE_FILE
import json

HISTORY = 40  # ticks of error history for sparkline
SPARK_CHARS = " ▁▂▃▄▅▆▇█"


def _sparkline(values: list[float], width: int = HISTORY) -> str:
    if not values:
        return " " * width
    vmin, vmax = min(values), max(values)
    span = vmax - vmin or 1e-9
    chars = []
    for v in values[-width:]:
        idx = int((v - vmin) / span * (len(SPARK_CHARS) - 1))
        chars.append(SPARK_CHARS[idx])
    return "".join(chars).ljust(width)


def _make_layout(
    state: dict,
    scenario_name: str,
    error_history: list[float],
) -> Layout:
    e = state["confidence_ellipse"]

    # ── Header ───────────────────────────────────────────────────────────────
    header_text = Text()
    header_text.append("Acoustic Source Localization  ", style="bold white")
    header_text.append(f"| {scenario_name}", style="dim")
    header = Panel(header_text, style="bold blue", padding=(0, 1))

    # ── Metrics ──────────────────────────────────────────────────────────────
    metrics = Table.grid(padding=(0, 2))
    metrics.add_column(style="dim", width=18)
    metrics.add_column(style="bold cyan", width=16)
    metrics.add_column(style="dim", width=18)
    metrics.add_column(style="bold cyan", width=16)

    tp = state["true_position"]
    ep = state["est_position"]
    metrics.add_row(
        "Tick",          str(state["tick"]),
        "Sim time",      f"{state['sim_time']:.1f} s",
    )
    metrics.add_row(
        "True position", f"({tp[0]:.1f}, {tp[1]:.1f}) m",
        "Est position",  f"({ep[0]:.1f}, {ep[1]:.1f}) m",
    )
    metrics.add_row(
        "Error",         f"{state['error_m'] * 100:.2f} cm",
        "Ellipse (a,b)", f"{e['a']*100:.1f} x {e['b']*100:.1f} cm",
    )
    metrics.add_row(
        "Ellipse angle", f"{e['angle_deg']:.1f} deg",
        "Est centre",    f"({e['cx']:.1f}, {e['cy']:.1f}) m",
    )

    metrics_panel = Panel(metrics, title="[bold]Localization Metrics", box=box.ROUNDED)

    # ── Sparkline ────────────────────────────────────────────────────────────
    spark = _sparkline(error_history)
    max_e = max(error_history) * 100 if error_history else 0
    mean_e = (sum(error_history) / len(error_history)) * 100 if error_history else 0
    spark_text = Text()
    spark_text.append(f" Error history (last {HISTORY} ticks)  ", style="dim")
    spark_text.append(spark, style="green")
    spark_text.append(f"  mean {mean_e:.2f} cm  max {max_e:.2f} cm", style="dim")
    spark_panel = Panel(spark_text, box=box.SIMPLE)

    # ── Sensor table ─────────────────────────────────────────────────────────
    sensor_table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    sensor_table.add_column("Sensor", style="dim", width=8)
    sensor_table.add_column("Position (m)", width=18)
    sensor_table.add_column("TOA (ms)", width=12)
    sensor_table.add_column("SNR (dB)", width=10)
    sensor_table.add_column("Bar", width=20)

    for s in state["sensors"]:
        snr = s["snr_db"]
        bar_len = int(min(snr, 40) / 40 * 18)
        bar = "[green]" + "█" * bar_len + "[/green]" + "░" * (18 - bar_len)
        snr_style = "green" if snr > 20 else "yellow" if snr > 10 else "red"
        pos = s["position"]
        sensor_table.add_row(
            f"S{s['id']}",
            f"({pos[0]:.0f}, {pos[1]:.0f})",
            f"{s['toa'] * 1000:.3f}",
            Text(f"{snr:.1f}", style=snr_style),
            bar,
        )

    sensor_panel = Panel(sensor_table, title="[bold]Sensor Status", box=box.ROUNDED)

    layout = Layout()
    layout.split_column(
        Layout(header,        name="header",  size=3),
        Layout(metrics_panel, name="metrics", size=9),
        Layout(spark_panel,   name="spark",   size=3),
        Layout(sensor_panel,  name="sensors", size=10),
    )
    return layout


def run_panel(scenario_name: str, poll_interval_s: float = 0.25) -> None:
    """
    Poll shared/current_state.json and render live until the engine finishes
    or the user hits Ctrl-C.
    """
    console = Console()
    error_history: deque[float] = deque(maxlen=HISTORY)
    last_tick = -1

    with Live(console=console, refresh_per_second=4, screen=True) as live:
        while True:
            try:
                state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else None
            except Exception:
                state = None
            if state is not None and state["tick"] != last_tick:
                last_tick = state["tick"]
                error_history.append(state["error_m"])
                live.update(_make_layout(state, scenario_name, list(error_history)))
            time.sleep(poll_interval_s)
