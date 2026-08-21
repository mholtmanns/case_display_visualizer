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
from case_display_visualizer.icon import build_icon_image
from case_display_visualizer.rainbow import is_rainbow_mode, rainbow_color
from case_display_visualizer.randomizer import SceneRandomizer
from case_display_visualizer.scenes.equalizer import EqualizerBars
from case_display_visualizer.scenes.hex_rings import COMPACT_MAX_REACH, HexRings
from case_display_visualizer.scenes.particles import ParticleBursts
from case_display_visualizer.scenes.starfield import TUNNEL_DIRECTIONS, Starfield
from case_display_visualizer.sensors.audio import AudioSensor
from case_display_visualizer.sensors.cpu import CpuSensor
from case_display_visualizer.sensors.gpu import GpuSensor
from case_display_visualizer.sensors.input_activity import InputActivitySensor
from case_display_visualizer.settings import load_settings
from case_display_visualizer.themes import DEFAULT_THEME, get_theme
from case_display_visualizer.tray import build_tray_icon
from case_display_visualizer.wander import CenterWander

BACKGROUND_COLOR = (5, 6, 12)
TARGET_FPS = 60
# Clearance margin beyond the compact rings' worst-case reach, so the radial
# equalizer's inner circle never visually collides with the rings.
RADIAL_EQUALIZER_MARGIN = 20.0
RADIAL_EQUALIZER_INNER_RADIUS = COMPACT_MAX_REACH + RADIAL_EQUALIZER_MARGIN

_HWND_TOPMOST = -1
_SWP_NOMOVE = 0x0002
_SWP_NOSIZE = 0x0001


def _set_app_user_model_id() -> None:
    """Give this process its own taskbar identity.

    Without this, Windows groups a raw python.exe/pythonw.exe process under
    the interpreter's own icon for the taskbar button, ignoring the window
    icon set via pygame.display.set_icon() (title bar/Alt+Tab pick it up
    fine either way -- only the taskbar button needs this).
    """
    if sys.platform != "win32":
        return
    import ctypes

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "CaseDisplayVisualizer.App"
        )
    except OSError:
        pass


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


def _apply_equalizer_style(style: str, hex_rings: HexRings, equalizer: EqualizerBars) -> None:
    """Radial mode needs the rings compact/fixed-count so the equalizer's
    enclosing circle has guaranteed clearance; bottom mode restores normal
    ring sizing/count variability."""
    is_radial = style == "radial"
    hex_rings.set_compact(is_radial)
    equalizer.set_style(style, inner_radius=RADIAL_EQUALIZER_INNER_RADIUS)


def _apply_theme(
    color_theme: str,
    effective_static_theme: str,
    rainbow_elapsed: float,
    applied_theme: str | None,
    hex_rings: HexRings,
    equalizer: EqualizerBars,
    particles: ParticleBursts,
) -> str:
    """Applies either a concrete named theme (once, only when it changes) or
    continuously recomputed rainbow colors (every call, since it animates).
    Returns the new applied_theme to track.
    """
    if is_rainbow_mode(color_theme):
        hex_rings.set_ring_colors(
            [
                rainbow_color(rainbow_elapsed, color_theme, i, hex_rings.ring_count)
                for i in range(hex_rings.ring_count)
            ]
        )
        equalizer.set_band_colors(
            [
                rainbow_color(rainbow_elapsed, color_theme, i, equalizer.band_count)
                for i in range(equalizer.band_count)
            ]
        )
        particles.set_color(rainbow_color(rainbow_elapsed, color_theme))
        return color_theme

    if effective_static_theme != applied_theme:
        theme = get_theme(effective_static_theme)
        hex_rings.set_color(theme.ring)
        hex_rings.set_ring_colors(None)
        equalizer.set_colors(theme.eq_low, theme.eq_high)
        equalizer.set_band_colors(None)
        particles.set_color(theme.particle)
        return effective_static_theme

    return applied_theme


