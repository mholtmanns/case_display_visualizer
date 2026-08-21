# Case Display Visualizer

A sci-fi, reactive visualization for an 800x480 auxiliary display (e.g. a PC
case-mounted secondary screen), built with Python. It renders animated
geometric shapes, starfields, and equalizer-style effects that react to live
system input: desktop audio, CPU/GPU utilization, and keyboard/mouse
activity.

Runs standalone (not through Rainmeter) and is meant to sit in the system
tray and start with Windows.

> See [DISCLAIMER.md](DISCLAIMER.md) — this codebase was built with
> AI assistance.

## Status

Build order (see commit history for detail on each stage):

1. [x] Static shape rendering on the target display
2. [x] CPU/GPU sensors wired into the composer
3. [x] Desktop audio loopback + FFT equalizer visuals
4. [x] Keyboard/mouse activity layer
5. [x] Config file + system tray controls
6. [x] Scene randomization (auto color theme cycling + ring shape variants)
7. [ ] AI-generated imagery pipeline (future)

## Requirements

- Windows 10/11
- Python 3.11+
- A secondary display (e.g. 800x480 panel) recognized by Windows as its own
  monitor

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Running

From the project root (with the venv active):

```bash
python cdv
```

By default the app targets a connected 800x480 monitor if one is found,
falling back to the first non-primary monitor otherwise. A system tray icon
(sci-fi hexagon) appears once running, with a menu to toggle individual
sensors (CPU/GPU/audio/keyboard-mouse), pick an animation speed, choose a
color theme, set the ring line thickness (1-6px), pick the starfield
direction (left/right/up/down/away/towards), choose the equalizer layout
(bottom bar / radial around the rings), toggle the moving center on/off,
pick the render depth (2D/3D -- see below), and quit.

### Flags

```bash
python cdv -v          # dump resolved config to the terminal on startup, then run normally
python cdv -vv         # also print live sensor energy values, updated in-place in the terminal
python cdv -window     # show it in a normal desktop window instead of full-screen on the case display
python cdv -static     # freeze every component in a fixed layout for tuning colors/settings
python cdv -window -vv # combine flags as needed
```

`-static` disables all sensors and animation so nothing moves: the hex rings
sit at their default unrotated shape, the starfield is frozen in place, and
the equalizer bars are fixed in a ramp from 5% (first bar) to 100% (last
bar) so every bar is visible at a distinct height. Theme, line thickness,
and starfield direction still update live from the tray menu, making it
easy to dial in colors and settings without motion in the way. Combine with
`-window` to preview it without needing the case display attached.

## Running as a standalone app (double-click, no console)

To run it like a normal Windows app -- double-click an icon, no terminal
window, correct icon in the taskbar -- build a standalone `.exe`:

```powershell
.venv\Scripts\pip install pyinstaller
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

This produces `dist\CaseDisplayVisualizer.exe`: a single self-contained
file (no Python install needed to run it) with the hexagon icon baked in
as a proper PE resource. Double-click it directly, or run the following to
drop a desktop shortcut pointing at it:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create_shortcut.ps1
```

You can then pin that shortcut (or the `.exe` itself) to the taskbar or
Start menu like any other app. `config.local.toml`/`themes.local.toml` are
read from and written next to wherever the `.exe` is run from, so they
persist across restarts the same way as running from source.

Why a compiled `.exe` and not just a shortcut to `pythonw.exe`? Windows
determines a running window's taskbar icon primarily from the icon baked
into the launching `.exe`'s own resources, not from anything a Python GUI
sets at runtime (`pygame.display.set_icon()` correctly updates the title
bar and Alt-Tab icon, but not the taskbar button) -- a raw
`python.exe`/`pythonw.exe` process always shows the interpreter's own icon
on the taskbar no matter what. Compiling avoids that entirely. A
`pythonw.exe`-based shortcut still works for double-click, console-free
launching (`create_shortcut.ps1` falls back to one automatically if you
skip the build step) -- it just won't have the right taskbar icon.

## Configuration

Edit [config.toml](config.toml) to change defaults (which sensors start
enabled, animation speed, color theme, ring line thickness, starfield
direction, equalizer layout), or copy it to `config.local.toml` for
machine-specific overrides -- that file is gitignored and takes precedence
when present.

### Radial equalizer

