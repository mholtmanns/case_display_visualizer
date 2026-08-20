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
        self.pulse = 0.0  # 0..1, driven by energy (e.g. GPU load)
        self.rotation_speed = 0.4  # rad/s at rest
        self.sides_base = 6
        self.sides_step = 2

    def set_energy(self, energy: float) -> None:
        self.pulse = energy

    def set_color(self, color: tuple[int, int, int]) -> None:
        self.color = color

    def set_shape_variant(self, ring_count: int, sides_step: int, sides_base: int = 6) -> None:
        self.ring_count = ring_count
        self.sides_step = sides_step
        self.sides_base = sides_base

    def update(self, dt: float) -> None:
        self.time += dt

    def draw(self, surface: pygame.Surface) -> None:
        rotation_speed = self.rotation_speed * (1.0 + self.pulse * 3.0)
        radius_boost = self.pulse * 30.0

        for i in range(self.ring_count):
            sides = max(3, self.sides_base + i * self.sides_step)
            wobble = math.sin(self.time * 1.5 + i) * 4
            radius = self.base_radius + i * 22 + wobble + radius_boost
            rotation = self.time * rotation_speed * (1 if i % 2 == 0 else -1)
            points = regular_polygon_points(self.center, radius, sides, rotation)

            fade = max(60, 255 - i * 45)
            brightness = 1.0 + self.pulse * 0.8
            color = tuple(
                min(255, int(c * fade / 255 * brightness)) for c in self.color
            )
            draw_glow_polygon(surface, points, color, width=2)
