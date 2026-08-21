"""System tray icon exposing sensor toggles, speed, and theme controls."""

from __future__ import annotations

import logging

import pystray

from case_display_visualizer.icon import build_icon_image
from case_display_visualizer.rainbow import RAINBOW_MODES
from case_display_visualizer.scenes.equalizer import STYLES as EQUALIZER_STYLES
from case_display_visualizer.scenes.starfield import ALL_DIRECTIONS
from case_display_visualizer.settings import (
    ALL_SENSORS,
    LINE_THICKNESS_CHOICES,
    SPEED_PRESETS,
    AppSettings,
    save_settings,
)
from case_display_visualizer.themes import THEME_NAMES, get_theme

logger = logging.getLogger(__name__)

SENSOR_LABELS = {
    "cpu": "CPU load",
    "gpu": "GPU load",
    "audio": "Desktop audio",
    "input": "Keyboard / mouse",
}

DIRECTION_LABELS = {
    "left": "Left (default)",
    "right": "Right",
    "up": "Up",
    "down": "Down",
    "away": "Away (tunnel)",
    "towards": "Towards (tunnel)",
}

EQUALIZER_STYLE_LABELS = {
    "bottom": "Bottom bar (default)",
    "radial": "Radial (around rings)",
}

RAINBOW_MODE_LABELS = {
    "prism": "Prism (rainbow, synced)",
    "aurora": "Aurora (rainbow, chase)",
}


def build_tray_icon(settings: AppSettings) -> pystray.Icon:
    def persist() -> None:
        try:
            save_settings(settings)
        except OSError as exc:
            logger.warning("Could not save settings to config.local.toml: %s", exc)

    def sensor_toggle(sensor_name: str):
        def handler(icon, item):
            settings.toggle_sensor(sensor_name)
            persist()

        return handler

    def sensor_checked(sensor_name: str):
        return lambda item: settings.is_enabled(sensor_name)

    def speed_handler(preset_name: str):
        def handler(icon, item):
            settings.set_speed_preset(preset_name)
            persist()

        return handler

    def speed_checked(preset_name: str):
        return lambda item: settings.speed_multiplier == SPEED_PRESETS[preset_name]

    def theme_handler(theme_name: str):
        def handler(icon, item):
            settings.set_theme(theme_name)
            persist()

        return handler

    def theme_checked(theme_name: str):
        return lambda item: settings.color_theme == theme_name

    def line_thickness_handler(thickness: int):
        def handler(icon, item):
            settings.set_line_thickness(thickness)
            persist()

        return handler

    def line_thickness_checked(thickness: int):
        return lambda item: settings.line_thickness == thickness

    def direction_handler(direction: str):
        def handler(icon, item):
            settings.set_starfield_direction(direction)
            persist()

        return handler

    def direction_checked(direction: str):
        return lambda item: settings.starfield_direction == direction

    def equalizer_style_handler(style: str):
        def handler(icon, item):
            settings.set_equalizer_style(style)
            persist()

        return handler

    def equalizer_style_checked(style: str):
        return lambda item: settings.equalizer_style == style

    def moving_center_handler(icon, item):
        settings.toggle_moving_center()
        persist()

    def moving_center_checked(item):
        return settings.moving_center

    def quit_handler(icon, item):
        settings.request_quit()
        icon.stop()

    sensor_items = [
        pystray.MenuItem(
            SENSOR_LABELS[name],
            sensor_toggle(name),
            checked=sensor_checked(name),
        )
        for name in ALL_SENSORS
    ]

    speed_items = [
        pystray.MenuItem(
            preset_name.capitalize(),
            speed_handler(preset_name),
            checked=speed_checked(preset_name),
            radio=True,
        )
        for preset_name in SPEED_PRESETS
    ]

    theme_items = (
        [
            pystray.MenuItem(
                "Auto (cycles)",
                theme_handler("auto"),
                checked=theme_checked("auto"),
                radio=True,
            )
        ]
        + [
            pystray.MenuItem(
                theme_name.capitalize(),
                theme_handler(theme_name),
                checked=theme_checked(theme_name),
                radio=True,
            )
            for theme_name in THEME_NAMES
        ]
        + [
            pystray.MenuItem(
                RAINBOW_MODE_LABELS[mode],
                theme_handler(mode),
                checked=theme_checked(mode),
                radio=True,
            )
            for mode in RAINBOW_MODES
        ]
    )

    line_thickness_items = [
        pystray.MenuItem(
            f"{thickness} px" + (" (default)" if thickness == 1 else ""),
            line_thickness_handler(thickness),
            checked=line_thickness_checked(thickness),
            radio=True,
        )
        for thickness in LINE_THICKNESS_CHOICES
    ]

    direction_items = [
        pystray.MenuItem(
            DIRECTION_LABELS[direction],
            direction_handler(direction),
            checked=direction_checked(direction),
            radio=True,
        )
        for direction in ALL_DIRECTIONS
    ]

    equalizer_style_items = [
        pystray.MenuItem(
            EQUALIZER_STYLE_LABELS[style],
            equalizer_style_handler(style),
            checked=equalizer_style_checked(style),
            radio=True,
        )
        for style in EQUALIZER_STYLES
    ]

    menu = pystray.Menu(
        pystray.MenuItem("Sensors", pystray.Menu(*sensor_items)),
        pystray.MenuItem("Speed", pystray.Menu(*speed_items)),
        pystray.MenuItem("Theme", pystray.Menu(*theme_items)),
        pystray.MenuItem("Line thickness", pystray.Menu(*line_thickness_items)),
        pystray.MenuItem("Starfield direction", pystray.Menu(*direction_items)),
        pystray.MenuItem("Equalizer style", pystray.Menu(*equalizer_style_items)),
        pystray.MenuItem(
            "Moving center", moving_center_handler, checked=moving_center_checked
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_handler),
    )

    icon_color = get_theme(settings.color_theme).ring
    return pystray.Icon(
        "case_display_visualizer",
        build_icon_image(icon_color, size=64),
        "Case Display Visualizer",
        menu,
    )
