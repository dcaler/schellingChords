# SchellingChords — Model Design

*Status: draft for review · 2026-06-18 · all code lives under `code/`*

## 1. Aim

Run a 1D Schelling segregation process where the agents are **chords** living in
the beats of a 4/4 window, and **sonify the segregation process**. Schelling
guarantees order emerges; the research question is *what that emergence sounds
like*.

## 2. Time model (the spine of the design)

There is **one** time axis — simulation time *is* musical time.

- The Schelling space is a window of **`bars_per_window` (X)** bars of 4/4
  (X parameterized; default 4 bars = 16 beats).
- A simulation **step** relocates the agents **forward into the next X bars**:
  each unsatisfied agent chooses an **empty** beat-slot in window `W(t+1)` near
  harmonically similar neighbors.
- The piece is the concatenation `W0 · W1 · W2 · … · Wn`. `W0` is harmonically
  scrambled; later windows are progressively segregated into contiguous tonal
  regions. Played front-to-back, the listener *hears* segregation unfold in real
  musical time.

```
sim step:      t=0        t=1        t=2              t=n
window:      [ W0 ]  →  [ W1 ]  →  [ W2 ]  → ... →  [ Wn ]
music time:  bars 1-4   bars 5-8   bars 9-12        bars ...
state:       scrambled  ...        ...              segregated
```

The same multiset of chord-agents persists across windows (population
conserved); each step is a Schelling relocation of that multiset into the next
window's slots.

## 3. Schelling → music mapping

| Schelling concept | Musical realization |
|---|---|
| Mobile agent | a chord (pitch-class set + root + quality + MIDI voicing) |
| Lattice cell | a beat-slot in the current X-bar window |
| **Vacancy** | an **empty beat = a rest** (enables relocation) |
| Neighborhood | window of nearby beats (`radius`, harmonic-context span) |
| Similarity ("like me") | small **chord distance** to neighbors |
| Tolerance threshold | perceptual-similarity cutoff (satisficing parameter) |
| Satisfaction ("happy") | fraction of (non-empty) neighbors within tolerance ≥ `happiness` |
| Relocation | move into an **empty** slot in the **next** window with similar neighbors |
| Macro outcome | contiguous tonal regions = emergent stability hierarchy |

## 4. Module architecture (Python + Mesa) — under `code/`

```
code/
  pyproject.toml
  schellingchords/
    chords.py        # Chord type + vocabulary; pitch-class sets, root, quality, MIDI voicing
    distance.py      # DistanceMetric protocol + registry
                     #   - PitchClassOverlap   (START HERE)
                     #   - TymoczkoVoiceLeading (later, pluggable)
                     #   - TIV / Cubarsi        (later, pluggable)
    agent.py         # ChordAgent(mesa.Agent): satisfaction(), desired_slot()
    model.py         # SchellingChordModel(mesa.Model): advancing X-bar window, scheduler, DataCollector
    schedule.py      # relocation into next window; movement order; vacancy/collision policy
    observables.py   # segregation index, region count, per-position stability profile
    sonify.py        # window/trajectory -> MIDI -> WAV (the deliverable)
    player.py        # beat-synced playback clock — emits (window, beat) ticks driving audio + viz together
    viz.py           # runtime visualization: lattice/window state + moving playhead, redrawn per tick
    gui.py           # control panel (parameters + run/pause/step controls) wrapping player + viz
    config.py        # parameter dataclass; YAML load/save
    run.py           # single run, batch sweep, phase-diagram experiments
  tests/             # one test module per source module (the gates)
  configs/           # YAML experiment configs
  outputs/           # audio + data, dated per the file-naming convention
```

### GUI & runtime visualization — **pygame + pygame_gui, LIVE/streaming (LOCKED)**

- **Live mode:** the model is stepped and sonified **in real musical time** — you
  hear segregation as it computes, and **control changes take effect mid-run**.
  Consequence: the model reads `tolerance`/`happiness`/`vacancy_fraction` from a
  **mutable `RuntimeParams`** each step (not the frozen `Config`); structural params
  (`n_chord_types`, `bars_per_window`, `seed`) apply on **reset**.
- **Controls:** sliders/inputs for `tolerance`, `happiness`, `vacancy_fraction`,
  `n_chord_types`, `bars_per_window`, `radius`, `tempo_bpm`, `seed` + run / pause /
  step / reset and load/save config.