def run(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    windowed = args.windowed
    static = args.static
    verbose = args.verbose

    target = find_target_display()
    settings = load_settings()

    if verbose >= 1:
        dump_config(target, settings, windowed, static)

    _set_app_user_model_id()

    pygame.init()
    pygame.display.set_caption("Case Display Visualizer")

    icon_image = build_icon_image(size=64)
    pygame.display.set_icon(
        pygame.image.fromstring(icon_image.tobytes(), icon_image.size, icon_image.mode)
    )

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

    default_center = (target.width / 2, target.height / 2)

    starfield = Starfield(target.width, target.height)
    hex_rings = HexRings(center=default_center)
    equalizer = EqualizerBars(target.width, target.height)
    particles = ParticleBursts(center=default_center)
    layers = [starfield, hex_rings, equalizer, particles]

    if static:
        # -static is for tuning colors/settings by eye: no sensors, no
        # randomizer, no motion. The equalizer gets a fixed 5%-100% ramp
        # (first bar to last) instead of live audio so every bar is visible
        # at a distinct height.
        audio_sensor = None
        input_sensor = None
        composer = None
        wander = None
        equalizer.set_static_ramp()
    else:
        audio_sensor = AudioSensor()
        input_sensor = InputActivitySensor()
        composer = Composer([CpuSensor(), GpuSensor(), audio_sensor, input_sensor])
        wander = CenterWander(target.width, target.height)

    tray_icon = build_tray_icon(settings)
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
    tray_thread.start()

    if not static:
        randomizer = SceneRandomizer()
        current_auto_theme = randomizer.next_theme()
        hex_rings.set_shape_variant(*randomizer.next_ring_variant())
    applied_theme = None
    applied_equalizer_style = None
    rainbow_elapsed = 0.0

    telemetry = LiveTelemetry() if verbose >= 2 and not static else None

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

            visual_dt = dt * settings.speed_multiplier

            if not windowed:
                # Overlay tools like Rainmeter periodically re-assert their
                # own topmost flag; keep re-winning the top spot rather than
                # setting it once at startup.
                topmost_reassert_timer += dt
                if topmost_reassert_timer >= 0.25:
                    topmost_reassert_timer = 0.0
                    _set_always_on_top()

            if static:
                # Settings (theme/thickness/direction) still react live via
                # the tray so colors can be tuned, but nothing animates and
                # no sensors are sampled.
                effective_theme = (
                    settings.color_theme if settings.color_theme != "auto" else DEFAULT_THEME
                )
                applied_theme = _apply_theme(
                    settings.color_theme,
                    effective_theme,
                    rainbow_elapsed,
                    applied_theme,
                    hex_rings,
                    equalizer,
                    particles,
                )

                hex_rings.set_line_thickness(settings.line_thickness)
                starfield.set_direction(settings.starfield_direction)

                if settings.equalizer_style != applied_equalizer_style:
                    applied_equalizer_style = settings.equalizer_style
                    _apply_equalizer_style(applied_equalizer_style, hex_rings, equalizer)
            else:
                if randomizer.update(dt):
                    current_auto_theme = randomizer.next_theme()
                    hex_rings.set_shape_variant(*randomizer.next_ring_variant())

                effective_theme = (
                    current_auto_theme
                    if settings.color_theme == "auto"
                    else settings.color_theme
                )
                rainbow_elapsed += visual_dt
                applied_theme = _apply_theme(
                    settings.color_theme,
                    effective_theme,
                    rainbow_elapsed,
                    applied_theme,
                    hex_rings,
                    equalizer,
                    particles,
                )

                hex_rings.set_line_thickness(settings.line_thickness)
                starfield.set_direction(settings.starfield_direction)

                if settings.equalizer_style != applied_equalizer_style:
                    applied_equalizer_style = settings.equalizer_style
                    _apply_equalizer_style(applied_equalizer_style, hex_rings, equalizer)

                center = wander.update(dt) if settings.moving_center else default_center
                hex_rings.set_center(center)
                particles.set_center(center)
                if settings.equalizer_style == "radial":
                    equalizer.set_center(center)
                if settings.starfield_direction in TUNNEL_DIRECTIONS:
                    starfield.set_center(center)

                energy = composer.update(dt)

                def energy_of(name: str) -> float:
                    return energy.get(name) if settings.is_enabled(name) else 0.0

                starfield.set_energy(max(energy_of("cpu"), energy_of("input") * 0.6))
                hex_rings.set_energy(max(energy_of("gpu"), energy_of("audio")))
                equalizer.set_bands(
                    audio_sensor.get_bands()
                    if settings.is_enabled("audio")
                    else audio_sensor.get_bands() * 0
                )

                if settings.is_enabled("input"):
                    burst_events = input_sensor.pop_burst_events()
                    if burst_events:
                        particles.trigger(burst_events)
                else:
                    input_sensor.pop_burst_events()

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
        if audio_sensor is not None:
            audio_sensor.close()
        if input_sensor is not None:
            input_sensor.close()
        pygame.quit()

    sys.exit(0)
