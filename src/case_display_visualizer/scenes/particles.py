"""Short-lived radial particle bursts, triggered by discrete events."""

from __future__ import annotations

import math
import random

import pygame

PARTICLE_LIFETIME = 0.6  # seconds
PARTICLE_SPEED_RANGE = (120.0, 260.0)
PARTICLES_PER_BURST = 14


class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "age", "color")

    def __init__(self, x: float, y: float, vx: float, vy: float, color: tuple[int, int, int]):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.age = 0.0
        self.color = color


class ParticleBursts:
    def __init__(
        self,
        center: tuple[float, float],
        color: tuple[int, int, int] = (255, 200, 60),
    ) -> None:
        self.center = center
        self.color = color
        self._particles: list[_Particle] = []

    def set_color(self, color: tuple[int, int, int]) -> None:
        self.color = color

    def set_center(self, center: tuple[float, float]) -> None:
        self.center = center

    def trigger(self, count: int = 1) -> None:
        for _ in range(min(count, 3)):  # cap so key-repeat can't flood it
            self._spawn_burst()

    def _spawn_burst(self) -> None:
        cx, cy = self.center
        for _ in range(PARTICLES_PER_BURST):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(*PARTICLE_SPEED_RANGE)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self._particles.append(_Particle(cx, cy, vx, vy, self.color))

    def update(self, dt: float) -> None:
        for p in self._particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.age += dt
        self._particles = [p for p in self._particles if p.age < PARTICLE_LIFETIME]

    def draw(self, surface: pygame.Surface) -> None:
        for p in self._particles:
            fade = 1.0 - (p.age / PARTICLE_LIFETIME)
            radius = max(1, int(3 * fade))
            color = tuple(int(c * fade) for c in p.color)
            pygame.draw.circle(surface, color, (int(p.x), int(p.y)), radius)
