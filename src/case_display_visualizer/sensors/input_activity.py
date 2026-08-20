"""Keyboard/mouse activity sensor.

Tracks event *rate*, not content -- no keys, text, or click targets are
ever recorded, only counts. Listener callbacks run on pynput's own
background threads.
"""

from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger(__name__)

try:
    from pynput import keyboard, mouse
except ImportError:  # pragma: no cover - optional dependency
    keyboard = None
    mouse = None

# Rough ceiling for "very active" input, in events/sec, used to normalize
# the rate into 0..1.
MAX_EVENTS_PER_SEC = 12.0

# Mouse move events fire far more often than is meaningful; only count one
# per this many seconds of continuous movement.
MOVE_THROTTLE_SEC = 0.05


class InputActivitySensor:
    name = "input"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rate_count = 0
        self._burst_count = 0
        self._last_move_time = 0.0
        self._last_sample_time = time.monotonic()

        self._keyboard_listener = None
        self._mouse_listener = None

        if keyboard is None:
            logger.info("pynput not installed; input activity sensor disabled")
            return

        try:
            self._keyboard_listener = keyboard.Listener(on_press=self._on_press)
            self._mouse_listener = mouse.Listener(
                on_click=self._on_click,
                on_scroll=self._on_scroll,
                on_move=self._on_move,
            )
            self._keyboard_listener.start()
            self._mouse_listener.start()
        except Exception as exc:  # pragma: no cover - depends on OS/permissions
            logger.info("Could not start input listeners; disabled (%s)", exc)
            self._keyboard_listener = None
            self._mouse_listener = None

    def _on_press(self, key) -> None:
        with self._lock:
            self._rate_count += 1
            self._burst_count += 1

    def _on_click(self, x, y, button, pressed) -> None:
        if not pressed:
            return
        with self._lock:
            self._rate_count += 1
            self._burst_count += 1

    def _on_scroll(self, x, y, dx, dy) -> None:
        with self._lock:
            self._rate_count += 1

    def _on_move(self, x, y) -> None:
        now = time.monotonic()
        if now - self._last_move_time < MOVE_THROTTLE_SEC:
            return
        self._last_move_time = now
        with self._lock:
            self._rate_count += 1

    def sample(self) -> float:
        """Normalized 0..1 activity rate since the last sample() call."""
        now = time.monotonic()
        with self._lock:
            elapsed = max(1e-3, now - self._last_sample_time)
            rate = self._rate_count / elapsed
            self._rate_count = 0
            self._last_sample_time = now

        return min(1.0, rate / MAX_EVENTS_PER_SEC)

    def pop_burst_events(self) -> int:
        """Discrete keypress/click count since the last call (for triggers)."""
        with self._lock:
            count = self._burst_count
            self._burst_count = 0
        return count

    def close(self) -> None:
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
