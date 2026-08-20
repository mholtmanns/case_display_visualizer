"""Periodically shuffles color theme and ring shape so idle visuals don't
look static even under constant sensor input.
"""

from __future__ import annotations

import random

from case_display_visualizer.themes import THEME_NAMES

DEFAULT_INTERVAL_SECONDS = 240.0

RING_COUNT_RANGE = (3, 6)
SIDES_STEP_CHOICES = (1, 2, 3)
SIDES_BASE_CHOICES = (3, 4, 5, 6)


class SceneRandomizer:
    def __init__(self, interval_seconds: float = DEFAULT_INTERVAL_SECONDS) -> None:
        self.interval_seconds = interval_seconds
        self._elapsed = 0.0
        self._last_theme: str | None = None

    def update(self, dt: float) -> bool:
        """Advance the timer; returns True on the tick a reshuffle is due."""
        self._elapsed += dt
        if self._elapsed >= self.interval_seconds:
            self._elapsed = 0.0
            return True
        return False

    def next_theme(self) -> str:
        choices = [t for t in THEME_NAMES if t != self._last_theme] or THEME_NAMES
        theme = random.choice(choices)
        self._last_theme = theme
        return theme

    def next_ring_variant(self) -> tuple[int, int, int]:
        ring_count = random.randint(*RING_COUNT_RANGE)
        sides_step = random.choice(SIDES_STEP_CHOICES)
        sides_base = random.choice(SIDES_BASE_CHOICES)
        return ring_count, sides_step, sides_base