Setting `equalizer_style = "radial"` (config or tray) moves the audio bars
from the bottom edge to a circle enclosing the hex rings, radiating
outward as bars the same width as the bottom layout -- low frequencies at
12 o'clock, going clockwise to high frequencies. The whole ring slowly
rotates (~50s per revolution) so the visual doesn't stay static just
because most audio energy tends to sit in the same low-frequency bands.
In this mode the rings are locked to a fixed count of 4 and shrunk so the
enclosing circle has guaranteed clearance; switching back to `"bottom"`
restores the rings' normal variable size/count. Loud audio can push bars
past the screen edge in this mode -- that's expected, not a bug.

Changes made via the tray menu are saved automatically to
`config.local.toml`, so they persist across restarts. `config.toml` itself
is never modified -- it stays as the checked-in set of shipped defaults.

### Wandering center

The hex rings' center drifts slowly around the screen along a smooth,
curved, non-repeating path (a rolling Catmull-Rom spline through random
waypoints, not the straight-line/bounce-off-the-wall motion of old
floating-logo screensavers), staying at least 50px from every edge. The
radial equalizer and the tunnel starfield (`away`/`towards`) share the
exact same moving center, so the whole cluster drifts together as one
unit; the bottom equalizer bar and linear starfield directions have no
"center" concept and are unaffected. Movement is intentionally slow and
fixed-rate rather than tied to the Speed setting. `-static` mode keeps
everything at the screen center as usual.

Toggle it off via the tray's "Moving center" checkbox or `moving_center =
false` in config -- everything snaps back to (and stays at) the screen
center. Turning it back on resumes the same path from where it paused.

### Custom color themes

Copy [themes.example.toml](themes.example.toml) to `themes.local.toml` to
add your own themes or override the built-in ones (cyan, amber, magenta,
matrix) -- colors can be given as hex strings (`"#00DCDC"`) or `[r, g, b]`
arrays. The file has inline comments explaining the four color roles each
theme needs and how to name a new one; it's picked up on startup and any
themes it defines show up in the tray icon's Theme submenu.

### Rainbow themes

Two more theme options cycle continuously through the color spectrum
instead of using fixed colors, like an RGB case-lighting "rainbow" mode:

- `prism` -- every ring, bar, and particle shares the same hue, shifting
  together over time (a single synced color sweep)
- `aurora` -- each ring and each equalizer band gets a hue offset by its
  position, so color visibly chases across them as the base hue advances

Both cycle at a rate tied to the existing Speed setting (slow/normal/fast),
so no separate speed control is needed. `prism`/`aurora` are reserved
names and can't be used for a custom theme in `themes.local.toml`.

### Depth (2D / 3D)

A "Depth" tray/config setting for a future true-3D rendering mode. Only
`2d` (the current, existing rendering) works right now -- `3d` is a
placeholder, shown greyed out in the tray menu and rejected if set
directly in config, until that mode is actually built.

## Project layout

```
cdv/__main__.py     Lets `python cdv` run the app from the project root
assets/app_icon.ico  App icon, baked into the .exe and used by shortcuts
scripts/
  generate_icon.py    Regenerates assets/app_icon.ico from icon.py's design
  build_exe.ps1        Builds dist\CaseDisplayVisualizer.exe (PyInstaller)
  create_shortcut.ps1  Drops a desktop shortcut to the exe (or venv fallback)
src/case_display_visualizer/
  __main__.py       Entry point for `python -m case_display_visualizer`
  cli.py             Argument parsing (-v, -vv, -window)
  debug.py            Startup config dump and live sensor telemetry
  app.py             Main loop wiring sensors -> composer -> renderer
  display.py         Monitor detection / window placement
  paths.py            Where config/theme overrides live (source vs. frozen .exe)
  composer.py         Smooths raw sensor samples into 0..1 energy values
  settings.py         Runtime settings shared with the tray icon
  themes.py            Named color palettes (+ themes.local.toml overrides)
  rainbow.py            Hue-cycling colors for the prism/aurora theme modes
  wander.py              Smooth Catmull-Rom wander path for the shared center
  icon.py                Shared hexagon icon design (tray/window/.ico all use it)
  tray.py               System tray icon and menu
  sensors/           Input sources (cpu, gpu, audio, input-activity)
  scenes/            Visual scenes (starfield, hex rings, equalizer, particles)
  render/            Rendering helpers
```

## License

MIT — see [LICENSE](LICENSE).