- **Runtime viz (synced to audio):** the 1D window is drawn as a strip of beat-cells
  colored by chord type (empty cells = rests); a **playhead** sweeps left→right in
  lock-step with playback, and successive windows scroll/advance so the viewer
  literally *watches* segregation while hearing it. `player.py`'s tick clock drives
  both audio and animation so they never drift; live audio = `pygame.midi` note
  events (note-on per beat-chord, note-off after the beat; rests = silence).
- **Decoupling:** core engine (Mesa) is GUI-agnostic; `player.py` exposes the tick
  stream; `viz.py`/`gui.py` are thin presentation layers. Headless runs (`run.py`)
  skip them; GUI tests run under `SDL_VIDEODRIVER=dummy` / `SDL_AUDIODRIVER=dummy`
  so the gates stay green without a display.

### Pluggable distance metric

```python
class DistanceMetric(Protocol):
    def distance(self, a: Chord, b: Chord) -> float: ...   # 0 == identical
```

v1 = **pitch-class set overlap** (shared-tone / Jaccard). Interface stays clean so
Tymoczko / TIV / Cubarsi drop in later and can be benchmarked against behavioral
stability ratings (Krumhansl, Bharucha).

### Agent rule (satisficing / bounded rationality)

```
neighbors = occupied slots within `radius` of this beat (current window)
similar   = count(n for n in neighbors if dist(self, n) <= tolerance)
satisfied = similar / len(neighbors) >= happiness        # vacuously true if no neighbors
# unsatisfied agents relocate into an EMPTY slot of the next window at a best-improving position
```

## 5. Vocabulary, chord types, vacancies, rhythm (LOCKED v1)

- Fixed alphabet of triads (7 diatonic triads of C major + optional chromatic
  neighbors), each a pitch-class set + MIDI voicing. Distance on pitch-class
  content (key-agnostic) so the engine generalizes.
- **`n_chord_types`** (config): how many *distinct* chords populate the run.
  Schelling used **2** "colors"; we generalize — the model selects `n_chord_types`
  distinct chords from the vocabulary (2 ≤ `n_chord_types` ≤ |vocabulary|) and
  distributes them across the occupied beats. With more types, "similarity" becomes
  graded rather than binary, which is the whole point of the chord-distance metric.
- 4/4: window length = `bars_per_window * beats_per_bar` slots.
- **Vacancies are real**: a fraction of beats are empty (`vacancy_fraction`,
  config). Empty beats are **rests**, and they are what agents move into. A
  consequence we *want*: the **rhythm itself evolves** as segregation proceeds —
  rests migrate as chords cluster, so the texture changes audibly alongside the
  harmony.

## 6. Observables (logged per step)

- **Segregation index** — mean local similarity (1D Schelling analogue).
- **Region count** — number of contiguous similar-chord runs per window.
- **Per-position stability** — settledness of each beat; aggregate → emergent
  stability hierarchy to compare with the perceptual literature.

## 7. Sonification (deliverable)

`Chord -> MIDI` via `pretty_midi`/`mido`; `MIDI -> WAV` via a SoundFont
(`fluidsynth`). Empty slots render as rests. Tempo + 4/4 metering applied at
render time. Output = one continuous WAV of `W0 … Wn`, plus per-window MIDI and
the observable time series.

---

# 8. Build pipeline — gated, test-driven, Ollama-worker tasks

The build is decomposed into **modules** (each a **gate**) and **tasks** (each a
unit of work with its own test). Machine-readable source of truth:
[`tasks.yaml`](./tasks.yaml). Orchestration is queue-ready for **trundlr**
(`trundlr_project_id: 2`) — *queueing is held pending user go/no-go review.*

### Worker assignment (local Ollama)

| Worker | Model | Task type |
|---|---|---|
| `strong` | `qwen3.6:27b-16k` | conceptually tricky: distance metrics, model dynamics, observables, sonification |
| `worker` | `llama3.1:8b` | scaffolding, vocabulary, config, run/CLI boilerplate, test stubs |

### Two levels: tasks have unit tests, modules have gates

- A **task** has a **unit test** — scope = one deliverable file; "does this file meet
  its spec?". Pass → task `done` (release next task); fail → next task `blocked`.
- A **module** has a **gate** = an **integration test** that composes the module's
  tasks (and upstream modules) — "do the pieces work *together*?". The gate runs only
  after **all** the module's tasks pass. Pass → release next module; fail → next
  module `blocked` (investigation needed; no silent skip).
- **Email** (address configured in trundlr) fires at the **end of every task and every
  gate** with status + test summary.

### Module / gate overview (10 gates, ~21 tasks)

