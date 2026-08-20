"""Startup config dump (-v) and live in-place sensor telemetry (-vv)."""

from __future__ import annotations

import sys

from case_display_visualizer.composer import EnergyState
from case_display_visualizer.display import TargetDisplay
from case_display_visualizer.settings import AppSettings

TELEMETRY_SENSOR_NAMES = ("cpu", "gpu", "audio", "input")


def dump_config(target: TargetDisplay, settings: AppSettings, windowed: bool) -> None:
    lines = [
        "=== Case Display Visualizer config ===",
        f"Target display : {target.name} {target.width}x{target.height} @ ({target.x},{target.y})",
        f"Window mode    : {'windowed' if windowed else 'full-screen on case display'}",
        f"Sensors enabled: {', '.join(sorted(settings.enabled_sensors)) or 'none'}",
        f"Speed multiplier: {settings.speed_multiplier}",
        f"Color theme    : {settings.color_theme}",
        f"Line thickness : {settings.line_thickness}px",
        "=======================================",
    ]
    print("\n".join(lines), flush=True)


class LiveTelemetry:
    """Throttled, single-line, in-place terminal readout of sensor energy."""

    def __init__(self, interval: float = 0.1) -> None:
        self.interval = interval
        self._elapsed = 0.0
        self._printed = False

    def update(
        self,
        dt: float,
        energy: EnergyState,
        settings: AppSettings,
        theme_name: str,
        fps: float,
    ) -> None:
        self._elapsed += dt
        if self._elapsed < self.interval:
            return
        self._elapsed = 0.0

        parts = [f"{name}={energy.get(name):.2f}" for name in TELEMETRY_SENSOR_NAMES]
        line = (
            " ".join(parts)
            + f" | theme={theme_name} speed={settings.speed_multiplier:.1f}x fps={fps:.0f}"
        )
        sys.stdout.write("\r" + line.ljust(90))
        sys.stdout.flush()
        self._printed = True

    def close(self) -> None:
        if self._printed:
            sys.stdout.write("\n")
            sys.stdout.flush()
