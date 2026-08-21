"""Named color palettes shared across scenes.

Built-in themes are defined in BUILTIN_THEMES below. Users can add new
themes or override the built-in ones by creating themes.local.toml in the
project root (see themes.example.toml for the documented format) -- it's
merged in once at import time, so a restart is needed to pick up edits.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from case_display_visualizer.rainbow import RAINBOW_MODES

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class Theme:
    ring: tuple[int, int, int]
    eq_low: tuple[int, int, int]
    eq_high: tuple[int, int, int]
    particle: tuple[int, int, int]


BUILTIN_THEMES: dict[str, Theme] = {
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


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    hex_digits = value.strip().lstrip("#")
    if len(hex_digits) != 6:
        raise ValueError(f"expected a 6-digit hex color like \"#00DCDC\", got {value!r}")
    return (
        int(hex_digits[0:2], 16),
        int(hex_digits[2:4], 16),
        int(hex_digits[4:6], 16),
    )


def _parse_color(value: Any) -> tuple[int, int, int]:
    """Accept either a hex string ("#RRGGBB") or a [r, g, b] array (0-255)."""
    if isinstance(value, str):
        return _hex_to_rgb(value)
    r, g, b = value
    return (int(r), int(g), int(b))


def _load_local_themes(path: Path | None = None) -> dict[str, Theme]:
    target = path if path is not None else _PROJECT_ROOT / "themes.local.toml"
    if not target.is_file():
        return {}

    import tomllib

    with target.open("rb") as f:
        data = tomllib.load(f)

    themes: dict[str, Theme] = {}
    for name, colors in data.get("themes", {}).items():
        if name in RAINBOW_MODES:
            logger.warning(
                "Skipping theme %r in themes.local.toml: name is reserved for the "
                "built-in rainbow mode",
                name,
            )
            continue
        try:
            themes[name] = Theme(
                ring=_parse_color(colors["ring"]),
                eq_low=_parse_color(colors["eq_low"]),
                eq_high=_parse_color(colors["eq_high"]),
                particle=_parse_color(colors["particle"]),
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("Skipping invalid theme %r in themes.local.toml: %s", name, exc)

    return themes


THEMES: dict[str, Theme] = {**BUILTIN_THEMES, **_load_local_themes()}
THEME_NAMES = list(THEMES.keys())


def get_theme(name: str) -> Theme:
    return THEMES.get(name, THEMES[DEFAULT_THEME])
