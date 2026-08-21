"""Runtime-mutable settings shared between the tray icon thread and the
render loop. Individual attribute reads/writes are atomic under the GIL, so
no explicit locking is used for the simple cases below.

Changes made at runtime (e.g. via the tray menu) are persisted to
config.local.toml so they survive restarts -- config.toml itself is never
written to, since it's the checked-in set of shipped defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from case_display_visualizer.paths import app_base_dir, bundled_resource_dir
from case_display_visualizer.scenes.equalizer import DEFAULT_STYLE, STYLES
from case_display_visualizer.scenes.starfield import ALL_DIRECTIONS, DEFAULT_DIRECTION

ALL_SENSORS = ("cpu", "gpu", "audio", "input")
SPEED_PRESETS = {"slow": 0.5, "normal": 1.0, "fast": 2.0}
MIN_LINE_THICKNESS = 1
MAX_LINE_THICKNESS = 6
LINE_THICKNESS_CHOICES = tuple(range(MIN_LINE_THICKNESS, MAX_LINE_THICKNESS + 1))

# "3d" exists as a placeholder for future work -- it's not selectable yet
# (the tray shows it greyed out), so DEFAULT_DEPTH is the only real value.
DEPTH_OPTIONS = ("2d", "3d")
AVAILABLE_DEPTH_OPTIONS = ("2d",)
DEFAULT_DEPTH = "2d"


@dataclass
class AppSettings:
    enabled_sensors: set[str] = field(default_factory=lambda: set(ALL_SENSORS))
    speed_multiplier: float = 1.0
    color_theme: str = "auto"
    line_thickness: int = 1
    starfield_direction: str = DEFAULT_DIRECTION
    equalizer_style: str = DEFAULT_STYLE
    moving_center: bool = True
    depth: str = DEFAULT_DEPTH
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

    def speed_preset_name(self) -> str:
        for name, value in SPEED_PRESETS.items():
            if value == self.speed_multiplier:
                return name
        return "normal"

    def set_theme(self, theme_name: str) -> None:
        self.color_theme = theme_name

    def set_line_thickness(self, thickness: int) -> None:
        self.line_thickness = max(MIN_LINE_THICKNESS, min(MAX_LINE_THICKNESS, thickness))

    def set_starfield_direction(self, direction: str) -> None:
        if direction in ALL_DIRECTIONS:
            self.starfield_direction = direction

    def set_equalizer_style(self, style: str) -> None:
        if style in STYLES:
            self.equalizer_style = style

    def toggle_moving_center(self) -> None:
        self.moving_center = not self.moving_center

    def set_depth(self, depth: str) -> None:
        if depth in AVAILABLE_DEPTH_OPTIONS:
            self.depth = depth

    def request_quit(self) -> None:
        self.quit_requested = True


def _config_search_paths(config_path: str | None) -> list[Path]:
    if config_path:
        return [Path(config_path)]
    return [
        app_base_dir() / "config.local.toml",
        bundled_resource_dir() / "config.toml",
    ]


def local_config_path() -> Path:
    """Path settings changes are persisted to: next to the .exe when
    frozen, the project root's (gitignored) config.local.toml otherwise."""
    return app_base_dir() / "config.local.toml"


def load_settings(config_path: str | None = None) -> AppSettings:
    """Build settings, applying overrides from a TOML config file if present."""
    import tomllib

    settings = AppSettings()

    for path in _config_search_paths(config_path):
        if path.is_file():
            with path.open("rb") as f:
                data = tomllib.load(f)
            _apply_config(settings, data)
            break

    return settings


def save_settings(settings: AppSettings, path: Path | None = None) -> None:
    """Persist current settings to config.local.toml (or the given path)."""
    target = path if path is not None else local_config_path()

    lines = [
        "# Machine-local overrides, written automatically when settings are",
        "# changed via the tray icon. Safe to hand-edit; see config.toml for",
        "# all available options and their meaning.",
        "",
        "[sensors]",
    ]
    for name in ALL_SENSORS:
        lines.append(f"{name} = {str(settings.is_enabled(name)).lower()}")

    lines += [
        "",
        "[display]",
        f'speed = "{settings.speed_preset_name()}"',
        f'theme = "{settings.color_theme}"',
        f"line_thickness = {settings.line_thickness}",
        f'starfield_direction = "{settings.starfield_direction}"',
        f'equalizer_style = "{settings.equalizer_style}"',
        f"moving_center = {str(settings.moving_center).lower()}",
        f'depth = "{settings.depth}"',
        "",
    ]

    target.write_text("\n".join(lines), encoding="utf-8")


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

    starfield_direction = display.get("starfield_direction", DEFAULT_DIRECTION)
    settings.set_starfield_direction(starfield_direction)

    equalizer_style = display.get("equalizer_style", DEFAULT_STYLE)
    settings.set_equalizer_style(equalizer_style)

    settings.moving_center = bool(display.get("moving_center", True))

    depth = display.get("depth", DEFAULT_DEPTH)
    settings.set_depth(depth)
