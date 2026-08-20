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
color theme, set the ring line thickness (1-6px), and quit.

### Flags

```bash
python cdv -v          # dump resolved config to the terminal on startup, then run normally
python cdv -vv         # also print live sensor energy values, updated in-place in the terminal
python cdv -window     # show it in a normal desktop window instead of full-screen on the case display
python cdv -window -vv # combine flags as needed
```

## Configuration

Edit [config.toml](config.toml) to change defaults (which sensors start
enabled, animation speed, color theme, ring line thickness), or copy it to
`config.local.toml` for machine-specific overrides -- that file is
gitignored and takes precedence when present. Tray menu changes are
runtime-only and are not written back to either file.

## Project layout

```
cdv/__main__.py     Lets `python cdv` run the app from the project root
src/case_display_visualizer/
  __main__.py       Entry point for `python -m case_display_visualizer`
  cli.py             Argument parsing (-v, -vv, -window)
  debug.py            Startup config dump and live sensor telemetry
  app.py             Main loop wiring sensors -> composer -> renderer
  display.py         Monitor detection / window placement
  composer.py         Smooths raw sensor samples into 0..1 energy values
  settings.py         Runtime settings shared with the tray icon
  themes.py            Named color palettes
  tray.py               System tray icon and menu
  sensors/           Input sources (cpu, gpu, audio, input-activity)
  scenes/            Visual scenes (starfield, hex rings, equalizer, particles)
  render/            Rendering helpers
```

## License

MIT — see [LICENSE](LICENSE).
