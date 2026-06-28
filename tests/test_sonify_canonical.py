"""Guards the sonification rendering transform against the canonical chords.

Scope (and its limit): sonify now derives its pitch classes from chords.py, so
this test shares that source -- it therefore verifies the *transform* (notes
reduce mod 12 to the source pitch-class set, base-48 voicing, rests silent,
inter-window contiguity under a non-default beats_per_bar), not the value of the
pitch classes themselves. The actual mislabel net (the named chord's pitch
classes are *correct*) is gate_sonify.py, which compares the canonical-derived
render against the independent hand-maintained tests/golden copy; deriving sonify
from chords.py is what makes that comparison non-tautological. The contiguity case
here is the general criterion-3 check the default-config gate cannot exercise.
"""

import pytest

from schellingchords.chords import diatonic_major
from schellingchords.config import Config
from schellingchords.sonify import window_to_midi, trajectory_to_midi


CANONICAL = {c.name: set(c.pitch_classes) for c in diatonic_major()}


def _cfg(**overrides):
    base = dict(
        n_chord_types=3, bars_per_window=4, vacancy_fraction=0.0,
        tolerance=0.5, happiness=0.5, radius=2, tempo_bpm=120, seed=1,
    )
    base.update(overrides)
    return Config(**base)


@pytest.mark.parametrize("chord_name", sorted(CANONICAL))
def test_rendered_notes_mod12_equal_canonical_pitch_classes(chord_name):
    """(1) Each rendered chord's notes, mod 12, equal its canonical pitch-class set."""
    cfg = _cfg()
    window = [chord_name] + [None] * (cfg.bars_per_window * cfg.beats_per_bar - 1)
    pm = window_to_midi(window, cfg)
    notes = pm.instruments[0].notes
    assert {n.pitch % 12 for n in notes} == CANONICAL[chord_name]


def test_rests_emit_no_notes():
    """(2) Vacant beats (None) emit no note."""
    cfg = _cfg()
    beat = 60.0 / cfg.tempo_bpm
    window = ["C", None, "Em", None]
    window += [None] * (cfg.bars_per_window * cfg.beats_per_bar - len(window))
    notes = window_to_midi(window, cfg).instruments[0].notes
    for idx, name in enumerate(window):
        onset_notes = [n for n in notes if abs(n.start - idx * beat) < 1e-6]
        if name is None:
            assert onset_notes == []
        else:
            assert {n.pitch % 12 for n in onset_notes} == CANONICAL[name]


def test_trajectory_contiguous_under_nondefault_beats_per_bar():
    """(3) Windows are contiguous on the global beat grid for beats_per_bar != 4."""
    cfg = _cfg(bars_per_window=2, beats_per_bar=3)
    wlen = cfg.bars_per_window * cfg.beats_per_bar  # 6
    window = ["C"] * wlen
    history = [window, window]
    pm = trajectory_to_midi(history, cfg)
    beat = 60.0 / cfg.tempo_bpm
    onset_beats = sorted({round(n.start / beat) for n in pm.instruments[0].notes})
    assert onset_beats == list(range(len(history) * wlen))
    expected_duration = len(history) * wlen * beat
    assert abs(pm.get_end_time() - expected_duration) < 1e-6
