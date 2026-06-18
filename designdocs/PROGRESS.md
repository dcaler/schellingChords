# SchellingChords — Build Progress

*Human-facing mirror of trundlr task + gate state. Source of truth: [`tasks.yaml`](./tasks.yaml).
Status legend: ⬜ pending · 🟦 in_progress · ✅ done · ❌ failed · ⛔ blocked*

Two levels: each **task** has a **unit test**; each **module** has a **gate** =
integration test that runs after all its tasks pass and releases the next module.

Last updated: 2026-06-18 (design phase — no tasks dispatched yet, awaiting go/no-go)

## Phase 0 — frozen test infrastructure (qwen, unattended)

Authors all tests into `code/tests/` before any implementation. Doer writes impl only.

| Task | Authors frozen tests for | Worker | Status |
|---|---|---|---|
| P0.T0 | harness + fixtures + golden values | strong | ⬜ |
| P0.M0–M9 | one task per module (unit + gate tests) | strong | ⬜ |
| GP0 | gate: all tests collect + run RED vs empty stubs | strong | ⬜ |

## Module gates

| Gate | Module | Worker | Status | Gate (integration test) |
|---|---|---|---|---|
| G0 | M0 — scaffold | worker | ⬜ | package imports + default.yaml → Config |
| G1 | M1 — chords | worker | ⬜ | build n_chord_types population from Config |
| G2 | M2 — distance | strong | ⬜ | metric orders diatonic chords correctly |
| G3 | M3 — agent | strong | ⬜ | satisfaction + move over real metric/window |
| G4 | M4 — model | strong | ⬜ | seeded run deterministic; conserved multiset/vacancy |
| G5 | M5 — observables | strong | ⬜ | logs per step; segregation trends up |
| G6 | M6 — sonify | strong | ⬜ | history → MIDI bars/pitches/rests correct |
| G7 | M7 — run/CLI | worker | ⬜ | CLI single + sweep produce outputs |
| G8 | M8 — system | strong | ⬜ | whole headless pipeline; segregation demonstrable (release) |
| G9 | M9 — GUI/viz | strong | ⬜ | headless player+viz+slider write-through |

## Tasks (unit tests)

| Task | Title | Worker | Depends on | Status |
|---|---|---|---|---|
| M0.T1 | Scaffold + deps + import smoke | worker | — | ⬜ |
| M0.T2 | Config dataclass + YAML | worker | M0.T1 | ⬜ |
| M1.T1 | Immutable Chord type | worker | M0.T2 | ⬜ |
| M1.T2 | Vocabulary + registry + select_types | worker | M1.T1 | ⬜ |
| M2.T1 | DistanceMetric protocol + registry | strong | M1.T2 | ⬜ |
| M2.T2 | PitchClassOverlap metric | strong | M2.T1 | ⬜ |
| M3.T1 | Satisfaction functions | strong | M2.T2 | ⬜ |
| M3.T2 | Desired empty-slot selection | strong | M3.T1 | ⬜ |
| M4.T1 | Schedule (movement/vacancy policy) | strong | M3.T2 | ⬜ |
| M4.T2 | SchellingChordModel loop | strong | M4.T1 | ⬜ |
| M5.T1 | Per-window observables | strong | M4.T2 | ⬜ |
| M5.T2 | Run profile + DataCollector | strong | M5.T1 | ⬜ |
| M6.T1 | Chord/window → MIDI | strong | M4.T2 | ⬜ |
| M6.T2 | Trajectory concat + WAV render | strong | M6.T1 | ⬜ |
| M7.T1 | single() run → outputs | worker | M5.T2, M6.T2 | ⬜ |
| M7.T2 | sweep() + argparse CLI | worker | M7.T1 | ⬜ |
| M8.T1 | Demo config | worker | M7.T2 | ⬜ |
| M8.T2 | End-to-end acceptance test | strong | M8.T1 | ⬜ |
| M9.T1 | Live player (real-time step+sonify) | strong | M8.T2 | ⬜ |
| M9.T2 | Runtime viz (lattice + playhead) | strong | M9.T1 | ⬜ |
| M9.T3 | Control panel (pygame_gui app) | strong | M9.T2 | ⬜ |

## Open decisions

- Boundary conditions: fixed vs periodic window ends (non-blocking; default fixed).
- trundlr submission adapter — held pending go/no-go on the design.

## How this file is maintained

Each worker updates its task row at task end: ✅ on green unit test → release next
task; ❌ → set the dependent task ⛔ blocked. When all of a module's tasks are ✅, the
**gate** integration test runs: ✅ → release next module; ❌ → next module ⛔ blocked.
End-of-task and end-of-gate emails go to the address configured in trundlr. (Once trundlr
queueing is wired, status is pushed here automatically; until then, updated by hand.)
