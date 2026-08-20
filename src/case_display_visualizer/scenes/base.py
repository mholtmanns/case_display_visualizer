"""Common interface for renderable scene layers."""

from __future__ import annotations

from typing import Protocol

import pygame


class SceneLayer(Protocol):
    def update(self, dt: float) -> None:
        """Advance internal animation state by dt seconds."""

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the layer onto the given surface."""
