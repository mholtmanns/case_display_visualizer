"""Rotating concentric polygon rings, HUD/sci-fi core visual."""

from __future__ import annotations

import math

import pygame

from case_display_visualizer.render.primitives import (
    draw_glow_polygon,
    regular_polygon_points,
)


class HexRings:
    def __init__(
        self,
        center: tuple[float, float],
        base_radius: float = 90.0,
        ring_count: int = 4,
        color: tuple[int, int, int] = (0, 220, 220),
    ) -> None:
        self.center = center
        self.base_radius = base_radius
        self.ring_count = ring_count
        self.color = color
        self.time = 0.0
        self.pulse = 0.0  # 0..1, driven by energy in later stages
        self.rotation_speed = 0.4  # rad/s

    def update(self, dt: float) -> None:
        self.time += dt

    def draw(self, surface: pygame.Surface) -> None:
        for i in range(self.ring_count):
            sides = 6 + i * 2
            radius = self.base_radius + i * 22 + math.sin(self.time * 1.5 + i) * 4
            rotation = self.time * self.rotation_speed * (1 if i % 2 == 0 else -1)
            points = regular_polygon_points(self.center, radius, sides, rotation)

            fade = max(60, 255 - i * 45)
            color = tuple(min(255, int(c * fade / 255)) for c in self.color)
            draw_glow_polygon(surface, points, color, width=2)
