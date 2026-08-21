"""Regenerate assets/app_icon.ico from the shared hexagon icon design.

Run after changing icon.py's design (icon.build_icon_image). The .ico is
committed to the repo so desktop shortcuts don't need Python to display an
icon before the app has ever run.
"""

from __future__ import annotations

from pathlib import Path

from case_display_visualizer.icon import build_icon_image

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "app_icon.ico"
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main() -> None:
    image = build_icon_image(size=256)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_PATH, format="ICO", sizes=ICO_SIZES)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
