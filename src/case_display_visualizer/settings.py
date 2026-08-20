"""Runtime-mutable settings shared between the tray icon thread and the
render loop. Individual attribute reads/writes are atomic under the GIL, so
no explicit locking is used for the simple cases below.
"""

from __future__ import annotations

from dataclasses import dataclass, field

ALL_SENSORS = ("cpu", "gpu", "audio", "input")
SPEED_PRESETS = {"slow": 0.5, "normal": 1.0, "fast": 2.0}
MIN_LINE_THICKNESS = 1
MAX_LINE_THICKNESS = 6
LINE_THICKNESS_CHOICES = tuple(range(MIN_LINE_THICKNESS, MAX_LINE_THICKNESS + 1))


@dataclass
class AppSettings:
    enabled_sensors: set[str] = field(default_factory=lambda: set(ALL_SENSORS))
    speed_multiplier: float = 1.0
    color_theme: str = "auto"
    line_thickness: int = 1
    quit_requested: bool = False

    def is_enabled(self, sensor_name: str) -> bool:
        return sensor_name in self.enabled_sensors

    def toggle_sensor(self, sensor_name: str) -> None:
        if sensor_name in self.enabled_sensors:
            self.enabled_sensors.discard(sensor_name)
        else:
            self.enabled_sensors.add(sensor_name)

    def set_speed_preset(self, preset_name: str) -> None:
        self.speed_multiplier = SPEED_PRESETS.get(preset_name, 1.0)

    def set_theme(self, theme_name: str) -> None:
        self.color_theme = theme_name

    def set_line_thickness(self, thickness: int) -> None:
        self.line_thickness = max(MIN_LINE_THICKNESS, min(MAX_LINE_THICKNESS, thickness))

    def request_quit(self) -> None:
        self.quit_requested = True


def load_settings(config_path: str | None = None) -> AppSettings:
    """Build settings, applying overrides from a TOML config file if present."""
    import tomllib
    from pathlib import Path

    settings = AppSettings()

    candidates = []
    if config_path:
        candidates.append(Path(config_path))
    else:
        base = Path(__file__).resolve().parent.parent.parent
        candidates.append(base / "config.local.toml")
        candidates.append(base / "config.toml")

    for path in candidates:
        if path.is_file():
            with path.open("rb") as f:
                data = tomllib.load(f)
            _apply_config(settings, data)
            break

    return settings


def _apply_config(settings: AppSettings, data: dict) -> None:
    sensors = data.get("sensors", {})
    enabled = {name for name in ALL_SENSORS if sensors.get(name, True)}
    settings.enabled_sensors = enabled

    display = data.get("display", {})
    speed_preset = display.get("speed", "normal")
    settings.set_speed_preset(speed_preset)

    theme = display.get("theme", "auto")
    settings.set_theme(theme)

    line_thickness = display.get("line_thickness", MIN_LINE_THICKNESS)
    settings.set_line_thickness(line_thickness)
