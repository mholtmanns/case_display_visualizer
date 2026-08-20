"""Scrolling / tunnel-warp starfield background layer.

Supports four linear scroll directions (left/right/up/down, star field
drifting across the screen) and two perspective "tunnel" directions
(away/towards, stars flying along the z-axis like a warp-speed effect).
Switching between the two families regenerates the star set since they use
different per-star state (screen x/y vs. 3D x/y/z).
"""

from __future__ import annotations

import random

import pygame

LINEAR_DIRECTIONS = ("left", "right", "up", "down")
TUNNEL_DIRECTIONS = ("away", "towards")
ALL_DIRECTIONS = LINEAR_DIRECTIONS + TUNNEL_DIRECTIONS
DEFAULT_DIRECTION = "left"

# Tunnel-mode perspective projection tuning.
FOCAL_LENGTH = 200.0
Z_NEAR = 1.0
Z_FAR = 400.0


class Starfield:
    def __init__(
        self,
        width: int,
        height: int,
        star_count: int = 120,
        base_speed: float = 20.0,
        direction: str = DEFAULT_DIRECTION,
    ) -> None:
        self.width = width
        self.height = height
        self.star_count = star_count
        self.base_speed = base_speed
        self.speed_multiplier = 1.0
        self.direction = direction
        self._init_stars()

    def _init_stars(self) -> None:
        if self.direction in TUNNEL_DIRECTIONS:
            self.stars = [self._make_tunnel_star() for _ in range(self.star_count)]
        else:
            self.stars = [self._make_linear_star() for _ in range(self.star_count)]

    def _make_linear_star(self) -> list[float]:
        return [
            random.uniform(0, self.width),
            random.uniform(0, self.height),
            random.uniform(0.3, 1.0),  # depth: smaller = farther/dimmer
        ]

    def _make_tunnel_star(self, z: float | None = None) -> list[float]:
        return [
            random.uniform(-self.width, self.width),
            random.uniform(-self.height, self.height),
            z if z is not None else random.uniform(Z_NEAR, Z_FAR),
        ]

    def set_direction(self, direction: str) -> None:
        if direction == self.direction:
            return
        was_tunnel = self.direction in TUNNEL_DIRECTIONS
        now_tunnel = direction in TUNNEL_DIRECTIONS
        self.direction = direction
        if was_tunnel != now_tunnel:
            self._init_stars()

    def set_energy(self, energy: float) -> None:
        """Drive scroll speed from a 0..1 energy value (e.g. CPU load)."""
        self.speed_multiplier = 0.5 + energy * 3.0

    def update(self, dt: float) -> None:
        speed = self.base_speed * self.speed_multiplier
        if self.direction in TUNNEL_DIRECTIONS:
            self._update_tunnel(dt, speed)
        else:
            self._update_linear(dt, speed)

    def _update_linear(self, dt: float, speed: float) -> None:
        dx = dy = 0.0
        if self.direction == "right":
            dx = speed
        elif self.direction == "left":
            dx = -speed
        elif self.direction == "down":
            dy = speed
        elif self.direction == "up":
            dy = -speed

        for star in self.stars:
            star[0] += dx * star[2] * dt
            star[1] += dy * star[2] * dt

            if star[0] < 0:
                star[0] = self.width
                star[1] = random.uniform(0, self.height)
            elif star[0] > self.width:
                star[0] = 0
                star[1] = random.uniform(0, self.height)

            if star[1] < 0:
                star[1] = self.height
                star[0] = random.uniform(0, self.width)
            elif star[1] > self.height:
                star[1] = 0
                star[0] = random.uniform(0, self.width)

    def _update_tunnel(self, dt: float, speed: float) -> None:
        z_speed = speed * 4.0
        # "towards" = star approaches the viewer = z shrinks; "away" = z grows.
        sign = -1.0 if self.direction == "towards" else 1.0

        for star in self.stars:
            star[2] += sign * z_speed * dt
            if star[2] <= Z_NEAR:
                star[0] = random.uniform(-self.width, self.width)
                star[1] = random.uniform(-self.height, self.height)
                star[2] = Z_FAR
            elif star[2] >= Z_FAR:
                star[0] = random.uniform(-self.width, self.width)
                star[1] = random.uniform(-self.height, self.height)
                star[2] = Z_NEAR

    def draw(self, surface: pygame.Surface) -> None:
        if self.direction in TUNNEL_DIRECTIONS:
            self._draw_tunnel(surface)
        else:
            self._draw_linear(surface)

    def _draw_linear(self, surface: pygame.Surface) -> None:
        for x, y, depth in self.stars:
            brightness = int(80 + depth * 175)
            color = (brightness, brightness, min(255, brightness + 30))
            size = 1 if depth < 0.7 else 2
            pygame.draw.circle(surface, color, (int(x), int(y)), size)

    def _draw_tunnel(self, surface: pygame.Surface) -> None:
        cx, cy = self.width / 2, self.height / 2
        for sx, sy, sz in self.stars:
            screen_x = cx + sx / sz * FOCAL_LENGTH
            screen_y = cy + sy / sz * FOCAL_LENGTH
            if not (0 <= screen_x < self.width and 0 <= screen_y < self.height):
                continue

            depth_frac = 1.0 - (sz - Z_NEAR) / (Z_FAR - Z_NEAR)  # 1=close, 0=far
            brightness = int(60 + depth_frac * 195)
            color = (brightness, brightness, min(255, brightness + 30))
            size = 1 if depth_frac < 0.6 else (2 if depth_frac < 0.9 else 3)
            pygame.draw.circle(surface, color, (int(screen_x), int(screen_y)), size)
