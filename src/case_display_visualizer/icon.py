"""Shared hexagon icon design used for the tray icon, the app window's
taskbar/title-bar icon, and the exported .ico used by desktop shortcuts.
Keeping one generator means all three always look identical.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

DEFAULT_COLOR = (0, 220, 220)


def build_icon_image(color: tuple[int, int, int] = DEFAULT_COLOR, size: int = 256) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = size * 4 / 64
    line_width = max(1, round(size * 3 / 64))
    cx, cy, r = size / 2, size / 2, size / 2 - margin

    points = [
        (
            cx + r * math.cos(math.radians(60 * i - 90)),
            cy + r * math.sin(math.radians(60 * i - 90)),
        )
        for i in range(6)
    ]
    draw.polygon(points, outline=color, width=line_width)
    return img
