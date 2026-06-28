"""
Sonification utilities for the SchellingChords model.

Converts chord names to MIDI pitch classes and windows of chords to PrettyMIDI objects.
"""

from typing import List, Optional
from pathlib import Path
import subprocess

from pretty_midi import PrettyMIDI, Instrument, Note

from schellingchords.config import Config
from schellingchords.chords import VOCABULARIES

# Rendering octave base. Pitch classes (0-11) are voiced at MIDI base 48; the
# mod-12 reduction of any rendered note therefore equals its pitch class exactly.
# (This is one octave below the canonical ``Chord.midi_voicing`` base of 60; the
# octave is a deliberate rendering choice and is mod-12 irrelevant.)
_VOICING_BASE = 48

# Single source of truth: derive chord -> pitch-class sets directly from the
# canonical vocabulary in chords.py, the same definitions the model and the
# distance metric use. NOT a private copy -- if a chord's pitch classes are
# corrected in chords.py, the rendered audio follows automatically and cannot
# silently diverge (the B-flat/B mislabel net). Sorted for deterministic voicings.
CHORD_PITCH_CLASSES = {
    chord.name: sorted(chord.pitch_classes)
    for factory in VOCABULARIES.values()
    for chord in factory()
}


def chord_to_notes(chord_name: str) -> List[int]:
    """
    Convert a chord name to a list of MIDI note numbers.

    Args:
        chord_name: The name of the chord (e.g., "C", "Dm").

    Returns:
        A list of MIDI note numbers corresponding to the chord's pitch classes,
        voiced at MIDI base 48.
    """
    if chord_name not in CHORD_PITCH_CLASSES:
        raise ValueError(f"Unknown chord name: {chord_name}")

    pitch_classes = CHORD_PITCH_CLASSES[chord_name]
    midi_notes = [pc + _VOICING_BASE for pc in pitch_classes]
    return midi_notes


def window_to_midi(window: List[Optional[str]], cfg: Config) -> PrettyMIDI:
    """
    Convert a window of chords to a PrettyMIDI object.

    Args:
        window: A list of chord names (strings) or None (for rests/vacant slots).
        cfg: The configuration object containing tempo and other parameters.

    Returns:
        A PrettyMIDI object representing the window.
    """
    pm = PrettyMIDI()
    instrument = Instrument(program=0, is_drum=False)
    
    beat_dur = 60.0 / cfg.tempo_bpm
    
    for idx, chord_name in enumerate(window):
        if chord_name is None:
            continue
        
        midi_notes = chord_to_notes(chord_name)
        start_time = idx * beat_dur
        
        for pitch in midi_notes:
            note = Note(
                velocity=100,
                pitch=pitch,
                start=start_time,
                end=start_time + beat_dur
            )
            instrument.notes.append(note)
    
    pm.instruments.append(instrument)
    return pm


def trajectory_to_midi(history: List[List[Optional[str]]], cfg: Config) -> PrettyMIDI:
    """
    Concatenate a sequence of windows into a single PrettyMIDI object.

    Args:
        history: A list of window states, each a list of chord names or None.
        cfg: The configuration object containing tempo and other parameters.

    Returns:
        A PrettyMIDI object representing the full trajectory.
    """
    pm = PrettyMIDI()
    instrument = Instrument(program=0, is_drum=False)
    beat_dur = 60.0 / cfg.tempo_bpm
    
    window_beats = cfg.bars_per_window * cfg.beats_per_bar
    for w_idx, window in enumerate(history):
        window_start_beat = w_idx * window_beats
        for slot_idx, chord_name in enumerate(window):
            if chord_name is None:
                continue
            global_beat = window_start_beat + slot_idx
            start_time = global_beat * beat_dur
            midi_notes = chord_to_notes(chord_name)
            for pitch in midi_notes:
                note = Note(
                    velocity=100,
                    pitch=pitch,
                    start=start_time,
                    end=start_time + beat_dur
                )
                instrument.notes.append(note)
                
    pm.instruments.append(instrument)
    
    # Ensure total duration matches expected window length
    total_beats = len(history) * window_beats
    expected_duration = total_beats * beat_dur
    if instrument.notes:
        max_start = max(n.start for n in instrument.notes)
        for n in instrument.notes:
            if n.start == max_start:
                n.end = expected_duration
                
    return pm


def render_wav(pm: PrettyMIDI, soundfont: Optional[str], out: str) -> None:
    """
    Render a PrettyMIDI object to a WAV file using fluidsynth.

    Args:
        pm: The PrettyMIDI object to render.
        soundfont: Path to the SoundFont file. If None, raises RuntimeError.
        out: Output path for the WAV file.

    Raises:
        RuntimeError: If soundfont is None or fluidsynth is unavailable/fails.
    """
    out_path = Path(out)
    mid_path = out_path.with_suffix('.mid')
    
    # Always emit the MIDI file first
    pm.write(str(mid_path))
    
    if soundfont is None:
        raise RuntimeError("soundfont path is required for audio rendering")
        
    # Attempt to render via fluidsynth
    try:
        subprocess.run(
            ["fluidsynth", "-F", str(out_path), soundfont, str(mid_path)],
            check=True,
            capture_output=True
        )
    except FileNotFoundError:
        raise RuntimeError("fluidsynth command not found. Install fluidsynth to render audio.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"fluidsynth failed: {e.stderr.decode()}")
