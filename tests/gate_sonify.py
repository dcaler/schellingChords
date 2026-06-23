import pytest
from pretty_midi import PrettyMIDI
from tests.golden import (
    DIATONIC_CHORDS,
    WINDOW_SLOTS,
    WINDOW_OCCUPIED_INDICES,
    WINDOW_OCCUPIED_SLOTS,
)
from schellingchords.config import Config
from schellingchords.sonify import trajectory_to_midi, render_wav


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
def history(cfg):
    """Realistic model history slice for gate validation."""
    window_chords = ["C" if s == 1 else None for s in WINDOW_SLOTS]
    return [window_chords, window_chords]


def test_g6_trajectory_bars_and_pitches(history, cfg):
    """G6: trajectory_to_midi total bars == n*bars_per_window, pitches match voicings, rests empty."""
    pm = trajectory_to_midi(history, cfg)
    assert isinstance(pm, PrettyMIDI)

    # Bar count validation
    expected_bars = len(history) * cfg.bars_per_window
    expected_duration = expected_bars * 4 * (60.0 / cfg.tempo_bpm)
    assert abs(pm.get_end_time() - expected_duration) < 1e-6

    notes = pm.instruments[0].notes
    beat_dur = 60.0 / cfg.tempo_bpm

    for w_idx, window in enumerate(history):
        for slot_idx, chord_name in enumerate(window):
            global_beat = w_idx * (cfg.bars_per_window * 4) + slot_idx
            start_time = global_beat * beat_dur
            slot_notes = [n for n in notes if abs(n.start - start_time) < 1e-6]

            if chord_name is None:
                # Empty slots produce no notes
                assert len(slot_notes) == 0
            else:
                # Note pitches match each chord's voicing
                expected_midi = sorted([pc + 48 for pc in DIATONIC_CHORDS[chord_name]])
                assert sorted([n.pitch for n in slot_notes]) == expected_midi


def test_g6_wav_skipped_headless(history, cfg, tmp_path):
    """G6: WAV render skipped headless when fluidsynth/soundfont absent."""
    pm = trajectory_to_midi(history, cfg)
    out_wav = tmp_path / "gate_test.wav"

    # Must fail gracefully without crashing the test suite
    with pytest.raises((RuntimeError, ImportError, FileNotFoundError)):
        render_wav(pm, soundfont=None, out=out_wav)
