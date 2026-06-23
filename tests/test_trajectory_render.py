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
    """Simulate a model history of 3 consecutive windows."""
    window_chords = ["C" if s == 1 else None for s in WINDOW_SLOTS]
    return [window_chords, window_chords, window_chords]


def test_trajectory_concat_bars(history, cfg):
    """M6.T2: trajectory_to_midi concatenates windows; total duration matches n*bars."""
    pm = trajectory_to_midi(history, cfg)
    assert isinstance(pm, PrettyMIDI)
    expected_bars = len(history) * cfg.bars_per_window
    # 4/4 time: 4 beats per bar
    expected_duration = expected_bars * 4 * (60.0 / cfg.tempo_bpm)
    assert abs(pm.get_end_time() - expected_duration) < 1e-6


def test_trajectory_concat_notes_and_pitches(history, cfg):
    """M6.T2: Concatenated MIDI preserves note counts and pitch voicings across windows."""
    pm = trajectory_to_midi(history, cfg)
    notes = pm.instruments[0].notes
    expected_note_count = len(history) * WINDOW_OCCUPIED_SLOTS * 3
    assert len(notes) == expected_note_count

    beat_dur = 60.0 / cfg.tempo_bpm
    for w_idx, window in enumerate(history):
        for slot_idx, chord_name in enumerate(window):
            if chord_name is None:
                continue
            global_beat = w_idx * (cfg.bars_per_window * 4) + slot_idx
            start_time = global_beat * beat_dur
            expected_midi = sorted([pc + 48 for pc in DIATONIC_CHORDS[chord_name]])
            slot_notes = [n for n in notes if abs(n.start - start_time) < 1e-6]
            assert len(slot_notes) == 3
            assert sorted([n.pitch for n in slot_notes]) == expected_midi


def test_render_wav_skips_headless(history, cfg, tmp_path):
    """M6.T2: render_wav emits .mid and raises/skips when fluidsynth/soundfont is absent."""
    pm = trajectory_to_midi(history, cfg)
    out_wav = tmp_path / "test.wav"
    out_mid = tmp_path / "test.mid"

    # Should raise a clear error when audio backend is unavailable
    with pytest.raises((RuntimeError, ImportError, FileNotFoundError)):
        render_wav(pm, soundfont=None, out=out_wav)

    # .mid must still be emitted regardless of audio render failure
    assert out_mid.exists()
