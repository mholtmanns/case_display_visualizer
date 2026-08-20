"""Main application loop: sets up the window and drives scene layers."""

from __future__ import annotations

import sys

import pygame

from case_display_visualizer.composer import Composer
from case_display_visualizer.display import find_target_display
from case_display_visualizer.scenes.hex_rings import HexRings
from case_display_visualizer.scenes.starfield import Starfield
from case_display_visualizer.sensors.cpu import CpuSensor
from case_display_visualizer.sensors.gpu import GpuSensor

BACKGROUND_COLOR = (5, 6, 12)
TARGET_FPS = 60

_HWND_TOPMOST = -1
_SWP_NOMOVE = 0x0002
_SWP_NOSIZE = 0x0001


def _set_always_on_top() -> None:
    """Keep the window above other always-on-top overlays (e.g. Rainmeter)."""
    if sys.platform != "win32":
        return
    import ctypes

    hwnd = pygame.display.get_wm_info().get("window")
    if not hwnd:
        return
    ctypes.windll.user32.SetWindowPos(
        ctypes.c_void_p(hwnd),
        ctypes.c_void_p(_HWND_TOPMOST),
        0,
        0,
        0,
        0,
        _SWP_NOMOVE | _SWP_NOSIZE,
    )


def run() -> None:
    target = find_target_display()

    pygame.init()
    pygame.display.set_caption("Case Display Visualizer")

    import os

    os.environ["SDL_VIDEO_WINDOW_POS"] = f"{target.x},{target.y}"

    flags = pygame.NOFRAME
    surface = pygame.display.set_mode((target.width, target.height), flags)
    _set_always_on_top()

    clock = pygame.time.Clock()
    topmost_reassert_timer = 0.0

    starfield = Starfield(target.width, target.height)
    hex_rings = HexRings(center=(target.width / 2, target.height / 2))
    layers = [starfield, hex_rings]

    composer = Composer([CpuSensor(), GpuSensor()])

    running = True
    while running:
        dt = clock.tick(TARGET_FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # Overlay tools like Rainmeter periodically re-assert their own
        # topmost flag; keep re-winning the top spot rather than setting it
        # once at startup.
        topmost_reassert_timer += dt
        if topmost_reassert_timer >= 1.0:
            topmost_reassert_timer = 0.0
            _set_always_on_top()

        energy = composer.update(dt)
        starfield.set_energy(energy.get("cpu"))
        hex_rings.set_energy(energy.get("gpu"))

        for layer in layers:
            layer.update(dt)

        surface.fill(BACKGROUND_COLOR)
        for layer in layers:
            layer.draw(surface)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)
