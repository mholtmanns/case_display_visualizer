"""Low-level drawing helpers for sci-fi style shapes."""

from __future__ import annotations

import math
from typing import Sequence

import pygame


def regular_polygon_points(
    center: tuple[float, float],
    radius: float,
    sides: int,
    rotation: float = 0.0,
) -> list[tuple[float, float]]:
    """Return vertex points for a regular polygon centered at `center`."""
    cx, cy = center
    points = []
    for i in range(sides):
        angle = rotation + (2 * math.pi * i / sides)
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def draw_glow_polygon(
    surface: pygame.Surface,
    points: Sequence[tuple[float, float]],
    color: tuple[int, int, int],
    width: int = 2,
    glow_passes: int = 3,
) -> None:
    """Draw a polygon outline with a soft additive glow, sci-fi HUD style."""
    for i in range(glow_passes, 0, -1):
        alpha = max(10, 60 // i)
        glow_width = width + i * 2
        glow_color = (*color, alpha)
        _draw_polygon_alpha(surface, points, glow_color, glow_width)

    pygame.draw.polygon(surface, color, points, width)


def _draw_polygon_alpha(
    surface: pygame.Surface,
    points: Sequence[tuple[float, float]],
    color: tuple[int, int, int, int],
    width: int,
) -> None:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    pad = width + 4
    min_x, max_x = min(xs) - pad, max(xs) + pad
    min_y, max_y = min(ys) - pad, max(ys) + pad
    w, h = max(1, int(max_x - min_x)), max(1, int(max_y - min_y))

    temp = pygame.Surface((w, h), pygame.SRCALPHA)
    shifted = [(x - min_x, y - min_y) for x, y in points]
    pygame.draw.polygon(temp, color, shifted, width)
    surface.blit(temp, (min_x, min_y))
