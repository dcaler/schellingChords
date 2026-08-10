# SchellingChords

A [Mesa](https://mesa.readthedocs.io) agent-based model that runs a 1D Schelling
segregation process where the agents are **chords** in the beats of a 4/4 window,
and **sonifies** the segregation as it unfolds.

Each beat holds a chord (or is vacant). A chord is *satisfied* when the mean
[Jaccard distance](https://en.wikipedia.org/wiki/Jaccard_index) of its pitch-class
set to its occupied neighbours is within `tolerance`; unsatisfied chords relocate to
a uniformly random vacant slot. Iterating this Schelling step drives the window
toward segregated blocks of like chords — which you can watch and hear in the GUI.

## Requirements

- **Python ≥ 3.10**
- A local desktop display for the GUI (`schellingchords.gui`). Headless runs
  (`schellingchords.run`) need no display.

### Dependencies

Complete runtime set (declared in [`pyproject.toml`](pyproject.toml); versions are
the tested floors from a known-good environment):

| Package | Constraint | Why |
|---|---|---|
| `mesa` | `>=3.0,<4` | ABM engine (`Model`, `DataCollector`, `model.steps`) |
| `networkx` | `>=3.0` | **required by mesa 3.x** (`discrete_space`) — mesa does not always auto-install it |
| `pyyaml` | `>=6.0` | YAML config load/save |
| `numpy` | `>=1.24.0` | numerics + audio sample buffers |
| `pandas` | `>=2.0` | observables dataframe (`DataCollector`) |
| `pretty_midi` | `>=0.2.10` | chord/window → MIDI **and** the GUI's live audio synthesis (`.synthesize()`); pulls in `mido`, `scipy` |
| `pygame_gui` | `>=0.6,<0.7` | GUI control panel — **0.6.x API** (`UI_HORIZONTAL_SLIDER_MOVED`, `.value_range`, `click_increment`); pulls in `pygame-ce` (provides `pygame`, incl. `pygame.mixer` for audio) |

**Pulled in transitively** (installed automatically, listed for reference):
`pygame-ce` (via `pygame_gui`), `mido` + `scipy` (via `pretty_midi`).

## Install

Use a virtual environment (required on macOS/Homebrew and other
externally-managed Pythons):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .          # one command — installs the package + all runtime deps above
```

Alternatives:

```bash
pip install -r requirements.txt      # just the runtime deps, without installing the package
```

## Run

```bash
# GUI control panel (needs a display):
python3 -m schellingchords.gui

# Headless single run -> per-window MIDI + observables CSV in ./outputs:
python3 -m schellingchords.run single configs/demo.yaml -o outputs

# Parameter sweep -> one summary CSV:
python3 -m schellingchords.run sweep configs/default.yaml tolerance 0.3 0.5 0.7
```

### What the GUI shows

The window is a live view of one Schelling window as it re-segregates, driven by the
same `model.step()` the headless run uses (so the GUI and headless trajectories match
for a given seed):

- **Two staves** — the *current* window (t) with a red **playhead** sweeping across it
  at the set tempo, and a ghost of the *next* window (t+1) below. A chord makes its
  move as the playhead crosses it; the ghost scrolls up when the window completes.
- **Live "unhappy chords" chart** — the count of unsatisfied chords per window over
  time; the x-axis compresses as it fills so the line keeps room to fall as the system
  segregates.
- **Colour legend** — one colour per chord type in play.
- **Controls** — sliders for `tolerance` and `vacancy` (0.1 steps), `tempo`,
  `n_chord_types`, `bars_per_window`, `radius`, and note subdivision
  (quarter / eighth / 16th); a numeric **seed** input and a **re-seed** button; and
  **Run / Pause / Step / Reset / Sound / Load / Save / Quit** buttons.

### Audio

- **In the GUI (live, no external tools):** as the playhead lands on each beat, the
  chord there is synthesised on the fly with `pretty_midi.synthesize()` into a numpy
  buffer and played through `pygame.mixer`. A short fade-in/out envelope keeps it from
  clicking at speed. Toggle it with the **Sound** button. This path needs nothing
  beyond the pip dependencies.
- **Headless WAV export (optional, not pip-installable):** the continuous-WAV path in
  `sonify.render_wav` shells out to the [`fluidsynth`](https://www.fluidsynth.org/)
  binary plus a SoundFont (`.sf2`). Install `fluidsynth` via your OS package manager
  if you want that export; without it, MIDI and the observables CSV still render.
