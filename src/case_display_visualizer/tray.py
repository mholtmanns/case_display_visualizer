"""System tray icon exposing sensor toggles, speed, and theme controls."""

from __future__ import annotations

import math

import pystray
from PIL import Image, ImageDraw

from case_display_visualizer.scenes.starfield import ALL_DIRECTIONS
from case_display_visualizer.settings import (
    ALL_SENSORS,
    LINE_THICKNESS_CHOICES,
    SPEED_PRESETS,
    AppSettings,
)
from case_display_visualizer.themes import THEME_NAMES, get_theme

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


def _make_icon_image(color: tuple[int, int, int] = (0, 220, 220)) -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy, r = size / 2, size / 2, size / 2 - 4
    points = [
        (
            cx + r * math.cos(math.radians(60 * i - 90)),
            cy + r * math.sin(math.radians(60 * i - 90)),
        )
        for i in range(6)
    ]
    draw.polygon(points, outline=color, width=3)
    return img


def build_tray_icon(settings: AppSettings) -> pystray.Icon:
    def sensor_toggle(sensor_name: str):
        def handler(icon, item):
            settings.toggle_sensor(sensor_name)

        return handler

    def sensor_checked(sensor_name: str):
        return lambda item: settings.is_enabled(sensor_name)

    def speed_handler(preset_name: str):
        def handler(icon, item):
            settings.set_speed_preset(preset_name)

        return handler

    def speed_checked(preset_name: str):
        return lambda item: settings.speed_multiplier == SPEED_PRESETS[preset_name]

    def theme_handler(theme_name: str):
        def handler(icon, item):
            settings.set_theme(theme_name)

        return handler

    def theme_checked(theme_name: str):
        return lambda item: settings.color_theme == theme_name

    def line_thickness_handler(thickness: int):
        def handler(icon, item):
            settings.set_line_thickness(thickness)

        return handler

    def line_thickness_checked(thickness: int):
        return lambda item: settings.line_thickness == thickness

    def direction_handler(direction: str):
        def handler(icon, item):
            settings.set_starfield_direction(direction)

        return handler

    def direction_checked(direction: str):
        return lambda item: settings.starfield_direction == direction

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

    theme_items = [
        pystray.MenuItem(
            "Auto (cycles)",
            theme_handler("auto"),
            checked=theme_checked("auto"),
            radio=True,
        )
    ] + [
        pystray.MenuItem(
            theme_name.capitalize(),
            theme_handler(theme_name),
            checked=theme_checked(theme_name),
            radio=True,
        )
        for theme_name in THEME_NAMES
    ]

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

    menu = pystray.Menu(
        pystray.MenuItem("Sensors", pystray.Menu(*sensor_items)),
        pystray.MenuItem("Speed", pystray.Menu(*speed_items)),
        pystray.MenuItem("Theme", pystray.Menu(*theme_items)),
        pystray.MenuItem("Line thickness", pystray.Menu(*line_thickness_items)),
        pystray.MenuItem("Starfield direction", pystray.Menu(*direction_items)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_handler),
    )

    icon_color = get_theme(settings.color_theme).ring
    return pystray.Icon(
        "case_display_visualizer",
        _make_icon_image(icon_color),
        "Case Display Visualizer",
        menu,
    )