| Gate | Module | Tasks | Worker | Gate = integration test |
|---|---|---|---|---|
| G0 | M0 — scaffold | T1 layout/deps · T2 Config | `worker` | package imports + default.yaml → Config |
| G1 | M1 — chords | T1 Chord type · T2 vocab+select_types | `worker` | build n_chord_types population from a Config |
| G2 | M2 — distance | T1 protocol+registry · T2 PitchClassOverlap | `strong` | metric orders diatonic chords correctly |
| G3 | M3 — agent | T1 satisfaction · T2 desired-slot | `strong` | agent satisfaction+move over real metric/window |
| G4 | M4 — model | T1 schedule · T2 model loop | `strong` | seeded run: deterministic, multiset/vacancy conserved |
| G5 | M5 — observables | T1 per-window · T2 profile+DataCollector | `strong` | run logs per step; segregation trends up |
| G6 | M6 — sonify | T1 window→MIDI · T2 trajectory+WAV | `strong` | real history → MIDI bars/pitches/rests correct |
| G7 | M7 — run/CLI | T1 single() · T2 sweep()+CLI | `worker` | CLI single+sweep produce outputs |
| G8 | M8 — system | T1 demo.yaml · T2 acceptance test | `strong` | whole headless pipeline; segregation demonstrable (release gate) |
| G9 | M9 — GUI/viz | T1 live player · T2 viz · T3 control panel | `strong` | headless: player steps model, viz renders, slider write-through |

Progress on the build is tracked live in [`PROGRESS.md`](./PROGRESS.md) (human-facing
mirror of trundlr task + gate state).

## 9. Parking lot (post-v1)

- Tolerance **static** first; later **context-modulated** (MEG-prior idea) — the
  literature synthesis gap, a v2 concern.
- Boundary conditions on the 1D window: fixed ends vs periodic.
- Benchmarking alternative distance metrics against Krumhansl/Bharucha ratings.

---

# 10. Execution architecture — how the local LLMs actually do the work

Grounded in the real trundlr API (`http://100.87.86.57:8251`, project **2** "SchellingChords")
and `~/trundlr/runner.py`.

**trundlr is a queue + runner daemon, not an LLM.** A task = a shell **command** run in
the project directory; **exit 0 → `done`, nonzero → `failed`**. Dependencies are
**single-parent** (`depends_on_id`), and a failed task auto-sets `dependency_broken`
on everything downstream — that *is* block-on-fail, for free. The build machinery lives
in `doer/` (outside `code/` — it is not part of the shipped package):

```
260526_SchellingChords/
  code/        # the package the workers BUILD; tests/ are FROZEN (authored in Phase 0)
  doer/
    doer.py    # the command each implementation task runs
    submit.py  # reads code/tasks.yaml -> creates the linearized trundlr task chain
```

1. **Phase 0 — frozen test infrastructure (qwen, unattended).** Before any implementation,
   `qwen3.6:27b-16k` authors **all** test infra (conftest, fixtures, golden values, every
   unit test, every gate test) into `code/tests/`. These are the executable spec and pin
   the interfaces. No human review (decided).
2. **`doer/doer.py --task X.Y`** (the task command): loads `code/tasks.yaml`, builds the
   prompt, calls the assigned Ollama model on oddjob (`localhost:11434`), writes **only the
   implementation file(s)** into `code/` (never `tests/`), runs the **frozen** test, bounded
   repair loop (escalate `llama→qwen`), and **exits with the test's status**.
3. **Gate tasks** = plain `pytest code/tests/gate_*.py` on CPU — no LLM.
4. **`doer/submit.py`**: linearizes the DAG into one ordered chain (single-parent deps; one
   GPU anyway), POSTs tasks to project 2 with `depends_on_id` chaining and `resource_ids` =
   **GPU(2)** for doer tasks, **CPU(3)** for gates; sets the project directory to the repo root.
5. **Notification:** trundlr sends the end-of-task email natively (no slurm). The task
   command is just `python doer/doer.py --task X.Y` (gates: `pytest code/tests/gate_*.py`).

**Per-task flow:** trundlr claim → doer → Ollama → write impl → run frozen test →
exit 0/1 → trundlr `done`/`failed` → (fail ⇒ `dependency_broken` downstream) → trundlr email.

**Accepted residual risk:** for qwen-implemented tasks (M2–M6, M9) qwen also wrote the
tests, so a shared misreading of the spec can pass both; the frozen module **gates** are the
backstop.
