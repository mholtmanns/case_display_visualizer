"""Where to find/write user-facing files (config.toml, themes.local.toml,
etc.) -- differs between running from source and running as a frozen
PyInstaller .exe, where bundled source files live in a temporary extraction
directory that's gone after the process exits.
"""

from __future__ import annotations

import sys
from pathlib import Path


def app_base_dir() -> Path:
    """Directory user-editable/persisted files live next to.

    - Frozen (PyInstaller) build: the directory containing the .exe, so
      config.local.toml/themes.local.toml survive next to it across runs.
    - Running from source: the project root (three levels up from this
      file: src/case_display_visualizer/paths.py -> src -> project root).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def bundled_resource_dir() -> Path:
    """Directory read-only bundled resources (e.g. a shipped config.toml)
    live in -- the PyInstaller temp extraction dir when frozen, otherwise
    the same as app_base_dir()."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", app_base_dir()))
    return app_base_dir()
