"""Named color palettes shared across scenes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    ring: tuple[int, int, int]
    eq_low: tuple[int, int, int]
    eq_high: tuple[int, int, int]
    particle: tuple[int, int, int]


THEMES: dict[str, Theme] = {
    "cyan": Theme(
        ring=(0, 220, 220),
        eq_low=(0, 200, 220),
        eq_high=(200, 60, 220),
        particle=(255, 200, 60),
    ),
    "amber": Theme(
        ring=(255, 150, 0),
        eq_low=(255, 200, 0),
        eq_high=(255, 60, 30),
        particle=(255, 255, 180),
    ),
    "magenta": Theme(
        ring=(230, 0, 200),
        eq_low=(120, 0, 220),
        eq_high=(255, 0, 140),
        particle=(255, 220, 255),
    ),
    "matrix": Theme(
        ring=(0, 255, 100),
        eq_low=(0, 120, 40),
        eq_high=(120, 255, 120),
        particle=(200, 255, 200),
    ),
}

DEFAULT_THEME = "cyan"
THEME_NAMES = list(THEMES.keys())


def get_theme(name: str) -> Theme:
    return THEMES.get(name, THEMES[DEFAULT_THEME])
