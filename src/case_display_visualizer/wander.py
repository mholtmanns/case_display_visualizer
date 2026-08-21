"""Smooth, non-repeating wander path for the shared hex-ring / radial
equalizer / tunnel-starfield center point.

Uses a rolling window of 4 randomized waypoints and a uniform Catmull-Rom
spline through the middle segment: continuous, curved, and never repeats
(each finished segment drops its oldest waypoint and appends a fresh random
one) -- deliberately not the straight-line, bounce-off-the-wall motion of
old floating-logo screensavers.
"""

from __future__ import annotations

import random

# Segments per second. Deliberately fixed and slow rather than tied to the
# Speed setting -- this is a much larger, more structural motion than the
# ring rotation/rainbow cycling, and moving it too fast reads as chaotic
# rather than ambient.
DEFAULT_SPEED = 0.04  # ~25s per leg


def _catmull_rom(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (
        2 * p1
        + (-p0 + p2) * t
        + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
        + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
    )


class CenterWander:
    def __init__(
        self,
        width: float,
        height: float,
        margin: float = 30.0,
        speed: float = DEFAULT_SPEED,
    ) -> None:
        self.min_x = margin
        self.max_x = max(margin, width - margin)
        self.min_y = margin
        self.max_y = max(margin, height - margin)
        self.speed = speed
        self.progress = 0.0
        self._points = [self._random_point() for _ in range(4)]

    def _random_point(self) -> tuple[float, float]:
        return (random.uniform(self.min_x, self.max_x), random.uniform(self.min_y, self.max_y))

    def update(self, dt: float) -> tuple[float, float]:
        self.progress += self.speed * dt
        while self.progress >= 1.0:
            self.progress -= 1.0
            self._points.pop(0)
            self._points.append(self._random_point())
        return self._current_position()

    def _current_position(self) -> tuple[float, float]:
        p0, p1, p2, p3 = self._points
        t = self.progress
        return (
            _catmull_rom(p0[0], p1[0], p2[0], p3[0], t),
            _catmull_rom(p0[1], p1[1], p2[1], p3[1], t),
        )
