"""Rotating concentric polygon rings, HUD/sci-fi core visual."""

from __future__ import annotations

import math

import pygame

from case_display_visualizer.render.primitives import (
    draw_glow_polygon,
    regular_polygon_points,
)

DEFAULT_BASE_RADIUS = 90.0
# Smaller/fixed-count layout used when the radial equalizer encloses the
# rings, so its enclosing circle has predictable, guaranteed clearance.
COMPACT_BASE_RADIUS = 50.0
COMPACT_RING_COUNT = 4
RING_SPACING = 22.0
MAX_WOBBLE = 4.0
MAX_PULSE_BOOST = 30.0
# Worst-case outer edge of the compact ring set (base + spacing + wobble +
# full pulse boost) -- a radial equalizer's inner_radius should clear this.
COMPACT_MAX_REACH = (
    COMPACT_BASE_RADIUS + (COMPACT_RING_COUNT - 1) * RING_SPACING + MAX_WOBBLE + MAX_PULSE_BOOST
)


class HexRings:
    def __init__(
        self,
        center: tuple[float, float],
        base_radius: float = DEFAULT_BASE_RADIUS,
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
        self.line_thickness = 1
        self.ring_count_locked = False
        self.ring_colors: list[tuple[int, int, int]] | None = None

    def set_energy(self, energy: float) -> None:
        self.pulse = energy

    def set_center(self, center: tuple[float, float]) -> None:
        self.center = center

    def set_color(self, color: tuple[int, int, int]) -> None:
        self.color = color

    def set_ring_colors(self, colors: list[tuple[int, int, int]] | None) -> None:
        """Per-ring color override (e.g. for rainbow "aurora" chase mode);
        pass None to fall back to the single uniform color from set_color()."""
        self.ring_colors = colors

    def set_line_thickness(self, thickness: int) -> None:
        self.line_thickness = max(1, min(6, thickness))

    def set_shape_variant(self, ring_count: int, sides_step: int, sides_base: int = 6) -> None:
        if not self.ring_count_locked:
            self.ring_count = ring_count
        self.sides_step = sides_step
        self.sides_base = sides_base

    def set_compact(self, enabled: bool) -> None:
        """Lock to a small, fixed-count layout (used by the radial
        equalizer, which needs predictable clearance for its enclosing
        circle), or restore the normal variable size/count."""
        if enabled:
            self.ring_count_locked = True
            self.ring_count = COMPACT_RING_COUNT
            self.base_radius = COMPACT_BASE_RADIUS
        else:
            self.ring_count_locked = False
            self.base_radius = DEFAULT_BASE_RADIUS

    def update(self, dt: float) -> None:
        self.time += dt

    def draw(self, surface: pygame.Surface) -> None:
        rotation_speed = self.rotation_speed * (1.0 + self.pulse * 3.0)
        radius_boost = self.pulse * MAX_PULSE_BOOST

        for i in range(self.ring_count):
            sides = max(3, self.sides_base + i * self.sides_step)
            wobble = math.sin(self.time * 1.5 + i) * MAX_WOBBLE
            radius = self.base_radius + i * RING_SPACING + wobble + radius_boost
            rotation = self.time * rotation_speed * (1 if i % 2 == 0 else -1)
            points = regular_polygon_points(self.center, radius, sides, rotation)

            base_color = (
                self.ring_colors[i % len(self.ring_colors)] if self.ring_colors else self.color
            )
            fade = max(60, 255 - i * 45)
            brightness = 1.0 + self.pulse * 0.8
            color = tuple(
                min(255, int(c * fade / 255 * brightness)) for c in base_color
            )
            draw_glow_polygon(surface, points, color, width=self.line_thickness)
