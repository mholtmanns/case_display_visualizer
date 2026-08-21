"""Frequency bar equalizer -- either a classic bottom-anchored bar row, or
bars radiating outward from a circle that encloses the hex rings.
"""

from __future__ import annotations

import math

import numpy as np
import pygame

RISE_RATE = 18.0  # per second, how fast bars jump up
FALL_RATE = 4.0  # per second, how fast bars settle back down
# Slow continuous spin for the radial layout, rad/s (~50s per revolution).
# Most audio energy tends to sit in the same low-frequency bands, so a
# fixed angular mapping would leave the same few bars doing all the work;
# rotating keeps it visually dynamic.
RADIAL_ROTATION_SPEED = 0.125

STYLES = ("bottom", "radial")
DEFAULT_STYLE = "bottom"


class EqualizerBars:
    def __init__(
        self,
        width: int,
        height: int,
        band_count: int = 32,
        max_bar_height: float = 140.0,
        low_color: tuple[int, int, int] = (0, 200, 220),
        high_color: tuple[int, int, int] = (200, 60, 220),
        style: str = DEFAULT_STYLE,
        center: tuple[float, float] | None = None,
        inner_radius: float = 170.0,
    ) -> None:
        self.width = width
        self.height = height
        self.band_count = band_count
        self.max_bar_height = max_bar_height
        self.low_color = low_color
        self.high_color = high_color
        self.style = style
        self.center = center if center is not None else (width / 2, height / 2)
        self.inner_radius = inner_radius

        self._target = np.zeros(band_count, dtype=np.float32)
        self._display = np.zeros(band_count, dtype=np.float32)
        self._rotation = 0.0
        self.band_colors: list[tuple[int, int, int]] | None = None

    def set_bands(self, bands: np.ndarray) -> None:
        self._target = bands

    def set_static_ramp(self, low: float = 0.05, high: float = 1.0) -> None:
        """Freeze bars into a fixed low->high ramp, first bar to last, with
        no rise/fall animation -- used by -static for tuning colors."""
        ramp = np.linspace(low, high, self.band_count, dtype=np.float32)
        self._target = ramp
        self._display = ramp.copy()

    def set_colors(
        self, low_color: tuple[int, int, int], high_color: tuple[int, int, int]
    ) -> None:
        self.low_color = low_color
        self.high_color = high_color

    def set_band_colors(self, colors: list[tuple[int, int, int]] | None) -> None:
        """Per-band color override (e.g. for rainbow "aurora" chase mode);
        pass None to fall back to the low->high gradient from set_colors()."""
        self.band_colors = colors

    def set_center(self, center: tuple[float, float]) -> None:
        """Only meaningful in "radial" style; ignored by "bottom"."""
        self.center = center

    def set_style(self, style: str, inner_radius: float | None = None) -> None:
        if style in STYLES:
            self.style = style
        if inner_radius is not None:
            self.inner_radius = inner_radius

    def update(self, dt: float) -> None:
        rising = self._target > self._display
        rate = np.where(rising, RISE_RATE, FALL_RATE)
        blend = np.clip(rate * dt, 0.0, 1.0)
        self._display += (self._target - self._display) * blend

        self._rotation = (self._rotation + RADIAL_ROTATION_SPEED * dt) % (2 * math.pi)

    def _color_for(self, index: int) -> tuple[int, int, int]:
        if self.band_colors:
            return self.band_colors[index % len(self.band_colors)]
        t = index / max(1, self.band_count - 1)
        return tuple(
            int(self.low_color[c] + (self.high_color[c] - self.low_color[c]) * t)
            for c in range(3)
        )

    def _bar_pixel_width(self) -> float:
        """Same tangential width as the bottom bars, for visual parity."""
        gap = 2
        return (self.width - gap * (self.band_count - 1)) / self.band_count

    def draw(self, surface: pygame.Surface) -> None:
        if self.style == "radial":
            self._draw_radial(surface)
        else:
            self._draw_bottom(surface)

    def _draw_bottom(self, surface: pygame.Surface) -> None:
        gap = 2
        bar_width = self._bar_pixel_width()

        for i, value in enumerate(self._display):
            bar_height = int(max(2.0, float(value) * self.max_bar_height))
            x = int(i * (bar_width + gap))
            y = int(self.height - bar_height)

            color = self._color_for(i)
            rect = pygame.Rect(x, y, int(bar_width), bar_height)
            pygame.draw.rect(surface, color, rect)

            cap_rect = pygame.Rect(x, y, int(bar_width), 2)
            pygame.draw.rect(surface, (255, 255, 255), cap_rect)

    def _draw_radial(self, surface: pygame.Surface) -> None:
        cx, cy = self.center
        half_width = self._bar_pixel_width() / 2

        for i, value in enumerate(self._display):
            length = max(2.0, float(value) * self.max_bar_height)
            # Start at 12 o'clock, go clockwise, plus the slow continuous spin.
            angle = (i / self.band_count) * 2 * math.pi - math.pi / 2 + self._rotation

            cos_a, sin_a = math.cos(angle), math.sin(angle)
            perp_x, perp_y = -sin_a, cos_a

            inner_x = cx + self.inner_radius * cos_a
            inner_y = cy + self.inner_radius * sin_a
            outer_x = cx + (self.inner_radius + length) * cos_a
            outer_y = cy + (self.inner_radius + length) * sin_a

            quad = [
                (inner_x + perp_x * half_width, inner_y + perp_y * half_width),
                (inner_x - perp_x * half_width, inner_y - perp_y * half_width),
                (outer_x - perp_x * half_width, outer_y - perp_y * half_width),
                (outer_x + perp_x * half_width, outer_y + perp_y * half_width),
            ]

            color = self._color_for(i)
            pygame.draw.polygon(surface, color, quad)

            cap = [
                (outer_x + perp_x * half_width, outer_y + perp_y * half_width),
                (outer_x - perp_x * half_width, outer_y - perp_y * half_width),
            ]
            pygame.draw.line(surface, (255, 255, 255), cap[0], cap[1], 2)
