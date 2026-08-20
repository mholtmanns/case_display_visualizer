"""Frequency bar equalizer -- either a classic bottom-anchored bar row, or
bars radiating outward from a circle that encloses the hex rings.
"""

from __future__ import annotations

import math

import numpy as np
import pygame

RISE_RATE = 18.0  # per second, how fast bars jump up
FALL_RATE = 4.0  # per second, how fast bars settle back down

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

    def _color_for(self, index: int) -> tuple[int, int, int]:
        t = index / max(1, self.band_count - 1)
        return tuple(
            int(self.low_color[c] + (self.high_color[c] - self.low_color[c]) * t)
            for c in range(3)
        )

    def draw(self, surface: pygame.Surface) -> None:
        if self.style == "radial":
            self._draw_radial(surface)
        else:
            self._draw_bottom(surface)

    def _draw_bottom(self, surface: pygame.Surface) -> None:
        gap = 2
        bar_width = (self.width - gap * (self.band_count - 1)) / self.band_count

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

        for i, value in enumerate(self._display):
            length = max(2.0, float(value) * self.max_bar_height)
            # Start at 12 o'clock, go clockwise.
            angle = (i / self.band_count) * 2 * math.pi - math.pi / 2

            cos_a, sin_a = math.cos(angle), math.sin(angle)
            inner = (cx + self.inner_radius * cos_a, cy + self.inner_radius * sin_a)
            outer = (
                cx + (self.inner_radius + length) * cos_a,
                cy + (self.inner_radius + length) * sin_a,
            )

            color = self._color_for(i)
            pygame.draw.line(surface, color, inner, outer, 3)
            pygame.draw.circle(surface, (255, 255, 255), (int(outer[0]), int(outer[1])), 2)
