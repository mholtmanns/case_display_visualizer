"""Hue-cycling color generation for the rainbow theme modes.

Two modes, named like the rest of the theme palette (cyan, amber, ...):
  prism  - every element shares the same hue, shifting together over time
           (like a single RGB zone breathing through colors)
  aurora - each element (ring, equalizer band) gets a hue offset by its
           position, so color visibly sweeps/chases across them as the
           base hue advances (like an RGB fan chase effect)
"""

from __future__ import annotations

import colorsys

RAINBOW_MODES = ("prism", "aurora")
DEFAULT_CYCLE_SECONDS = 12.0  # time for one full hue rotation at 1x speed
SATURATION = 0.95
VALUE = 0.95


def is_rainbow_mode(theme_name: str) -> bool:
    return theme_name in RAINBOW_MODES


def hue_to_rgb(hue: float, saturation: float = SATURATION, value: float = VALUE) -> tuple[int, int, int]:
    r, g, b = colorsys.hsv_to_rgb(hue % 1.0, saturation, value)
    return (int(r * 255), int(g * 255), int(b * 255))


def rainbow_color(
    elapsed: float,
    mode: str,
    index: int = 0,
    count: int = 1,
    cycle_seconds: float = DEFAULT_CYCLE_SECONDS,
) -> tuple[int, int, int]:
    """Color for one "slot" (e.g. ring or equalizer band) at a point in time.

    `elapsed` should already include any speed scaling the caller wants
    (e.g. dt * settings.speed_multiplier), so the cycle rate follows the
    app's existing Speed setting for free.
    """
    base_hue = elapsed / cycle_seconds
    offset = (index / count) if (mode == "aurora" and count > 0) else 0.0
    return hue_to_rgb(base_hue + offset)
