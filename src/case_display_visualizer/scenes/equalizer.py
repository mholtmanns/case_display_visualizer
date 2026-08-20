"""Bottom-anchored frequency bar equalizer, classic visualizer style."""

from __future__ import annotations

import numpy as np
import pygame

RISE_RATE = 18.0  # per second, how fast bars jump up
FALL_RATE = 4.0  # per second, how fast bars settle back down


class EqualizerBars:
    def __init__(
        self,
        width: int,
        height: int,
        band_count: int = 32,
        max_bar_height: float = 140.0,
        low_color: tuple[int, int, int] = (0, 200, 220),
        high_color: tuple[int, int, int] = (200, 60, 220),
    ) -> None:
        self.width = width
        self.height = height
        self.band_count = band_count
        self.max_bar_height = max_bar_height
        self.low_color = low_color
        self.high_color = high_color

        self._target = np.zeros(band_count, dtype=np.float32)
        self._display = np.zeros(band_count, dtype=np.float32)

    def set_bands(self, bands: np.ndarray) -> None:
        self._target = bands

    def set_colors(
        self, low_color: tuple[int, int, int], high_color: tuple[int, int, int]
    ) -> None:
        self.low_color = low_color
        self.high_color = high_color

    def update(self, dt: float) -> None:
        rising = self._target > self._display
        rate = np.where(rising, RISE_RATE, FALL_RATE)
        blend = np.clip(rate * dt, 0.0, 1.0)
        self._display += (self._target - self._display) * blend

    def draw(self, surface: pygame.Surface) -> None:
        gap = 2
        bar_width = (self.width - gap * (self.band_count - 1)) / self.band_count

        for i, value in enumerate(self._display):
            bar_height = int(max(2.0, float(value) * self.max_bar_height))
            x = int(i * (bar_width + gap))
            y = int(self.height - bar_height)

            t = i / max(1, self.band_count - 1)
            color = tuple(
                int(self.low_color[c] + (self.high_color[c] - self.low_color[c]) * t)
                for c in range(3)
            )
            rect = pygame.Rect(x, y, int(bar_width), bar_height)
            pygame.draw.rect(surface, color, rect)

            cap_rect = pygame.Rect(x, y, int(bar_width), 2)
            pygame.draw.rect(surface, (255, 255, 255), cap_rect)
