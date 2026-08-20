"""Scrolling starfield background layer."""

from __future__ import annotations

import random

import pygame


class Starfield:
    def __init__(
        self,
        width: int,
        height: int,
        star_count: int = 120,
        base_speed: float = 20.0,
    ) -> None:
        self.width = width
        self.height = height
        self.base_speed = base_speed
        self.speed_multiplier = 1.0
        self.stars = [
            [
                random.uniform(0, width),
                random.uniform(0, height),
                random.uniform(0.3, 1.0),  # depth: smaller = farther/dimmer
            ]
            for _ in range(star_count)
        ]

    def set_energy(self, energy: float) -> None:
        """Drive scroll speed from a 0..1 energy value (e.g. CPU load)."""
        self.speed_multiplier = 0.5 + energy * 3.0

    def update(self, dt: float) -> None:
        for star in self.stars:
            star[0] -= self.base_speed * self.speed_multiplier * star[2] * dt
            if star[0] < 0:
                star[0] = self.width
                star[1] = random.uniform(0, self.height)

    def draw(self, surface: pygame.Surface) -> None:
        for x, y, depth in self.stars:
            brightness = int(80 + depth * 175)
            color = (brightness, brightness, min(255, brightness + 30))
            size = 1 if depth < 0.7 else 2
            pygame.draw.circle(surface, color, (int(x), int(y)), size)
