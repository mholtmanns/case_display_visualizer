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

Early scaffolding. Build order (see `plan` in project history / commits):

1. [x] Static shape rendering on the target display
2. [ ] CPU/GPU sensors wired into the composer
3. [ ] Desktop audio loopback + FFT equalizer visuals
4. [ ] Keyboard/mouse activity layer
5. [ ] Config file + system tray controls
6. [ ] Visual polish (glow/bloom), scene randomization
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

```bash
python -m case_display_visualizer
```

By default the app targets the second monitor in your display arrangement.
See `config.toml` (once added) to pin a specific monitor, resolution, or
window position.

## Project layout

```
src/case_display_visualizer/
  __main__.py       Entry point
  app.py             Main loop wiring sensors -> composer -> renderer
  display.py         Monitor detection / window placement
  sensors/           Input sources (cpu, gpu, audio, input-activity)
  scenes/            Visual scenes (shapes, starfield, equalizer)
  render/            Rendering helpers
```

## License

MIT — see [LICENSE](LICENSE).
