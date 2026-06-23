import pytest
from pretty_midi import PrettyMIDI
from tests.golden import (
    DIATONIC_CHORDS,
    WINDOW_SLOTS,
    WINDOW_OCCUPIED_INDICES,
    WINDOW_OCCUPIED_SLOTS,
)
from schellingchords.config import Config
from schellingchords.sonify import chord_to_notes, window_to_midi


@pytest.fixture
def cfg():
    return Config(
        n_chord_types=3,
        bars_per_window=4,
        vacancy_fraction=0.625,
        tolerance=0.5,
        happiness=0.5,
        radius=2,
        tempo_bpm=120,
        seed=42,
    )


@pytest.fixture
def window_chords():
    """Map 0/1 slots to chord names or None for rests."""
    return ["C" if s == 1 else None for s in WINDOW_SLOTS]


@pytest.mark.parametrize("chord_name, expected_pcs", [
    (key, val) for key, val in DIATONIC_CHORDS.items()
])
def test_chord_to_notes(chord_name, expected_pcs):
    """M6.T1: chord_to_notes returns correct MIDI pitches for each chord type."""
    notes = chord_to_notes(chord_name)
    # Assume voicing places pitch classes in octave 4 (MIDI base 48)
    expected_midi = sorted([pc + 48 for pc in expected_pcs])
    assert sorted(notes) == expected_midi


def test_window_to_midi_note_count(cfg, window_chords):
    """M6.T1: window_to_midi produces correct number of notes for occupied slots."""
    pm = window_to_midi(window_chords, cfg)
    assert isinstance(pm, PrettyMIDI)
    # Each occupied slot holds a triad (3 notes)
    assert len(pm.instruments[0].notes) == WINDOW_OCCUPIED_SLOTS * 3


def test_window_to_midi_pitches_and_timing(cfg, window_chords):
    """M6.T1: Notes align to beats, pitches match voicings, rests produce no notes."""
    pm = window_to_midi(window_chords, cfg)
    notes = pm.instruments[0].notes
    beat_dur = 60.0 / cfg.tempo_bpm

    # Verify occupied slots
    for idx in WINDOW_OCCUPIED_INDICES:
        chord_name = window_chords[idx]
        expected_midi = sorted([pc + 48 for pc in DIATONIC_CHORDS[chord_name]])
        start_time = idx * beat_dur
        slot_notes = [n for n in notes if abs(n.start - start_time) < 1e-6]
        assert len(slot_notes) == 3
        assert sorted([n.pitch for n in slot_notes]) == expected_midi

    # Verify vacant slots produce no notes
    for idx in range(len(WINDOW_SLOTS)):
        if idx not in WINDOW_OCCUPIED_INDICES:
            slot_notes = [n for n in notes if abs(n.start - idx * beat_dur) < 1e-6]
            assert len(slot_notes) == 0
