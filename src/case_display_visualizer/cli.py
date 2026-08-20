"""Command-line argument parsing."""

from __future__ import annotations

import argparse


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="cdv",
        description="Reactive sci-fi visualization for an auxiliary display.",
    )
    parser.add_argument(
        "-v",
        dest="verbose",
        action="count",
        default=0,
        help=(
            "-v dumps config details on startup; "
            "-vv also prints live sensor values in-place in the terminal"
        ),
    )
    parser.add_argument(
        "-window",
        dest="windowed",
        action="store_true",
        help=(
            "show the visualization in a normal desktop window instead of "
            "full-screen on the case display"
        ),
    )
    parser.add_argument(
        "-static",
        dest="static",
        action="store_true",
        help=(
            "show every visualization component in a fixed, non-animated "
            "layout (sensors disabled, equalizer bars ramped 5%%-100%%) for "
            "tuning colors and settings without motion in the way"
        ),
    )
    return parser.parse_args(argv)
