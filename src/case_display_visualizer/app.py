"""Main application loop: sets up the window and drives scene layers."""

from __future__ import annotations

import os
import sys
import threading

import pygame

from case_display_visualizer.cli import parse_args
from case_display_visualizer.composer import Composer
from case_display_visualizer.debug import LiveTelemetry, dump_config
from case_display_visualizer.display import find_target_display
from case_display_visualizer.randomizer import SceneRandomizer
from case_display_visualizer.scenes.equalizer import EqualizerBars
from case_display_visualizer.scenes.hex_rings import HexRings
from case_display_visualizer.scenes.particles import ParticleBursts
from case_display_visualizer.scenes.starfield import Starfield
from case_display_visualizer.sensors.audio import AudioSensor
from case_display_visualizer.sensors.cpu import CpuSensor
from case_display_visualizer.sensors.gpu import GpuSensor
from case_display_visualizer.sensors.input_activity import InputActivitySensor
from case_display_visualizer.settings import load_settings
from case_display_visualizer.themes import get_theme
from case_display_visualizer.tray import build_tray_icon

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


def run(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    windowed = args.windowed
    verbose = args.verbose

    target = find_target_display()
    settings = load_settings()

    if verbose >= 1:
        dump_config(target, settings, windowed)

    pygame.init()
    pygame.display.set_caption("Case Display Visualizer")

    if windowed:
        flags = 0
        surface = pygame.display.set_mode((target.width, target.height), flags)
    else:
        os.environ["SDL_VIDEO_WINDOW_POS"] = f"{target.x},{target.y}"
        flags = pygame.NOFRAME
        surface = pygame.display.set_mode((target.width, target.height), flags)
        _set_always_on_top()

    clock = pygame.time.Clock()
    topmost_reassert_timer = 0.0

    starfield = Starfield(target.width, target.height)
    hex_rings = HexRings(center=(target.width / 2, target.height / 2))
    equalizer = EqualizerBars(target.width, target.height)
    particles = ParticleBursts(center=(target.width / 2, target.height / 2))
    layers = [starfield, hex_rings, equalizer, particles]

    audio_sensor = AudioSensor()
    input_sensor = InputActivitySensor()
    composer = Composer([CpuSensor(), GpuSensor(), audio_sensor, input_sensor])

    tray_icon = build_tray_icon(settings)
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
    tray_thread.start()

    randomizer = SceneRandomizer()
    current_auto_theme = randomizer.next_theme()
    hex_rings.set_shape_variant(*randomizer.next_ring_variant())
    applied_theme = None

    telemetry = LiveTelemetry() if verbose >= 2 else None

    try:
        running = True
        while running:
            dt = clock.tick(TARGET_FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            if settings.quit_requested:
                running = False

            if not windowed:
                # Overlay tools like Rainmeter periodically re-assert their
                # own topmost flag; keep re-winning the top spot rather than
                # setting it once at startup.
                topmost_reassert_timer += dt
                if topmost_reassert_timer >= 0.25:
                    topmost_reassert_timer = 0.0
                    _set_always_on_top()

            if randomizer.update(dt):
                current_auto_theme = randomizer.next_theme()
                hex_rings.set_shape_variant(*randomizer.next_ring_variant())

            effective_theme = (
                current_auto_theme if settings.color_theme == "auto" else settings.color_theme
            )
            if effective_theme != applied_theme:
                applied_theme = effective_theme
                theme = get_theme(applied_theme)
                hex_rings.set_color(theme.ring)
                equalizer.set_colors(theme.eq_low, theme.eq_high)
                particles.set_color(theme.particle)

            hex_rings.set_line_thickness(settings.line_thickness)

            energy = composer.update(dt)

            def energy_of(name: str) -> float:
                return energy.get(name) if settings.is_enabled(name) else 0.0

            starfield.set_energy(max(energy_of("cpu"), energy_of("input") * 0.6))
            hex_rings.set_energy(max(energy_of("gpu"), energy_of("audio")))
            equalizer.set_bands(
                audio_sensor.get_bands() if settings.is_enabled("audio") else audio_sensor.get_bands() * 0
            )

            if settings.is_enabled("input"):
                burst_events = input_sensor.pop_burst_events()
                if burst_events:
                    particles.trigger(burst_events)
            else:
                input_sensor.pop_burst_events()

            visual_dt = dt * settings.speed_multiplier
            starfield.update(visual_dt)
            hex_rings.update(visual_dt)
            equalizer.update(dt)
            particles.update(dt)

            surface.fill(BACKGROUND_COLOR)
            for layer in layers:
                layer.draw(surface)
            pygame.display.flip()

            if telemetry is not None:
                telemetry.update(dt, energy, settings, applied_theme, clock.get_fps())
    finally:
        if telemetry is not None:
            telemetry.close()
        tray_icon.stop()
        audio_sensor.close()
        input_sensor.close()
        pygame.quit()

    sys.exit(0)
