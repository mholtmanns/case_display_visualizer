"""Monitor detection and window placement for the target auxiliary display."""

from __future__ import annotations

from dataclasses import dataclass

import screeninfo


@dataclass(frozen=True)
class TargetDisplay:
    x: int
    y: int
    width: int
    height: int
    name: str


def find_target_display(
    preferred_width: int = 800,
    preferred_height: int = 480,
) -> TargetDisplay:
    """Locate the auxiliary display to render on.

    Prefers a monitor matching preferred_width x preferred_height. Falls back
    to the first non-primary monitor, then the primary monitor, so the app
    still starts (windowed) if the panel isn't connected.
    """
    monitors = screeninfo.get_monitors()

    for m in monitors:
        if m.width == preferred_width and m.height == preferred_height:
            return TargetDisplay(m.x, m.y, m.width, m.height, m.name)

    for m in monitors:
        if not m.is_primary:
            return TargetDisplay(m.x, m.y, m.width, m.height, m.name)

    for m in monitors:
        if m.is_primary:
            return TargetDisplay(m.x, m.y, m.width, m.height, m.name)

    raise RuntimeError("No monitors detected")
